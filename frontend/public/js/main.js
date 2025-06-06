document.addEventListener('DOMContentLoaded', function () {
    // Initialize mermaid for diagrams
    mermaid.initialize({ startOnLoad: true, theme: 'neutral' });

    // Variables to store form data
    let formData = {
        domain: '',
        industry: '',
        objective: '',
        reconMethods: [],
        email: ''
    };

    // Define the screen sequence for navigation
    const screenSequence = [
        'welcome-screen',
        'domain-screen',
        'industry-screen',
        'legal-screen',
        'recon-screen',
        'exploit-screen',
        'thank-you-screen'
    ];

    // Get elements
    const startButton = document.getElementById('start-button');
    const submitButtons = document.querySelectorAll('.submit-btn');
    const backButtons = document.querySelectorAll('.back-button');
    const allScreens = document.querySelectorAll('.form-screen');
    const industryItems = document.querySelectorAll('.industry-item');
    const scheduleButton = document.getElementById('schedule-button');

    // Welcome screen button
    startButton.addEventListener('click', function () {
        navigateToScreen('welcome-screen', 'domain-screen');
    });

    // Add event listener for continue button on domain screen
    const continueButton = document.getElementById('continue-button');
    if (continueButton) {
        continueButton.addEventListener('click', function () {
            const domain = document.getElementById('domain-input').value.trim();

            if (!domain) {
                highlightEmptyField('domain-input');
                return;
            }

            // Simple domain validation
            const domainPattern = /^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;
            if (!domainPattern.test(domain)) {
                highlightEmptyField('domain-input');
                alert('Please enter a valid domain (e.g., example.com)');
                return;
            }

            // Store the domain
            formData.domain = domain;

            // Navigate to the industry screen
            navigateToScreen('domain-screen', 'industry-screen');
        });
    }

    // Industry selection
    industryItems.forEach(item => {
        item.addEventListener('click', function () {
            // Toggle selected class
            document.querySelectorAll('.industry-item').forEach(i => {
                i.classList.remove('selected');
            });
            this.classList.add('selected');

            // Store selected industry
            formData.industry = this.getAttribute('data-industry');

            // Focus the first radio button
            const firstRadio = this.querySelector('input[type="radio"]');
            if (firstRadio) {
                firstRadio.focus();
            }
        });
    });

    // Handle back buttons
    backButtons.forEach(button => {
        button.addEventListener('click', function () {
            const prevScreen = this.getAttribute('data-prev');
            if (prevScreen) {
                navigateToScreen(this.closest('.form-screen').id, prevScreen);
            } else {
                const currentScreenId = this.closest('.form-screen').id;
                const currentIndex = screenSequence.indexOf(currentScreenId);

                if (currentIndex > 0) {
                    const previousScreenId = screenSequence[currentIndex - 1];
                    navigateToScreen(currentScreenId, previousScreenId);
                }
            }
        });
    });

    // Handle submit buttons
    submitButtons.forEach(button => {
        button.addEventListener('click', function () {
            const currentScreen = this.closest('.form-screen').id;
            const nextScreen = this.getAttribute('data-next');

            // Validate and store data based on current screen
            if (currentScreen === 'industry-screen') {
                // Check if industry is selected
                if (!formData.industry) {
                    alert('Please select an industry');
                    return;
                }

                // Check if objective is selected
                const selectedObjective = document.querySelector('input[name="objective"]:checked');
                if (!selectedObjective) {
                    alert('Please select a primary objective');
                    return;
                }

                formData.objective = selectedObjective.value;
            }
            else if (currentScreen === 'legal-screen') {
                // Get email
                const emailInput = document.getElementById('contact-email');
                const email = emailInput.value.trim();

                if (!email) {
                    highlightEmptyField('contact-email');
                    return;
                }

                formData.email = email;

                // Get selected recon methods
                formData.reconMethods = [];
                document.querySelectorAll('input[name="recon-methods"]:checked').forEach(checkbox => {
                    formData.reconMethods.push(checkbox.value);
                });

                // If no methods selected, use default
                if (formData.reconMethods.length === 0) {
                    document.getElementById('osint-search').checked = true;
                    formData.reconMethods.push('osint-search');
                }
            }

            // Navigate to next screen
            if (nextScreen) {
                navigateToScreen(currentScreen, nextScreen);

                // If moving to recon screen, render the diagram
                if (nextScreen === 'recon-screen') {
                    setTimeout(() => {
                        mermaid.init(undefined, document.querySelector(".mermaid"));
                    }, 500);
                }
            }
        });
    });

    // Schedule button
    if (scheduleButton) {
        scheduleButton.addEventListener('click', function () {
            // Here you would typically redirect to a scheduling page or open a modal
            alert('Thank you for your interest! A member of our team will contact you shortly to schedule your penetration test.');
        });
    }

    // Navigation function
    function navigateToScreen(currentId, nextId) {
        document.getElementById(currentId).classList.remove('active');
        document.getElementById(nextId).classList.add('active');

        // Auto-focus on input in the next screen if applicable
        const nextInput = document.getElementById(nextId).querySelector('input:not([type="radio"]):not([type="checkbox"])');
        if (nextInput) {
            setTimeout(() => nextInput.focus(), 300);
        }

        // Scroll to top
        window.scrollTo(0, 0);
    }

    // Highlight empty field
    function highlightEmptyField(fieldId) {
        const field = document.getElementById(fieldId);

        if (field) {
            field.style.borderColor = '#e74c3c';
            field.addEventListener('input', function resetBorder() {
                this.style.borderColor = '';
                this.removeEventListener('input', resetBorder);
            });

            field.focus();
        }
    }

    // Handle screen navigation
    document.querySelectorAll('.form-screen').forEach(screen => {
        // Back button handling
        const backBtn = screen.querySelector('.back-button');
        if (backBtn) {
            backBtn.addEventListener('click', () => {
                const prevScreen = backBtn.dataset.prev;
                if (prevScreen) {
                    document.querySelectorAll('.form-screen').forEach(s => s.classList.remove('active'));
                    document.getElementById(prevScreen).classList.add('active');
                }
            });
        }

        // Forward button handling
        const nextBtn = screen.querySelector('.cta-button');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                const nextScreen = nextBtn.dataset.next;
                if (nextScreen) {
                    // Check if we're on the legal screen and validate checkboxes
                    if (screen.id === 'legal-screen') {
                        const checkedMethods = screen.querySelectorAll('input[name="recon-methods"]:checked');
                        if (checkedMethods.length === 0) {
                            alert('Please select at least one reconnaissance method.');
                            return;
                        }
                    }

                    document.querySelectorAll('.form-screen').forEach(s => s.classList.remove('active'));
                    document.getElementById(nextScreen).classList.add('active');
                }
            });
        }
    });

    // Update stats when reaching the thank you screen
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.target.classList.contains('active') &&
                mutation.target.id === 'thank-you-screen') {
                updateClickStats();
            }
        });
    });

    const thankYouScreen = document.getElementById('thank-you-screen');
    if (thankYouScreen) {
        observer.observe(thankYouScreen, {
            attributes: true,
            attributeFilter: ['class']
        });
    }

    // Update stats every 30 seconds if thank you screen is visible
    setInterval(() => {
        const thankYouScreen = document.getElementById('thank-you-screen');
        if (thankYouScreen && thankYouScreen.classList.contains('active')) {
            updateClickStats();
        }
    }, 30000);
});

async function updateClickStats() {
    try {
        // Update the URL to point to our backend API
        const response = await fetch('http://localhost:8000/api/click-stats');
        const stats = await response.json();

        // Update total clicks
        document.getElementById('total-clicks').textContent = stats.total_clicks;
        document.getElementById('unique-users').textContent = stats.unique_users;

        // Update user clicks table
        const userClicksTable = document.getElementById('user-clicks-table');
        userClicksTable.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Company</th>
                        <th>Clicks</th>
                        <th>First Click</th>
                        <th>Last Click</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(stats.user_stats || {}).map(([email, data]) => `
                        <tr>
                            <td>${email}</td>
                            <td>${data.company}</td>
                            <td class="click-count">${data.count}</td>
                            <td class="timestamp">${new Date(data.first_click).toLocaleString()}</td>
                            <td class="timestamp">${new Date(data.last_click).toLocaleString()}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        // Update recent clicks list
        const clicksList = document.getElementById('clicks-list');
        clicksList.innerHTML = (stats.recent_clicks || [])
            .map(click => `
                <div class="click-item">
                    <div class="click-time">
                        ${new Date(click.timestamp).toLocaleString()}
                    </div>
                    <div>User: ${click.email}</div>
                    <div>Company: ${click.company}</div>
                </div>
            `)
            .join('');

    } catch (error) {
        console.error('Failed to fetch click statistics:', error);
    }
} 