document.addEventListener('DOMContentLoaded', () => {
    // Store form data
    const formData = {};
    
    // Get DOM elements
    const startButton = document.getElementById('start-button');
    const submitButtons = document.querySelectorAll('.submit-btn');
    
    // Function to show a specific screen
    const showScreen = (screenId) => {
        // Hide all screens
        document.querySelectorAll('.form-screen').forEach(screen => {
            screen.classList.remove('active');
        });
        
        // Show the requested screen
        document.getElementById(screenId).classList.add('active');
        
        // Set focus on the input if present
        const input = document.getElementById(screenId).querySelector('input, textarea');
        if (input) {
            setTimeout(() => input.focus(), 300);
        }
    };
    
    // Start button click handler
    startButton.addEventListener('click', () => {
        showScreen('question-1');
    });
    
    // Submit buttons click handlers
    submitButtons.forEach(button => {
        button.addEventListener('click', () => {
            const questionType = button.getAttribute('data-question');
            let inputValue;
            
            // Get the input value based on question type
            switch (questionType) {
                case 'name':
                    inputValue = document.getElementById('name-input').value.trim();
                    if (!inputValue) {
                        alert('Please enter your name');
                        return;
                    }
                    formData.name = inputValue;
                    showScreen('question-2');
                    break;
                    
                case 'email':
                    inputValue = document.getElementById('email-input').value.trim();
                    if (!validateEmail(inputValue)) {
                        alert('Please enter a valid email address');
                        return;
                    }
                    formData.email = inputValue;
                    showScreen('question-3');
                    break;
                    
                case 'feedback':
                    inputValue = document.getElementById('feedback-input').value.trim();
                    formData.feedback = inputValue || 'No feedback provided';
                    displaySummary();
                    showScreen('thank-you-screen');
                    break;
            }
        });
    });
    
    // Email validation
    const validateEmail = (email) => {
        const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    };
    
    // Display summary of responses
    const displaySummary = () => {
        const summaryContainer = document.getElementById('response-summary');
        
        summaryContainer.innerHTML = `
            <div class="response-item">
                <div class="response-label">Name:</div>
                <div>${formData.name}</div>
            </div>
            <div class="response-item">
                <div class="response-label">Email:</div>
                <div>${formData.email}</div>
            </div>
            <div class="response-item">
                <div class="response-label">Feedback:</div>
                <div>${formData.feedback}</div>
            </div>
        `;
        
        // Here you could also add code to send data to your server
        console.log('Form data collected:', formData);
    };
}); 