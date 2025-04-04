from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
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
from record import start_record
import uvicorn
import psycopg2
import psycopg2.extras
import bcrypt

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

    
class EvaluationRequest(BaseModel):
    job_description: Optional[str] = None
    username: Optional[str] = None

class InterviewMessage(BaseModel):
    role: str  # "interviewer" hoặc "candidate"
    content: str

class InterviewQuestionRequest(BaseModel):
    job_description: str
    history: List[InterviewMessage] = []

class InterviewFeedbackRequest(BaseModel):
    job_description: str
    history: List[InterviewMessage]
    
app = FastAPI(title="Resume Evaluation System")

# Cấu hình thư mục uploads
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Cấu hình static files và templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

def get_db_connection():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except Exception as e:
        print("Database connection error:", e)
        return None


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


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, message: Optional[str] = None):
    return templates.TemplateResponse("register.html", {"request": request, "message": message})


@app.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    if not conn:
        return {"error": "Database connection failed"}
    
    cursor = conn.cursor()

    # Kiểm tra user đã tồn tại chưa
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_name = %s", (username,))
    (user_exists,) = cursor.fetchone()
    if user_exists:
        cursor.close()
        conn.close()
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "message": "Username already exists"
        })

    # Mã hóa mật khẩu với bcrypt
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Lưu vào database
    cursor.execute("INSERT INTO users (user_name, password) VALUES (%s, %s)", (username, hashed_password))
    conn.commit()

    cursor.close()
    conn.close()

    return RedirectResponse(url="/login?message=Registration+successful", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_location = os.path.join(UPLOAD_FOLDER, "test.pdf")
        with open(file_location, "wb") as file_object:
            shutil.copyfileobj(file.file, file_object)
        return {"filename": "test.pdf", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate")
async def evaluate_resume(request: EvaluationRequest):
    try:
        if request.job_description:
            with open("job_description.txt", "w") as f:
                jd_text = request.job_description
                f.write(jd_text)
        
        cv_evaluation_pipeline("uploads/test.pdf", jd_text)
        with open("evaluation_result.json", "r") as f:
            evaluation_result = json.load(f)
        
        # Extract position from cv_extracted.json
        try:
            with open("cv_extracted.json", "r") as f:
                cv_data = json.load(f)
                position = cv_data['personal_info'].get('desired_job', 'unknown')
        except Exception as e:
            position = "Unknown"
            print(f"Error extracting position: {str(e)}")
        
        # Connect to PostgreSQL and update/insert position
        conn = get_db_connection()
        cursor = conn.cursor()
        username = request.username
        # Kiểm tra user đã tồn tại chưa, nếu có thì update
        cursor.execute("SELECT COUNT(*) FROM user_history WHERE user_name = %s", (username,))
        user_exists = cursor.fetchone()[0]

        if user_exists:
            # Nếu user đã tồn tại, update position vào mảng related_jobs
            cursor.execute("""
                UPDATE user_history
                SET related_jobs = array_append(related_jobs, %s)
                WHERE user_name = %s
            """, (position, username))
        else:
            # Nếu user chưa tồn tại, insert vào bảng
            cursor.execute("""
                INSERT INTO user_history (user_name, related_jobs)
                VALUES (%s, %s)
            """, (username, [position]))  # Chuyển position thành mảng

        conn.commit()
        cursor.close()
        conn.close()
        
        return evaluation_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading evaluation result: {str(e)}")

# Thêm endpoint cho phỏng vấn ảo
@app.post("/interview-question")
async def get_interview_question(request: InterviewQuestionRequest):
    try:
        # Xây dựng prompt cho Groq LLM
        system_prompt = f"""
        You are an expert technical interviewer conducting a job interview.
        
        Job Description:
        {request.job_description}
        
        Your task is to ask relevant technical questions based on the job description and the candidate's previous answers.
        Ask one question at a time. Make your questions specific, challenging but fair.
        Focus on technical skills, experience, and problem-solving abilities relevant to the position.
        """
        
        # Xây dựng lịch sử hội thoại cho LLM
        messages = [{"role": "system", "content": system_prompt}]
        
        # Thêm lịch sử hội thoại
        for message in request.history:
            role = "assistant" if message.role == "interviewer" else "user"
            messages.append({"role": role, "content": message.content})
        
        # Thêm prompt cho câu hỏi tiếp theo
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
        
        # Gọi API Groq
        response = groq_client.chat.completions.create(
            model="llama3-70b-8192",  # hoặc model khác của Groq
            messages=messages,
            temperature=0.7,
            max_tokens=200
        )
        
        # Lấy câu hỏi từ phản hồi của LLM
        question = response.choices[0].message.content.strip()
        
        return {"question": question}
        
    except Exception as e:
        # Fallback khi có lỗi
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
        # Xây dựng prompt cho Groq LLM
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
        
        # Xây dựng lịch sử hội thoại cho LLM
        messages = [{"role": "system", "content": system_prompt}]
        
        # Thêm lịch sử hội thoại
        for message in request.history:
            role = "assistant" if message.role == "interviewer" else "user"
            messages.append({"role": role, "content": message.content})
        
        # Thêm prompt yêu cầu phản hồi
        messages.append({
            "role": "system", 
            "content": "Analyze the interview and provide your assessment in the JSON format specified earlier."
        })
        print(messages)
        # Gọi API Groq
        response = groq_client.chat.completions.create(
            model="qwen-2.5-32b",  # hoặc model khác của Groq
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Lấy phản hồi từ LLM và chuyển đổi thành JSON
        feedback_text = response.choices[0].message.content.strip()
        
        # Xử lý trường hợp khi phản hồi có thể chứa markdown hoặc các ký tự đặc biệt
        # Tìm và trích xuất phần JSON từ phản hồi
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', feedback_text)
        if json_match:
            feedback_text = json_match.group(1)
        else:
            # Tìm phần JSON bắt đầu từ { và kết thúc bằng }
            json_match = re.search(r'({[\s\S]*})', feedback_text)
            if json_match:
                feedback_text = json_match.group(1)
        
        try:
            feedback = json.loads(feedback_text)
        except json.JSONDecodeError:
            # Nếu không parse được JSON, tạo một phản hồi mặc định
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
        # Fallback khi có lỗi
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


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)   
