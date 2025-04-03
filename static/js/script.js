document.addEventListener('DOMContentLoaded', function() {
    // File upload handling
    const dropArea = document.querySelector('.file-drop-area');
    const fileInput = document.querySelector('.file-input');
    const fileNameDisplay = document.getElementById('file-name-display');
    const uploadForm = document.getElementById('upload-form');
    const evaluateBtn = document.getElementById('evaluate-btn');
    const jobDescriptionInput = document.getElementById('job-description');
    const saveJdBtn = document.getElementById('save-jd-btn');
    const clearJdBtn = document.getElementById('clear-jd-btn');
    
    // Virtual Interview elements
    const startInterviewBtn = document.getElementById('start-interview-btn');
    const virtualInterviewSection = document.getElementById('virtual-interview-section');
    const interviewMessages = document.getElementById('interview-messages');
    const interviewAnswer = document.getElementById('interview-answer');
    const sendAnswerBtn = document.getElementById('send-answer-btn');
    const endInterviewBtn = document.getElementById('end-interview-btn');
    const interviewResults = document.getElementById('interview-results');
    const interviewSummaryText = document.getElementById('interview-summary-text');
    const interviewSkillsList = document.getElementById('interview-skills-list');
    const interviewRecommendationsList = document.getElementById('interview-recommendations-list');
    const downloadReportBtn = document.getElementById('download-report-btn');
    const backToEvaluationBtn = document.getElementById('back-to-evaluation-btn');
    const recordingBtn = document.getElementById('record-answer-btn')
    
    let uploadedFileName = '';
    let fileUploaded = false;
    let jdSaved = false;
    
    let isRecording = false;
    let answer = '';
    
    // Kiểm tra xem có thể kích hoạt nút đánh giá hay không
    function checkEvaluateButtonState() {
        if (evaluateBtn) {
            evaluateBtn.disabled = !(fileUploaded && jdSaved);
        }
    }
    
    if (dropArea) {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Highlight drop area when item is dragged over
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            dropArea.classList.add('is-active');
        }
        
        function unhighlight() {
            dropArea.classList.remove('is-active');
        }
        
        // Handle dropped files
        dropArea.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length) {
                fileInput.files = files;
                updateFileNameDisplay(files[0].name);
            }
        }
        
        // Handle file input change
        fileInput.addEventListener('change', function() {
            if (fileInput.files.length) {
                updateFileNameDisplay(fileInput.files[0].name);
            }
        });
        
        function updateFileNameDisplay(fileName) {
            fileNameDisplay.textContent = `Selected file: ${fileName}`;
            uploadedFileName = fileName;
        }
        
        // Handle form submission
        if (uploadForm) {
            uploadForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                if (!fileInput.files.length) {
                    alert('Please select a file first!');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        alert('File uploaded successfully!');
                        fileUploaded = true;
                        checkEvaluateButtonState();
                    } else {
                        alert('Error uploading file.');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('An error occurred during file upload.');
                }
            });
        }
    }
    
    // Job Description handling
    if (saveJdBtn) {
        saveJdBtn.addEventListener('click', function() {
            const jdText = jobDescriptionInput.value.trim();
            if (!jdText) {
                alert('Please enter a job description.');
                return;
            }
            
            // Lưu JD vào localStorage để sử dụng sau này
            localStorage.setItem('jobDescription', jdText);
            alert('Job description saved!');
            jdSaved = true;
            checkEvaluateButtonState();
        });
    }
    
    if (clearJdBtn) {
        clearJdBtn.addEventListener('click', function() {
            jobDescriptionInput.value = '';
            localStorage.removeItem('jobDescription');
            jdSaved = false;
            checkEvaluateButtonState();
        });
    }
    
    // Khôi phục JD từ localStorage nếu có
    if (jobDescriptionInput && localStorage.getItem('jobDescription')) {
        jobDescriptionInput.value = localStorage.getItem('jobDescription');
        jdSaved = true;
        checkEvaluateButtonState();
    }
    
    // Evaluation button handling
    if (evaluateBtn) {
        evaluateBtn.addEventListener('click', async function() {
            if (!fileUploaded) {
                alert('Please upload a resume first.');
                return;
            }
            
            if (!jdSaved) {
                alert('Please save a job description first.');
                return;
            }
            
            try {
                // Hiển thị thông báo đang đánh giá
                const evaluationPlaceholder = document.getElementById('evaluation-placeholder');
                if (evaluationPlaceholder) {
                    evaluationPlaceholder.innerHTML = '<p>Evaluating resume... Please wait.</p>';
                }
                
                // Lấy JD từ localStorage
                const jobDescription = localStorage.getItem('jobDescription');
                
                // Gọi API để lấy kết quả đánh giá
                const response = await fetch('/evaluate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ job_description: jobDescription })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                displayEvaluationResults(result);
                
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred during evaluation: ' + error.message);
            }
        });
    }
    
    // Display evaluation results
    function displayEvaluationResults(results) {
        const evaluationResults = document.getElementById('evaluation-results');
        const evaluationPlaceholder = document.getElementById('evaluation-placeholder');
        
        if (evaluationResults && evaluationPlaceholder) {
            // Update progress bars and scores
            document.getElementById('skills-progress').style.width = `${results.evaluation.technical_skills_score * 4}%`;
            document.getElementById('experience-progress').style.width = `${results.evaluation.experience_score * 3.33}%`;
            document.getElementById('education-progress').style.width = `${results.evaluation.education_score * 6.67}%`;
            document.getElementById('soft-skills-progress').style.width = `${results.evaluation.soft_skills_score * 10}%`;
            document.getElementById('language-progress').style.width = `${results.evaluation.language_score * 10}%`;
            document.getElementById('projects-achievements-progress').style.width = `${results.evaluation.projects_achievements_score * 10}%`;
            document.getElementById('overall-progress').style.width = `${results.evaluation.total_score}%`;
            
            document.getElementById('skills-score').textContent = `${results.evaluation.technical_skills_score}/25`;
            document.getElementById('experience-score').textContent = `${results.evaluation.experience_score}/30`;
            document.getElementById('education-score').textContent = `${results.evaluation.education_score}/15`;
            document.getElementById('soft-skills-score').textContent = `${results.evaluation.soft_skills_score}/10`;
            document.getElementById('language-score').textContent = `${results.evaluation.language_score}/10`;
            document.getElementById('projects-achievements-score').textContent = `${results.evaluation.projects_achievements_score}/10`;
            document.getElementById('overall-score').textContent = `${results.evaluation.total_score}/100`;
            
            // Update suggestions
            const suggestionList = document.getElementById('suggestion-list');
            suggestionList.innerHTML = '';
            
            // Add strengths
            const strengthsHeader = document.createElement('h5');
            strengthsHeader.textContent = 'Strengths:';
            suggestionList.appendChild(strengthsHeader);
            
            results.analysis.strengths.forEach(strength => {
                const li = document.createElement('li');
                li.textContent = strength;
                li.classList.add('strength');
                suggestionList.appendChild(li);
            });
            
            // Add weaknesses
            const weaknessesHeader = document.createElement('h5');
            weaknessesHeader.textContent = 'Areas for Improvement:';
            weaknessesHeader.style.marginTop = '15px';
            suggestionList.appendChild(weaknessesHeader);
            
            results.analysis.weaknesses.forEach(weakness => {
                const li = document.createElement('li');
                li.textContent = weakness;
                li.classList.add('weakness');
                suggestionList.appendChild(li);
            });
            
            // Add recommendation
            const recommendationDiv = document.createElement('div');
            recommendationDiv.classList.add('recommendation');
            recommendationDiv.innerHTML = `
                <h5>Recommendation:</h5>
                <p>${results.analysis.recommendation}</p>
            `;
            suggestionList.appendChild(recommendationDiv);
            
            // Show results and hide placeholder
            evaluationResults.classList.remove('hidden');
            evaluationPlaceholder.classList.add('hidden');
        }
    }
    
    // Virtual Interview Handling
    if (startInterviewBtn) {
        startInterviewBtn.addEventListener('click', function() {
            // Show interview section
            virtualInterviewSection.classList.remove('hidden');
            
            // Scroll to interview section
            virtualInterviewSection.scrollIntoView({ behavior: 'smooth' });
            
            // Reset interview state
            interviewHistory = [];
            interviewMessages.innerHTML = '';
            interviewInProgress = true;
            
            // Start the interview with welcome message
            addInterviewerMessage("Welcome to your virtual interview! I'll ask you questions based on your resume and the job description. Please answer them as you would in a real interview.");
            
            // Start the interview
            startInterview();
        });
    }
    
    async function startInterview() {
        try {
            // Show typing indicator
            showTypingIndicator();
            
            // Get job description
            const jobDescription = localStorage.getItem('jobDescription');
            
            // Call API to get first interview question
            const response = await fetch('/interview-question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    job_description: jobDescription,
                    history: interviewHistory
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            // Remove typing indicator
            hideTypingIndicator();
            
            // Add the question to chat
            addInterviewerMessage(result.question);
            
            // Add to history
            interviewHistory.push({
                role: "interviewer",
                content: result.question
            });
            
        } catch (error) {
            console.error('Error starting interview:', error);
            hideTypingIndicator();
            
            // Fallback question if API fails
            const fallbackQuestion = "Could you tell me about your relevant experience for this position?";
            addInterviewerMessage(fallbackQuestion);
            
            interviewHistory.push({
                role: "interviewer",
                content: fallbackQuestion
            });
        }
    }
    
    function showTypingIndicator() {
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('typing-indicator');
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        typingIndicator.id = 'typing-indicator';
        interviewMessages.appendChild(typingIndicator);
        interviewMessages.scrollTop = interviewMessages.scrollHeight;
    }
    
    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    function addInterviewerMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'interviewer-message');
        messageDiv.textContent = message;
        interviewMessages.appendChild(messageDiv);
        interviewMessages.scrollTop = interviewMessages.scrollHeight;
    }
    
    function addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'user-message');
        messageDiv.textContent = message;
        interviewMessages.appendChild(messageDiv);
        interviewMessages.scrollTop = interviewMessages.scrollHeight;
    }

    if (recordingBtn) {
        recordingBtn.addEventListener('click', async function() {
            isRecording = true; 
            try {
                const response = await fetch('/start_recording', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                data = await response.json();

                if (data.success) {
                    interviewAnswer.value = data.text;
                } else {
                    console.error("Error in recording");
                }
            } catch (error) {
                console.error("Request failed:", error);
            }
        });
    }
    
    if (sendAnswerBtn) {
        sendAnswerBtn.addEventListener('click', async function() {
            if (isRecording) {
                isRecording = false; 
            }

            answer = interviewAnswer.value.trim();

            
            if (!answer) {
                alert('Please type an answer before sending.');
                return;
            }
            
            // Add user's answer to chat
            addUserMessage(answer);
            
            // Add to history
            interviewHistory.push({
                role: "candidate",
                content: answer
            });
            
            // Clear the input
            interviewAnswer.value = '';
            
            // Get next question
            try {
                // Show typing indicator
                showTypingIndicator();
                
                // Get job description
                const jobDescription = localStorage.getItem('jobDescription');
                
                // Call API to get next interview question
                const response = await fetch('/interview-question', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        job_description: jobDescription,
                        history: interviewHistory
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                
                // Remove typing indicator
                hideTypingIndicator();
                
                // Add the question to chat
                addInterviewerMessage(result.question);
                
                // Add to history
                interviewHistory.push({
                    role: "interviewer",
                    content: result.question
                });
                
            } catch (error) {
                console.error('Error getting next question:', error);
                hideTypingIndicator();
                
                // Fallback question if API fails
                const fallbackQuestions = [
                    "That's interesting. Can you tell me more about your technical skills?",
                    "How do you handle challenging situations in your work?",
                    "What are your career goals and how does this position fit into them?",
                    "Can you describe a project where you had to learn something new quickly?",
                    "What would you consider your greatest professional achievement?"
                ];
                
                const randomQuestion = fallbackQuestions[Math.floor(Math.random() * fallbackQuestions.length)];
                addInterviewerMessage(randomQuestion);
                
                interviewHistory.push({
                    role: "interviewer",
                    content: randomQuestion
                });
            }
        });
    }
    
    // Allow pressing Enter to send message
    if (interviewAnswer) {
        interviewAnswer.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendAnswerBtn.click();
            }
        });
    }
    
    if (endInterviewBtn) {
        endInterviewBtn.addEventListener('click', async function() {
            if (interviewHistory.length < 3) {
                alert('Please answer at least one question before ending the interview.');
                return;
            }
            
            try {
                // Disable the end button to prevent multiple clicks
                endInterviewBtn.disabled = true;
                endInterviewBtn.textContent = 'Generating Feedback...';
                
                // Show a message that we're generating feedback
                addInterviewerMessage("Thank you for completing the interview! I'm now analyzing your responses to provide personalized feedback.");
                
                // Get job description
                const jobDescription = localStorage.getItem('jobDescription');
                
                // Call API to get interview feedback
                const response = await fetch('/interview-feedback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        job_description: jobDescription,
                        history: interviewHistory
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                
                // Display the interview results
                displayInterviewResults(result);
                
                // Hide interview chat and show results
                document.querySelector('.interview-container').classList.add('hidden');
                interviewResults.classList.remove('hidden');
                
            } catch (error) {
                console.error('Error generating feedback:', error);
                alert('An error occurred while generating feedback. Please try again.');
                
                // Re-enable the button
                endInterviewBtn.disabled = false;
                endInterviewBtn.textContent = 'End Interview & Get Feedback';
            }
        });
    }
    
    function displayInterviewResults(results) {
        // Populate interview summary
        interviewSummaryText.textContent = results.summary;
        
        // Populate skills assessment
        interviewSkillsList.innerHTML = '';
        results.skills_assessment.forEach(skill => {
            const li = document.createElement('li');
            li.classList.add('skill-item');
            
            const skillRating = Math.round(skill.rating * 10) / 10; // Round to 1 decimal place
            const percentage = skill.rating * 10; // Convert 0-10 scale to percentage
            
            li.innerHTML = `
                <span class="skill-name">${skill.name}</span>
                <div class="skill-rating">
                    <div class="skill-level">
                        <div class="skill-level-fill" style="width: ${percentage}%"></div>
                    </div>
                    <span>${skillRating}/10</span>
                </div>
            `;
            interviewSkillsList.appendChild(li);
        });
        
        // Populate recommendations
        interviewRecommendationsList.innerHTML = '';
        results.recommendations.forEach(recommendation => {
            const li = document.createElement('li');
            li.textContent = recommendation;
            interviewRecommendationsList.appendChild(li);
            });
        }
        
        if (downloadReportBtn) {
            downloadReportBtn.addEventListener('click', function() {
                // Create report content
                let reportContent = `
                    # Interview Assessment Report
                    
                    ## Summary
                    ${interviewSummaryText.textContent}
                    
                    ## Skills Assessment
                `;
                
                // Add skills
                const skillItems = interviewSkillsList.querySelectorAll('.skill-item');
                skillItems.forEach(item => {
                    const skillName = item.querySelector('.skill-name').textContent;
                    const skillRating = item.querySelector('.skill-rating span').textContent;
                    reportContent += `\n- ${skillName}: ${skillRating}`;
                });
                
                // Add recommendations
                reportContent += `\n\n## Recommendations`;
                const recommendations = interviewRecommendationsList.querySelectorAll('li');
                recommendations.forEach(item => {
                    reportContent += `\n- ${item.textContent}`;
                });
                
                // Create a blob and download
                const blob = new Blob([reportContent], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'interview_assessment_report.md';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            });
        }
        
        if (backToEvaluationBtn) {
            backToEvaluationBtn.addEventListener('click', function() {
                // Hide interview results and section
                interviewResults.classList.add('hidden');
                virtualInterviewSection.classList.add('hidden');
                
                // Scroll back to evaluation section
                document.querySelector('.evaluation-section').scrollIntoView({ behavior: 'smooth' });
                
                // Reset interview state
                interviewHistory = [];
                interviewMessages.innerHTML = '';
                document.querySelector('.interview-container').classList.remove('hidden');
                
                // Reset button
                endInterviewBtn.disabled = false;
                endInterviewBtn.textContent = 'End Interview & Get Feedback';
            });
        }

        
    });

