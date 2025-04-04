import json
from groq import Groq
from pypdf import PdfReader
from dotenv import load_dotenv
import os

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=groq_api_key)

def standardize_jd_prompt(jd_text):
    prompt = f"""
    You are a job description analysis expert. Please analyze the following JD and standardize it into a structured JSON format without saying anything else for me to parse it correctly.

    JD to analyze:
    ```
    {jd_text}
    ```

    Please return the result in the following JSON format:
    {{
        "job_info": {{
            "title": "Job title",
            "department": "Department",
            "level": "Level",
            "employment_type": "Employment type (Full-time, Part-time, etc.)",
            "location": "Work location"
        }},
        "requirements": {{
            "education": {{
                "degree": "Required degree",
                "field": "Field of study",
                "importance": "Importance level (1-10)"
            }},
            "experience": {{
                "years": "Required years of experience",
                "specific_domains": ["Specific experience domains"],
                "importance": "Importance level (1-10)"
            }},
            "technical_skills": [
                {{
                    "name": "Skill name",
                    "level": "Required proficiency level (Beginner, Intermediate, Advanced, Expert)",
                    "importance": "Importance level (1-10)"
                }}
            ],
            "soft_skills": [
                {{
                    "name": "Soft skill name",
                    "importance": "Importance level (1-10)"
                }}
            ],
            "languages": [
                {{
                    "name": "Language name",
                    "proficiency": "Proficiency level",
                    "importance": "Importance level (1-10)"
                }}
            ]
        }},
        "responsibilities": [
            {{
                "description": "Responsibility description",
                "importance": "Importance level (1-10)"
            }}
        ],
        "preferred_qualifications": [
            {{
                "description": "Preferred qualification description",
                "importance": "Importance level (1-10)"
            }}
        ]
    }}

    Please return only the JSON, without any additional explanatory text.
    """
    return prompt

def evaluate_match_prompt(cv_json, jd_json):
    prompt = f"""
    You are an expert in evaluating the match between a candidate's CV and job requirements (JD). Please thoroughly analyze and assess how well the candidate fits the job position.

    Candidate's CV (JSON format):
    ```json
    {cv_json}
    ```

    Job Description (JD) (JSON format):
    ```json
    {jd_json}
    ```

    Please evaluate the match according to the following criteria and score on a scale of 100:

    1. Detailed Analysis:
       - Education: Compare the candidate's degree, field of study, and institution with the requirements in the JD.
       - Work Experience: Compare the years of experience and domains of experience with the requirements.
       - Technical Skills: Compare the candidate's technical skills with the requirements, considering proficiency levels.
       - Soft Skills: Compare the candidate's soft skills with the requirements.
       - Languages: Compare the candidate's language abilities with the requirements.
       - Projects and Achievements: Assess the relevance of projects and achievements to the job position.

    2. Scoring:
       - Education Score (0-15): Based on the match of degree, field of study, and institution.
       - Experience Score (0-30): Based on years of experience and relevance of experience.
       - Technical Skills Score (0-25): Based on the match and proficiency level of technical skills.
       - Soft Skills Score (0-10): Based on the match of soft skills.
       - Language Score (0-10): Based on required language abilities.
       - Projects and Achievements Score (0-10): Based on the relevance and impressiveness of projects and achievements.

    3. Conclusion:
       - Total Score (0-100): Sum of scores from the above criteria.
       - Overall Assessment: Overall evaluation of the candidate's fit.
       - Strengths: List 3-5 notable strengths of the candidate for the position.
       - Weaknesses: List 3-5 weaknesses or gaps of the candidate for the position.
       - Recommendation: Suggest whether to invite the candidate for an interview or not.

    Return the evaluation result in the following JSON format without saying anything else for me to parse it correctly:
    {{
        "evaluation": {{
            "education_score": "Education score (0-15)",
            "experience_score": "Experience score (0-30)",
            "technical_skills_score": "Technical skills score (0-25)",
            "soft_skills_score": "Soft skills score (0-10)",
            "language_score": "Language score (0-10)",
            "projects_achievements_score": "Projects and achievements score (0-10)",
            "total_score": "Total score (0-100)"
        }},
        "analysis": {{
            "education_analysis": "Detailed analysis of education",
            "experience_analysis": "Detailed analysis of experience",
            "skills_analysis": "Detailed analysis of skills",
            "overall_comment": "Overall assessment",
            "strengths": ["Strength 1", "Strength 2", "..."],
            "weaknesses": ["Weakness 1", "Weakness 2", "..."],
            "recommendation": "Recommendation (Should interview / Need further consideration / Not suitable)"
        }}
    }}
    
    Please return only the JSON, without any additional explanatory text.
    """
    return prompt

def extract_text_from_pdf(pdf_path):
    """Trích xuất văn bản từ file PDF."""
    reader = PdfReader(pdf_path)
    extracted_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return extracted_text

def standardize_cv(text):
    """Standardize CV using Groq LLM"""
    prompt = f"""
    You are an AI assistant that formats raw extracted text into a structured resume. Please analyze the following text and standardize it into a structured JSON format without saying anything else for me to parse it correctly.
    Below is the extracted text from a PDF file:
    {text}

    Please return the result in the following JSON format:
    {{
        "personal_info": {{
            "name": "Candidate's full name (if available)",
            "email": "Contact email (if available)",
            "phone": "Phone number (if available)",
            "location": "Address (if available)",
            "desired_job": "Desired job title (if available)",
            "objective": ["List of career objectives (if available)"]
        }},
        "education": [
            {{
                "degree": "Degree (if available)",
                "institution": "School name",
                "field": "Field of study",
                "duration": "Study period",
                "gpa": "GPA (if available)",
                "details": {{}} 
            }}
        ],
        "work_experience": [
            {{
                "position": "Job position",
                "company": "Company name",
                "duration": "Employment period",
                "description": ["List of job responsibilities and achievements"]
            }}
        ],
        "skills": {{
            "technical": ["List of technical skills"],
            "soft": ["List of soft skills (if available)"],
            "languages": ["List of languages (if available)"]
        }},
        "projects": [
            {{
                "name": "Project name",
                "link": "Project link (if available)",
                "description": "Project description",
                "technologies": ["List of technologies used"],
                "main_tasks": ["List of main tasks or contributions"]
            }}
        ],
        "awards": ["List of awards and achievements"],
        "certificates": [
            {{
                "name": "Certificate name (if available)",
                "issuer": "Issuing organization (if available)",
                "date": "Issue date (if available)"
            }}
        ]
    }}
    Please return only the JSON, without any additional explanatory text.
    """
    response = client.chat.completions.create(
        model="llama3-70b-8192",  
        messages=[
            {"role": "system", "content": "You are an expert in resume formatting."},
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

def standardize_jd(jd_text):
    """Standardize JD using Groq LLM"""
    prompt = standardize_jd_prompt(jd_text)
    
    response = client.chat.completions.create(
        model="llama3-70b-8192",  
        messages=[
            {"role": "system", "content": "You are a job description analysis expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,  
        max_tokens=3000
    )
    
    try:
        jd_json = json.loads(response.choices[0].message.content)
        return jd_json
    except json.JSONDecodeError:
        print("Error: Could not parse JSON from response")
        return None

def evaluate_match(cv_json, jd_json):
    """Evaluate the match between CV and JD"""
    prompt = evaluate_match_prompt(json.dumps(cv_json), 
                                  json.dumps(jd_json))
    
    response = client.chat.completions.create(
        model="llama3-70b-8192",  # Use appropriate Groq model
        messages=[
            {"role": "system", "content": "You are an expert in evaluating the match between a candidate's CV and job requirements."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,  # Low temperature for consistent results but allowing some creativity in analysis
        max_tokens=4000
    )
    
    try:
        evaluation_result = json.loads(response.choices[0].message.content)
        return evaluation_result
    except json.JSONDecodeError:
        print("Error: Could not parse JSON from response")
        return None

def cv_evaluation_pipeline(file_path, jd_text):
    """Complete CV evaluation pipeline"""
    print("Step 1: Extracting information from CV...")
    cv_text = extract_text_from_pdf(file_path)
    cv_json = standardize_cv(cv_text)
    if not cv_json:
        return {"error": "Could not extract information from CV"}
    
    print("Step 2: Standardizing JD...")
    jd_json = standardize_jd(jd_text)
    if not jd_json:
        return {"error": "Could not standardize JD"}
    
    print("Step 3: Evaluating match...")
    evaluation_result = evaluate_match(cv_json, jd_json)
    if not evaluation_result:
        return {"error": "Could not evaluate match"}
    
    with open("cv_extracted.json", "w") as f:
        json.dump(cv_json, f, indent=2)
    
    with open("jd_standardized.json", "w") as f:
        json.dump(jd_json, f, indent=2)
    
    with open("evaluation_result.json", "w") as f:
        json.dump(evaluation_result, f, indent=2)
    
    return {
        "cv_json": cv_json,
        "jd_json": jd_json,
        "evaluation": evaluation_result
    }

