import sounddevice as sd
import numpy as np
import whisper
import wave
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
import json 
import uuid
import base64
import psycopg2
from psycopg2 import extras
from pdf2image import convert_from_path
import os

SAMPLERATE = 16000  
SILENCE_THRESHOLD = 500  
SILENCE_DURATION = 2  
TEMP_IMAGES_FOLDER = "temp_images" 

def is_silent(audio_chunk, silence_threshold=SILENCE_THRESHOLD):
    return np.max(np.abs(audio_chunk)) < silence_threshold

def start_record(chunk_duration=0.5, samplerate=SAMPLERATE, silence_duration=SILENCE_DURATION, model="base"):

    recorded_audio = []
    silent_time = 0

    while True:
        chunk = sd.rec(int(chunk_duration * samplerate), samplerate=samplerate, channels=1, dtype=np.int16)
        sd.wait()
        recorded_audio.append(chunk)
        
        if is_silent(chunk):
            silent_time += chunk_duration
        else:
            silent_time = 0  
        
        if silent_time >= silence_duration:
            break

    filename = "temp_audio.wav"
    recorded_audio = np.concatenate(recorded_audio, axis=0)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  
        wf.setframerate(samplerate)
        wf.writeframes(recorded_audio.tobytes())

    model = whisper.load_model(model)

    result = model.transcribe(filename)
    return result["text"]

def create_agent(llm):
    tavily_search_tool = TavilySearch(max_results=1)
    agent = create_react_agent(llm, [tavily_search_tool])
    return agent 

def get_job_text(job_title, agent):
    user_input = f"""
    You are a job search assistant. Your task is to find the top 5 **most relevant and high-quality** job listings for the position of **'{job_title}'** in **Vietnam**.

    Strict requirements:
    - The jobs **must be directly related** to the '{job_title}' role (e.g., matching title and relevant responsibilities).
    - Only include listings **posted within the last 14 days**.
    - Prioritize roles from **well-known companies, innovative startups, or industry leaders**.
    - Avoid duplicate, generic, or irrelevant listings.

    For each job, return **exactly and only** the following:
    1. **Job Title**
    2. **Company Name**
    3. **Location**
    4. **Concise Job Description** (max 3 sentences)
    5. **Direct and valid job posting link**
    6. **Date Posted** (e.g., "April 8, 2025")

    Additional Instructions:
    - Make sure each listing is **unique, verified**, and currently **open for applications**.
    - Do not fabricate or assume job links—include only real links.
    - Keep the response clean, well-formatted, and easy to read.

    Your output should be a numbered list of exactly **5** listings.
    """
    
    all_steps = []
    for step in agent.stream({"messages": user_input}, stream_mode="values"):
        all_steps.append(step["messages"][-1])
        
    job_text = all_steps[-1].content
    return job_text

def save_json_jobs(groq_client, job_text):
    prompt = f"""
    You will be given a list of job postings in plain text. Your task is to extract all jobs into a **valid JSON array** of objects, following this exact format:

    [
    {{
        "title": "Job Title",
        "company": "Company Name",
        "location": "Hanoi, Vietnam",
        "description": "Short but accurate job description",
        "link": "URL to the job posting",
        "datePosted": "X days ago"
    }},
    ...
    ]

    Instructions:
    - Only include the actual job entries that exist — do not generate or assume jobs.
    - Return only the **pure JSON array**, no explanation or wrapper.
    - Make sure the output is valid JSON and can be parsed by `json.loads()` in Python.

    Here is the job listings text:

    "{job_text}"
    """
    
    response = groq_client.chat.completions.create(
        model="llama3-70b-8192",  
        messages=[
            {"role": "system", "content": "You extract structured JSON from text."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,  
        max_tokens=3000
    )
    
    try:
        cv_json = json.loads(response.choices[0].message.content)
        return cv_json
    except json.JSONDecodeError:
        print("Error: Could not parse JSON from response")
        return None
        
def generate_unique_filename(username: str, file_name: str):
    extension = file_name.rsplit('.', 1)[1] if '.' in file_name else ''
    # resume_id = str(uuid.uuid4()).replace('-','')
    return f'{username}.{extension}'

def get_db_connection(db_host, db_name, db_user, db_password):
    try:
        return psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=5432
        )
    except Exception as e:
        print("Database connection error:", e)
        return None
    
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def pdf_to_images(user_name, pdf_path):
    """Convert PDF to a list of images, one per page"""
    try:
        images = convert_from_path(pdf_path)
        
        image_paths = []
 
        for i, image in enumerate(images):
            image_path = os.path.join(TEMP_IMAGES_FOLDER, f"{user_name}_page_{i+1}.jpeg")
            image.save(image_path, "JPEG")
            image_paths.append(image_path)
            
        return image_paths
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []