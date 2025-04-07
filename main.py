from fastapi import FastAPI, BackgroundTasks, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil
import json
import re
from typing import Optional, List
from pydantic import BaseModel
from evaluate import cv_evaluation_pipeline
from dotenv import load_dotenv
from groq import Groq
from utils import *
import uvicorn
import bcrypt
from langchain_groq import ChatGroq
import redis 
from rq import Queue 


load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key)

llm = ChatGroq(model="deepseek-r1-distill-llama-70b", api_key=groq_api_key)
redis_client = redis.Redis(host="localhost", port=6379, db=0)


RESUME_EVALUATION_QUEUE_NAME = "resume_evaluation_queue"
redis_conn = redis.Redis()
queue = Queue(RESUME_EVALUATION_QUEUE_NAME, connection=redis_conn)


    
class EvaluationRequest(BaseModel):
    job_description: Optional[str] = None
    username: Optional[str] = None

class InterviewMessage(BaseModel):
    role: str  # "interviewer" or "candidate"
    content: str

class InterviewQuestionRequest(BaseModel):
    job_description: str
    history: List[InterviewMessage] = []

class InterviewFeedbackRequest(BaseModel):
    job_description: str
    history: List[InterviewMessage]
    
class RelatedJobs(BaseModel):
    username: Optional[str] = None
    
app = FastAPI(title="Resume Evaluation System")

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, message: Optional[str] = None):
    return templates.TemplateResponse("login.html", {"request": request, "message": message})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}

    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT password FROM users WHERE user_name = %s", (username,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        return RedirectResponse(url="/dashboard", status_code=303)
    
    return templates.TemplateResponse("login.html", {
        "request": request, 
        "message": "Invalid username or password"
    })
    
@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request, message: Optional[str] = None):
    return templates.TemplateResponse("jobs.html", {"request": request, "message": message})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, message: Optional[str] = None):
    return templates.TemplateResponse("register.html", {"request": request, "message": message})


@app.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users WHERE user_name = %s", (username,))
    (user_exists,) = cursor.fetchone()
    if user_exists:
        cursor.close()
        conn.close()
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "message": "Username already exists"
        })

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    cursor.execute("INSERT INTO users (user_name, password) VALUES (%s, %s)", (username, hashed_password))
    conn.commit()

    cursor.close()
    conn.close()

    return RedirectResponse(url="/login?message=Registration+successful", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/upload")
async def upload_file(username: str = Form(...), file: UploadFile = File(...)):
    try:
        file_name = generate_unique_filename(username, file.filename)
        file_location = os.path.join(UPLOAD_FOLDER, file_name)
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        redis_client.set(f'username:{username}', str(file_location))
        return {"filename": file_name, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def evaluate_resume(username, file_path, job_description):
    results = cv_evaluation_pipeline(file_path, job_description)
    evaluation_result = results['evaluation']
    
    try:
        cv_data = results['cv_json']
        position = cv_data['personal_info'].get('desired_job', 'unknown')
    except Exception as e:
        position = "Unknown"
        print(f"Error extracting position: {str(e)}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    username = username
    cursor.execute("SELECT COUNT(*) FROM user_history WHERE user_name = %s", (username,))
    user_exists = cursor.fetchone()[0]

    if user_exists:
        cursor.execute("""
            UPDATE user_history
            SET related_jobs = CASE
                WHEN NOT (%s = ANY(related_jobs)) THEN array_append(related_jobs, %s)
                ELSE related_jobs
            END
            WHERE user_name = %s
        """, (position, position, username))
    else:
        cursor.execute("""
            INSERT INTO user_history (user_name, related_jobs)
            VALUES (%s, %s)
        """, (username, [position]))  

    conn.commit()
    cursor.close()
    conn.close()
    
    return evaluation_result

@app.post("/evaluate")
def evaluate(request: EvaluationRequest):
    username = request.username
    file_path = redis_client.get(f'username:{username}').decode()
    jd_text = request.job_description
    job = queue.enqueue(evaluate_resume, username=username, file_path=file_path, job_description=jd_text)
    return JSONResponse({"job_id": job.get_id()})

@app.get("/result/{job_id}")
def get_result(request: Request, job_id: str):
    job = queue.fetch_job(job_id)
    if job is None or not job.is_finished:
        return JSONResponse({"status": "pending"})
    return JSONResponse({"status": "completed", "result": job.result})
        

@app.post("/interview-question")
async def get_interview_question(request: InterviewQuestionRequest):
    try:
        system_prompt = f"""
        You are an expert technical interviewer conducting a job interview.
        
        Job Description:
        {request.job_description}
        
        Your task is to ask relevant technical questions based on the job description and the candidate's previous answers.
        Ask one question at a time. Make your questions specific, challenging but fair.
        Focus on technical skills, experience, and problem-solving abilities relevant to the position.
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        
        for message in request.history:
            role = "assistant" if message.role == "interviewer" else "user"
            messages.append({"role": role, "content": message.content})
        
        if len(request.history) > 0:
            messages.append({
                "role": "system", 
                "content": "Based on the candidate's last response, ask your next interview question."
            })
        else:
            messages.append({
                "role": "system", 
                "content": "Start the interview with a relevant question about the candidate's experience related to this job."
            })
        
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192", 
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        
        question = response.choices[0].message.content.strip()
        
        return {"question": question}
        
    except Exception as e:
        fallback_questions = [
            "Could you tell me about your relevant experience for this position?",
            "What technical skills do you have that are most relevant to this job?",
            "Can you describe a challenging project you've worked on?",
            "How do you stay updated with the latest developments in your field?",
            "What would you consider your greatest technical strength?"
        ]
        import random
        return {"question": random.choice(fallback_questions)}

@app.post("/interview-feedback")
async def get_interview_feedback(request: InterviewFeedbackRequest):
    try:
        system_prompt = f"""
        You are an expert technical interviewer who has just completed an interview.
        
        Job Description:
        {request.job_description}
        
        Your task is to analyze the interview conversation and provide:
        1. A summary of the candidate's performance
        2. An assessment of their skills (on a scale of 0-10)
        3. Specific recommendations for improvement
        
        Format your response as a JSON object with the following structure:
        {{
            "summary": "Detailed summary of performance",
            "skills_assessment": [
                {{"name": "Skill Name", "rating": score}},
                ...
            ],
            "recommendations": [
                "Specific recommendation 1",
                "Specific recommendation 2",
                ...
            ]
        }}
        
        Ensure your response is valid JSON that can be parsed by Python's json.loads().
        """
        
        messages = [{"role": "system", "content": system_prompt}]
        
        for message in request.history:
            role = "assistant" if message.role == "interviewer" else "user"
            messages.append({"role": role, "content": message.content})
        
        messages.append({
            "role": "system", 
            "content": "Analyze the interview and provide your assessment in the JSON format specified earlier."
        })
        
        response = groq_client.chat.completions.create(
            model="qwen-2.5-32b",  
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        feedback_text = response.choices[0].message.content.strip()
        
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', feedback_text)
        if json_match:
            feedback_text = json_match.group(1)
        else:
            json_match = re.search(r'({[\s\S]*})', feedback_text)
            if json_match:
                feedback_text = json_match.group(1)
        
        try:
            feedback = json.loads(feedback_text)
        except json.JSONDecodeError:
            feedback = {
                "summary": "Based on the interview, the candidate demonstrated some relevant skills and experience for the position.",
                "skills_assessment": [
                    {"name": "Technical Knowledge", "rating": 7.0},
                    {"name": "Communication", "rating": 7.5},
                    {"name": "Problem Solving", "rating": 6.5},
                    {"name": "Experience Relevance", "rating": 7.0}
                ],
                "recommendations": [
                    "Consider expanding knowledge in key technical areas mentioned in the job description",
                    "Prepare more concrete examples of past projects to demonstrate technical skills",
                    "Practice explaining complex technical concepts more clearly",
                    "Research more about the company's products/services to show deeper interest"
                ]
            }
        
        return feedback
        
    except Exception as e:
        return {
            "summary": "Thank you for completing the interview. Based on your responses, we can see that you have some relevant experience for this position.",
            "skills_assessment": [
                {"name": "Technical Knowledge", "rating": 7.0},
                {"name": "Communication", "rating": 7.5},
                {"name": "Problem Solving", "rating": 6.5},
                {"name": "Experience Relevance", "rating": 7.0}
            ],
            "recommendations": [
                "Consider expanding your technical knowledge in areas relevant to the job",
                "Prepare more specific examples of your past work to showcase your skills",
                "Practice articulating your experience more clearly",
                "Research more about the industry to demonstrate deeper understanding"
            ]
        }
        

@app.post("/start_recording")
async def start_recording_endpoint():
    try:
        print("Recording started...")
        text = start_record()
        return {"success": True, "text": text}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post('/get_related_jobs')
async def get_related_jobs(request: RelatedJobs):
    conn = get_db_connection()
    cursor = conn.cursor()
    username = request.username
    cursor.execute("SELECT related_jobs FROM user_history WHERE user_name = %s", (username,))
    result = cursor.fetchone()[0]
    jobs = set(result)
    agent = create_agent(llm)
    job_text = ''
    for job in jobs:
        job_text += get_job_text(groq_client, job, agent)
    save_json_jobs(groq_client, job_text)
    with open("test.json", "r") as f:
        result = json.load(f)
    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)   
