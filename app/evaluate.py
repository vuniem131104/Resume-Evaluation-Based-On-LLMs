import json
from groq import Groq
from pypdf import PdfReader
from dotenv import load_dotenv
import os
from utils import encode_image, pdf_to_images

load_dotenv()

groq_api_key1 = os.getenv("GROQ_API_KEY1")
groq_api_key2 = os.getenv("GROQ_API_KEY2")
groq_api_key3 = os.getenv("GROQ_API_KEY3")
groq_api_key4 = os.getenv("GROQ_API_KEY4")

client1 = Groq(api_key=groq_api_key1)
client2 = Groq(api_key=groq_api_key2)
client3 = Groq(api_key=groq_api_key3)
client4 = Groq(api_key=groq_api_key4)

def evaluate_match_prompt(cv_json, jd_json):
    prompt = f"""
    You are an expert in evaluating the match between a candidate's CV and job requirements (JD). Please thoroughly analyze and assess how well the candidate fits the job position.
    DO NOT ADD: "```json" or "```" or any explanation, greeting, or wrapping.
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
       - Education Score (0-10): Based on the match of degree, field of study, and institution.
       - Experience Score (0-20): Based on years of experience and relevance of experience.
       - Technical Skills Score (0-20): Based on the match and proficiency level of technical skills.
       - Soft Skills Score (0-10): Based on the match of soft skills.
       - Projects and Achievements Score (0-20): Based on the relevance and impressiveness of projects and achievements.

    3. Conclusion:
       - Total Score (0-80): Sum of scores from the above criteria.
       - Overall Assessment: Overall evaluation of the candidate's fit.
       - Strengths: List 3-5 notable strengths of the candidate for the position.
       - Weaknesses: List 3-5 weaknesses or gaps of the candidate for the position.
       - Recommendation: Suggest whether to invite the candidate for an interview or not.

    Return the evaluation result in the following JSON format without saying anything else for me to parse it correctly:
    {{
        "evaluation": {{
            "education_score": "Education score (0-10)",
            "experience_score": "Experience score (0-20)",
            "technical_skills_score": "Technical skills score (0-20)",
            "soft_skills_score": "Soft skills score (0-10)",
            "projects_achievements_score": "Projects and achievements score (0-20)",
            "total_score": "Total score (0-80)"
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
    The input text may be in Vietnamese. You MUST translate it to English BEFORE analyzing it. Always return the final result in English only.
    
    Your task:
    1. Translate the following raw text from Vietnamese to English first.
    2. Then analyze the translated version and convert it into structured JSON format.
    3. DO NOT include the translated text — only return the final JSON result.

    IMPORTANT:
    - DO NOT include code blocks like ```json or ```.
    - DO NOT write any greeting, explanation, or wrapping.
    - Only return the pure JSON object.
    
    Below is the extracted text from a PDF file:
    "{text}"

    Please return exactly the result in the following JSON format:
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
    """
    response = client1.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",  
        messages=[
            {"role": "system", "content": "You are an expert in resume formatting."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  
        max_completion_tokens=2048
    )
    
    try:
        cv_json = json.loads(response.choices[0].message.content)
        return cv_json
    except json.JSONDecodeError:
        print("Error: Could not parse JSON from response")
        return None

def standardize_jd(jd_text):
    """Standardize JD using Groq LLM"""
    prompt = f"""
    You are a job description analysis expert. Please analyze the following job description and standardize it into a structured JSON format without saying anything else for me to parse it correctly.
    The job description may be in Vietnamese. You MUST translate it to English BEFORE analyzing it. Always return the final result in English only.
    
    Your task:
    1. Translate the following job description from Vietnamese to English first.
    2. Then analyze the translated version and convert it into structured JSON format.
    3. DO NOT include the translated text — only return the final JSON result.

    IMPORTANT:
    - DO NOT include code blocks like ```json or ```.
    - DO NOT write any greeting, explanation, or wrapping.
    - Only return the pure JSON object.
    Job description to analyze:
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
    """
    
    response = client2.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",  
        messages=[
            {"role": "system", "content": "You are a job description analysis expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,  
        max_completion_tokens=2048
    )
    
    try:
        jd_json = json.loads(response.choices[0].message.content)
        return jd_json
    except json.JSONDecodeError:
        print("Error: Could not parse JSON from response")
        return None

def evaluate_content(cv_json, jd_json):
    """Evaluate the match between CV and JD"""
    prompt = evaluate_match_prompt(json.dumps(cv_json), 
                                  json.dumps(jd_json))
    
    response = client3.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct", 
        messages=[
            {"role": "system", "content": "You are an expert in evaluating the match between a candidate's CV and job requirements."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,  
        max_completion_tokens=4096
    )
    
    try:
        content_evaluation = json.loads(response.choices[0].message.content)
        return content_evaluation
    except json.JSONDecodeError:
        print("Error: Could not parse JSON from response")
        return None

def evaluate_layout(username, file_path):
    """Evaluate the layout of the CV"""
    prompt = f"""
    You are a professional recruiter and visual design expert. Your task is to evaluate the layout quality of a candidate's CV based on the provided image.

    Focus only on the **visual and structural design**, not the content. Assess how well the layout supports readability, clarity, and professional appearance.

    Score the following layout criteria from 0 (very poor) to 20 (excellent):

    1. header_score — Is the name and job title prominently and clearly displayed?
    2. contact_info_score — Is the contact section easy to find and neatly arranged?
    3. section_structure_score — Are the sections (Education, Experience, Skills, etc.) logically ordered and clearly separated?
    4. alignment_score — Are the elements (text blocks, headings) consistently aligned throughout the CV?
    5. font_style_score — Are font choices consistent and easy to read?
    6. whitespace_balance_score — Is there good use of margins and spacing between elements?
    7. visual_hierarchy_score — Is there a clear visual distinction between headings, subheadings, and body text?
    8. overall_layout_score — How professional and polished is the overall layout?

    Additionally, list any **layout-related issues** (e.g., inconsistent alignment, cluttered sections), and provide a short summary comment.
    
    IMPORTANT:
    - DO NOT include code blocks like ```json or ```.
    - DO NOT write any greeting, explanation, or wrapping.
    - Only return the pure JSON object.
    
    Return the result strictly in this JSON format:

    {{
    "header_score": (0-20),
    "contact_info_score": (0-20),
    "section_structure_score": (0-20),
    "alignment_score": (0-20),
    "font_style_score": (0-20),
    "whitespace_balance_score": (0-20),
    "visual_hierarchy_score": (0-20),
    "overall_layout_score": (0-20),
    "issues": [ "string describing issue 1", "string describing issue 2", ... ],
    "comments": "brief summary of layout quality (1-2 sentences)"
    }}
    """
    image_paths = pdf_to_images(username, file_path)
    content = [{"type": "text", "text": prompt}]
    for image_path in image_paths:
        base64_image = encode_image(image_path)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}",
            },
        })
        
    response = client4.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=1,
        max_completion_tokens=1024,
    )
    
    try:
        layout_evaluation = json.loads(response.choices[0].message.content)
        return layout_evaluation
    except json.JSONDecodeError:
        print("Error: Could not parse JSON from response")
        return None

def cv_evaluation_pipeline(username, file_path, jd_text):
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
    
    print("Step 3: Evaluating content match...")
    content_evaluation = evaluate_content(cv_json, jd_json)
    if not content_evaluation:
        return {"error": "Could not evaluate content match"}
    
    print("Step 4: Evaluating layout...")
    layout_evaluation = evaluate_layout(username, file_path)
    if not layout_evaluation:
        return {"error": "Could not evaluate layout"}
    
    print("Step 5: Combining results...")
    print("Final step: Done!!!")
    
    # with open("cv_extracted.json", "w") as f:
    #     json.dump(cv_json, f, indent=2)
    
    # with open("jd_standardized.json", "w") as f:
    #     json.dump(jd_json, f, indent=2)
    
    # with open("content_evaluation.json", "w") as f:
    #     json.dump(content_evaluation, f, indent=2)
    
    # with open("layout_evaluation.json", "w") as f:
    #     json.dump(layout_evaluation, f, indent=2)
    
    return {
        "cv_json": cv_json,
        "jd_json": jd_json,
        "content_evaluation": content_evaluation,
        "layout_evaluation": layout_evaluation
    }

