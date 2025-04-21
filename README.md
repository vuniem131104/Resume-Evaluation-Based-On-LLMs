# 🧠 Resume-Evaluation-Based-On-LLMs

A smart, asynchronous resume evaluation system powered by LLMs, Redis, and FastAPI. This system allows users to upload resumes, job descriptions and receive both general and personalized feedback through automated evaluation and virtual interviews.

## 🖥️ User Interface

### 1. Main
- Users upload their resumes and job descriptions here

![image](https://github.com/user-attachments/assets/0b1e9e1e-e6a6-4818-a79e-2cdbb703afba)


- Then, click "Evaluate Resume" button and receive result

![image](https://github.com/user-attachments/assets/4996f95e-de08-49dc-abb3-eba989a68594)


- Virtual Interview
  
![image](https://github.com/user-attachments/assets/63032caa-3301-4016-9360-552b84a5f174)


- Jobs recommedation based on users' history

![image](https://github.com/user-attachments/assets/7517e05d-b04f-432c-b535-d947c41281f1)


- Users' evaluation history
  
![image](https://github.com/user-attachments/assets/f9f2f28b-3a8e-414a-afca-e0c8f97feeb0)


## 🔧 Tech Stack

- **FastAPI** – API server
- **Redis** – Message queue and temporary result store
- **Redis Queue** – Asynchronous task handling (e.g., resume evaluation)
- **Llama 4** – Used for text extraction, job/resume standardization and evaluate content and layout of the resume. Also, it will serve as a virtual recruiter and give personalized feedback
- **OpenAI Whisper** – Voice recognition for virtual interviews
- **Tavily + Web Search Agent** – Recent job recommendations
- **MongoDB** – User history and job storage, user database
- **AWS S3** – Store resumes files uploaded by users

---

## 🚀 System Architecture

### 1. Resume Evaluation Flow

![pipeline](https://github.com/user-attachments/assets/40f75ec5-7624-4539-9e13-4c62e0013cea)

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

![agent](https://github.com/user-attachments/assets/9aefbf82-5c81-4066-b693-af843b57aaf4)


- **Input**: User submits a request to find relevant jobs.
- **Process**:
  - Job preferences are fetched from **MongoDB**.
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

### 1. Clone Repo
```bash
# 1. Clone the repo
git clone https://github.com/your-username/Resume-Evaluation-Based-On-LLMs.git
cd Resume-Evaluation-Based-On-LLMs/app

# 2. Set up virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Start Redis server
redis-server

# 4. Create .env file similar to .env.example in this repo then put it into folder app/

# 5. Run the FastAPI app
python main.py

# 6. In another terminal, start the workers
python resume_evaluation_worker.py # for resume evaluation worker
python related_jobs_worker.py # for related jobs retrieval worker
```

### 2. Docker
- Make sure that you have installed docker and docker-compose in your local machine :)))
- Your folder structur will look like this:
  
resume-application/

├── uploads/               
├── .env                   
└── docker-compose.yml

```bash
# 1. Create a folder in your local machine
mkdir resume-application && cd resume-application
mkdir uploads

# 2. Copy docker-compose-user.yml in this repo into the folder

# 3. Create .env file similar to .env.example in this repo

# 4. Run Application
docker-compose up -d
```

---


## 📌 Future Improvements

- Add OAuth2 login for real users
- Enable file storage via S3 or MinIO
- Add analytics dashboard for job fit trends
- Implement feedback history per user

