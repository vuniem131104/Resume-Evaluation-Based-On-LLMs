document.addEventListener('DOMContentLoaded', function() {
    let username = sessionStorage.getItem('username') || 'guest';
    
    async function loadHistory() {
        try {
            pollHistoryResults();
        } catch (error) {
            console.error('Error loading history:', error);
            document.getElementById('history-loader').classList.add('hidden');
            document.getElementById('no-history').classList.remove('hidden');
        }
    }
    
    async function pollHistoryResults() {
        try {
            const response = await fetch(`/get_history/${username}`);
            const data = await response.json();
            displayHistory(data.history);
        } catch (error) {
            console.error('Error polling history results:', error);
            document.getElementById('history-loader').classList.add('hidden');
            document.getElementById('no-history').classList.remove('hidden');
        }
    }
    
    function displayHistory(historyItems) {
        document.getElementById('history-loader').classList.add('hidden');
        
        if (!historyItems || historyItems.length === 0) {
            document.getElementById('no-history').classList.remove('hidden');
            return;
        }
        
        const historyContent = document.getElementById('history-content');
        historyContent.classList.remove('hidden');
        
        historyItems.sort((a, b) => {
            return new Date(b.evaluation_date) - new Date(a.evaluation_date);
        });
        
        historyItems.forEach((item, index) => {
            const result = item.evaluation_result;
            const totalScore = Math.round(result.total_score);
            
            const historyItemHtml = `
                <div class="history-item">
                    <div class="history-date">
                        <i class="fas fa-calendar-alt"></i> ${item.evaluation_date}
                    </div>
                    
                    <div class="total-score">
                        ${totalScore}/100
                    </div>
                    
                    <div class="history-jd" id="jd-${index}">
                        <strong>Job Description:</strong><br>
                        ${item.job_description.substring(0, 200)}${item.job_description.length > 200 ? '...' : ''}
                    </div>
                    ${item.job_description.length > 200 ? 
                        `<div class="read-more" onclick="toggleJd('jd-${index}', '${encodeURIComponent(item.job_description)}')">Read more</div>` : 
                        ''}
                    
                    <div class="resume-file">
                        <strong><i class="fas fa-file-alt"></i> Resume File:</strong> 
                        <a href="javascript:void(0)" onclick="viewResume('${item.resume_file}')">${item.resume_file.split('/').pop()}</a>
                    </div>
                    
                    <div class="history-scores">
                        <div class="score-chip">
                            <span><i class="fas fa-code"></i> Technical</span>
                            <span>${result.technical_score}/20</span>
                        </div>
                        <div class="score-chip">
                            <span><i class="fas fa-briefcase"></i> Experience</span>
                            <span>${result.experience_score}/20</span>
                        </div>
                        <div class="score-chip">
                            <span><i class="fas fa-graduation-cap"></i> Education</span>
                            <span>${result.education_score}/10</span>
                        </div>
                        <div class="score-chip">
                            <span><i class="fas fa-comments"></i> Soft Skills</span>
                            <span>${result.soft_skills_score}/10</span>
                        </div>
                        <div class="score-chip">
                            <span><i class="fas fa-tasks"></i> Projects</span>
                            <span>${result.projects_achievements_score}/20</span>
                        </div>
                        <div class="score-chip">
                            <span><i class="fas fa-columns"></i> Layout</span>
                            <span>${result.layout_score}/20</span>
                        </div>
                    </div>
                    
                    <div class="history-details">
                        <h4><i class="fas fa-plus-circle"></i> Strengths</h4>
                        <ul>
                            ${result.strengths.map(s => `<li>${s}</li>`).join('')}
                        </ul>
                        
                        <h4><i class="fas fa-minus-circle"></i> Areas to Improve</h4>
                        <ul>
                            ${result.weaknesses.map(w => `<li>${w}</li>`).join('')}
                        </ul>
                        
                        <h4><i class="fas fa-lightbulb"></i> Recommendations</h4>
                        <ul>
                            ${Array.isArray(result.recommendation) 
                                ? result.recommendation.map(r => `<li>${r}</li>`).join('') 
                                : `<li>${result.recommendation}</li>`}
                        </ul>
                    </div>
                </div>
            `;
            
            historyContent.innerHTML += historyItemHtml;
        });
    }
    
    // Initialize
    loadHistory();
});

// Toggle job description expanded view
function toggleJd(id, jobDescription) {
    const jdElement = document.getElementById(id);
    const readMoreBtn = jdElement.nextElementSibling;
    
    if (!jdElement.classList.contains('expanded')) {
        // Nếu đang ở trạng thái thu gọn, hiển thị đầy đủ
        jdElement.innerHTML = `<strong>Job Description:</strong><br>${decodeURIComponent(jobDescription)}`;
        jdElement.classList.add('expanded');
        readMoreBtn.textContent = 'Show less';
    } else {
        // Nếu đang mở rộng, hiển thị lại phiên bản rút gọn
        const shortDesc = decodeURIComponent(jobDescription).substring(0, 200);
        jdElement.innerHTML = `<strong>Job Description:</strong><br>${shortDesc}...`;
        jdElement.classList.remove('expanded');
        readMoreBtn.textContent = 'Read more';
    }
}

// View resume file
function viewResume(filePath) {
    // Hiển thị file trong cửa sổ mới hoặc tab mới
    try {
        // Nếu là file PDF, hiển thị trực tiếp trên trình duyệt
        if (filePath.toLowerCase().endsWith('.pdf')) {
            window.open(`/view_resume?path=${encodeURIComponent(filePath)}`, '_blank');
        } else {
            // Nếu không, tải file xuống
            fetch(`/download_resume?path=${encodeURIComponent(filePath)}`)
                .then(response => {
                    if (response.ok) {
                        return response.blob();
                    }
                    throw new Error('Network response was not ok.');
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filePath.split('/').pop();
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Không thể tải file. Vui lòng thử lại sau.');
                });
        }
    } catch (error) {
        console.error('Error viewing resume:', error);
        alert('Không thể mở file. Vui lòng thử lại sau.');
    }
}
