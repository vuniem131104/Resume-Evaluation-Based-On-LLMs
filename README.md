# 🧠 Resume-Evaluation-Based-On-LLMs

A smart, asynchronous resume evaluation system powered by LLMs, Redis, and FastAPI. This system allows users to upload resumes, job descriptions and receive both general and personalized feedback through automated evaluation and virtual interviews.

## 🔧 Tech Stack

- **FastAPI** – API server
- **Redis** – Message queue and temporary result store
- **RQ / Celery** – Asynchronous task handling (e.g., resume evaluation)
- **Meta LLM** – Used for text extraction, job/resume standardization and evaluate by matching between standardized json files
- **Qwen 2.5** – Personalized feedback generation
- **OpenAI Whisper** – Voice recognition for virtual interviews
- **Tavily + Web Search Agent** – Recent job recommendations
- **PostgreSQL** – User history and job storage, user database
- **AWS S3** – Store resumes files uploaded by users

---

## 🚀 System Architecture

### 1. Resume Evaluation Flow

![pipeline](https://github.com/user-attachments/assets/f7beaabd-8bc4-4674-8bc0-7ad50a920aca)


- **Step 1**: Users upload their **resume** and provide the **job description**.
- **Step 2**: The system asynchronously extracts and standardizes text from both the resume and the job description using LLMs.
- **Step 3**: The evaluation task is queued via Redis and executed by workers. Once complete, the user receives a **non-personalized feedback**.
- **Optional**: If the user wants more personalized insights, they proceed to a virtual interview.

### 2. Virtual Interview and Personalized Feedback

- **Step 4**: The LLM generates interview questions based on the job description.
- **Step 5**: The user replies via text or voice (processed by Whisper).
- **Step 6**: The conversation is passed to Qwen 2.5, which generates **personalized feedback**.
- **Final**: Feedback is returned to the user.

---

### 3. Job Recommendation via Web Search Agent

![agent](https://github.com/user-attachments/assets/ce2733a7-4284-47e1-8822-f3997fccbe95)


- **Input**: User submits a request to find relevant jobs.
- **Process**:
  - Job preferences are fetched from **PostgreSQL**.
  - Tavily-powered **Web Search Agent** fetches the latest related job postings.
- **Output**: Returned to the user.

---


## ⚙️ How It Works (Key Points)

- Uses **Redis** to enqueue/dequeue long-running tasks like resume evaluation.
- Separation between **upload** and **evaluation** actions to allow flexibility for users.
- Fully **asynchronous**, scalable design with pluggable LLMs.
- Feedback available in 2 modes: quick general or in-depth personalized.

---

## 🧪 How to Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/your-username/Resume-Evaluation-Based-On-LLMs.git
cd Resume-Evaluation-Based-On-LLMs

# 2. Set up virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Start Redis server
redis-server

# 4. Run the FastAPI app
uvicorn app.main:app --reload

# 5. In another terminal, start the workers
python resume_evaluation_worker.py # for resume evaluation worker
python related_jobs_worker.py # for related jobs retrieval worker
```

---


## 📌 Future Improvements

- Add OAuth2 login for real users
- Enable file storage via S3 or MinIO
- Add analytics dashboard for job fit trends
- Implement feedback history per user

