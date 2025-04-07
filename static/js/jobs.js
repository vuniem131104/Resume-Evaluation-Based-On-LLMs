document.addEventListener('DOMContentLoaded', async function () {
    const username = localStorage.getItem('username');
    const jobList = document.getElementById('job-list');


    async function get_jobs() {
        try {
            const response = await fetch('/get_related_jobs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username: username })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            const jobUrl = `get_related_jobs_result/${data.job_id}`;
            renderJobs(jobUrl);
        } catch (error) {
            console.error('Error:', error);
            const loadingContainer = document.getElementById('loading-animation');
            loadingContainer.innerHTML = `
                <i class="fas fa-exclamation-circle" style="font-size: 3rem; color: #e74c3c; margin-bottom: 1rem;"></i>
                <p>An error occurred while fetching jobs: ${error.message}</p>
            `;
        }
    }

    function renderJobs(url) {
        let tries = 0;
        const maxTries = 30;
        const interval = setInterval(async () => {
            const res = await fetch(url);
            const results = await res.json();
            const status = results.status;
            const jobs = results.result;
            if (status === 'completed') {
                const loadingAnimation = document.getElementById('loading-animation');
                jobList.innerHTML = '';
                jobList.appendChild(loadingAnimation);

                jobs.forEach(job => {
                    const jobCard = document.createElement('div');
                    jobCard.className = 'job-card';

                    jobCard.innerHTML = `
                <div class="job-header">
                    <div>
                    <h2 class="job-title">${job.title}</h2>
                    <p class="job-company">${job.company}</p>
                    </div>
                    <button class="save-job" title="Save job">
                    <i class="far fa-bookmark"></i>
                    </button>
                </div>
                <p class="job-location">
                    <i class="fas fa-map-marker-alt"></i> ${job.location}
                </p>
                <p class="job-description">${job.description}</p>
                <div class="job-footer">
                    <a href="${job.link}" class="job-link" target="_blank">
                    Apply Now <i class="fas fa-external-link-alt"></i>
                    </a>
                    <p class="job-date">${job.datePosted}</p>
                </div>
                `;

                    jobList.appendChild(jobCard);
                });

                jobList.classList.add('loaded');

                document.querySelectorAll('.save-job').forEach(button => {
                    button.addEventListener('click', function (e) {
                        e.stopPropagation();
                        this.classList.toggle('saved');

                        if (this.classList.contains('saved')) {
                            this.innerHTML = '<i class="fas fa-bookmark"></i>';
                        } else {
                            this.innerHTML = '<i class="far fa-bookmark"></i>';
                        }
                    });
                });

                document.querySelectorAll('.job-card').forEach((card, index) => {
                    card.addEventListener('click', function () {
                        window.open(jobsToRender[ index ].link, '_blank');
                    });
                });
                clearInterval(interval);
            } else if (++tries >= maxTries) {
                alert('Evaluation is taking longer than expected. Please try again later.');
                clearInterval(interval);
            }
        }, 3000);
    }


    const filterButtons = document.querySelectorAll('.filter-btn');

    get_jobs();

    filterButtons.forEach(button => {
        button.addEventListener('click', function () {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            const filter = this.textContent.toLowerCase();

            let filteredJobs;

            if (filter === 'all') {
                filteredJobs = jobs;
            } else if (filter === 'last 7 days') {
                filteredJobs = jobs.filter(job => {
                    const days = parseInt(job.datePosted);
                    return days <= 7;
                });
            } else {
                filteredJobs = jobs.filter(job =>
                    job.title.toLowerCase().includes(filter) ||
                    job.description.toLowerCase().includes(filter)
                );
            }

            renderJobs(filteredJobs);
        });
    });

    const searchBar = document.querySelector('.search-bar input');
    const searchButton = document.querySelector('.search-bar button');

    function performSearch() {
        const searchTerm = searchBar.value.toLowerCase().trim();

        if (searchTerm === '') {
            renderJobs(jobs);
            return;
        }

        const searchResults = jobs.filter(job =>
            job.title.toLowerCase().includes(searchTerm) ||
            job.company.toLowerCase().includes(searchTerm) ||
            job.description.toLowerCase().includes(searchTerm)
        );

        renderJobs(searchResults);
    }

    searchButton.addEventListener('click', performSearch);
    searchBar.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
});