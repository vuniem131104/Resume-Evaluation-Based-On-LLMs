import sounddevice as sd
import numpy as np
import whisper
import wave
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
import json 
import uuid
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv
import os

load_dotenv()

SAMPLERATE = 16000  
SILENCE_THRESHOLD = 500  
SILENCE_DURATION = 2  

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

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

def get_job_text(groq_client, job_title, agent):
    user_input = f"""
    Search for the best available job listings for a '{job_title}' position located in Hanoi, Vietnam.
    Only include jobs posted within the last 14 days.
    Focus on high-quality opportunities from top companies or startups in the relevant field.
    For each job, provide:
    1. Job title
    2. Company name
    3. Location
    4. Short job description
    5. Direct link to the job posting (do not fake the link)
    6. Date posted

    Only include jobs that are specifically related to the '{job_title}' role (not unrelated listings).
    Return exactly 5 of the most relevant listings.
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

    {job_text}
    """
    
    response = groq_client.chat.completions.create(
        model="llama3-70b-8192",  
        messages=[
            {"role": "system", "content": "You extract structured JSON from text."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  
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

