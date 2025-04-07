// Workflow management JavaScript for Agents_Q
document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const workflowForm = document.getElementById('workflow-form');
    const userInput = document.getElementById('user-input');
    const sessionId = document.getElementById('session-id').value;
    const createPlanBtn = document.getElementById('create-plan-btn');
    const planDisplay = document.getElementById('plan-display');
    const planSummary = document.getElementById('plan-summary');
    const planSteps = document.getElementById('plan-steps');
    const acceptPlanBtn = document.getElementById('accept-plan-btn');
    const revisePlanBtn = document.getElementById('revise-plan-btn');
    const analyzePlanBtn = document.getElementById('analyze-plan-btn');
    const workflowProgress = document.getElementById('workflow-progress');
    const progressBar = document.getElementById('progress-bar');
    const currentStep = document.getElementById('current-step');
    const progressUpdates = document.getElementById('progress-updates');
    const workflowResult = document.getElementById('workflow-result');
    const resultContent = document.getElementById('result-content');
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.status span');
    const feedbackForm = document.getElementById('feedback-form');
    const feedbackInput = document.getElementById('feedback-input');
    const submitFeedbackBtn = document.getElementById('submit-feedback-btn');
    const planAnalysis = document.getElementById('plan-analysis');
    const analysisContent = document.getElementById('analysis-content');

    // Connect to Socket.IO
    const socket = io();

    // Socket.IO event handlers
    socket.on('connect', function() {
        setStatus('ready', 'Connected to server');
    });

    socket.on('disconnect', function() {
        setStatus('error', 'Disconnected from server');
    });

    socket.on('status', function(data) {
        setStatus('ready', data.message);
    });

    socket.on('plan_created', function(data) {
        if (data.session_id === sessionId) {
            displayPlan(data.plan);
            setStatus('ready', 'Plan created');
            
            // Show feedback form
            if (feedbackForm) {
                feedbackForm.classList.remove('hidden');
            }
        }
    });

    socket.on('plan_accepted', function(data) {
        if (data.session_id === sessionId) {
            showWorkflowProgress();
            setStatus('thinking', 'Executing plan...');
            
            // Hide feedback form
            if (feedbackForm) {
                feedbackForm.classList.add('hidden');
            }
        }
    });

    socket.on('workflow_update', function(data) {
        if (data.session_id === sessionId) {
            addProgressUpdate(data.message);
        }
    });

    socket.on('workflow_completed', function(data) {
        if (data.session_id === sessionId) {
            showWorkflowResult(data.result);
            setStatus('ready', 'Workflow completed');
        }
    });

    socket.on('plan_analysis', function(data) {
        if (data.session_id === sessionId) {
            showPlanAnalysis(data.analysis);
        }
    });

    socket.on('error', function(data) {
        setStatus('error', data.message);
        addProgressUpdate('Error: ' + data.message);
    });

    // Form submission
    workflowForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = userInput.value.trim();
        if (!message) return;
        
        // Disable form while processing
        userInput.disabled = true;
        createPlanBtn.disabled = true;
        
        // Set status to thinking
        setStatus('thinking', 'Creating plan...');
        
        // Send message to server
        socket.emit('create_plan', {
            message: message,
            session_id: sessionId
        });
    });

    // Accept plan button
    acceptPlanBtn.addEventListener('click', function() {
        socket.emit('accept_plan', {
            session_id: sessionId
        });
    });

    // Revise plan button
    revisePlanBtn.addEventListener('click', function() {
        if (feedbackForm) {
            feedbackForm.classList.remove('hidden');
            feedbackInput.focus();
        } else {
            planDisplay.classList.add('hidden');
            userInput.disabled = false;
            createPlanBtn.disabled = false;
            userInput.focus();
        }
    });

    // Analyze plan button
    if (analyzePlanBtn) {
        analyzePlanBtn.addEventListener('click', function() {
            setStatus('thinking', 'Analyzing plan...');
            socket.emit('analyze_plan', {
                session_id: sessionId
            });
        });
    }

    // Submit feedback button
    if (submitFeedbackBtn && feedbackForm) {
        feedbackForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const feedback = feedbackInput.value.trim();
            if (!feedback) return;
            
            // Disable form while processing
            feedbackInput.disabled = true;
            submitFeedbackBtn.disabled = true;
            
            // Set status to thinking
            setStatus('thinking', 'Refining plan...');
            
            // Send feedback to server
            socket.emit('refine_plan', {
                session_id: sessionId,
                feedback: feedback
            });
            
            // Hide feedback form
            feedbackForm.classList.add('hidden');
        });
    }

    // Function to display the plan
    function displayPlan(plan) {
        // Show the plan display
        planDisplay.classList.remove('hidden');
        
        // Display the summary
        planSummary.textContent = plan.summary;
        
        // Display the steps
        planSteps.innerHTML = '';
        plan.steps.forEach((step, index) => {
            const stepElement = document.createElement('div');
            stepElement.className = 'plan-step';
            stepElement.innerHTML = `
                <div class="step-number">${index + 1}</div>
                <div class="step-content">
                    <h3>${step.title}</h3>
                    <p>${step.description}</p>
                </div>
            `;
            planSteps.appendChild(stepElement);
        });
        
        // Enable the accept and revise buttons
        acceptPlanBtn.disabled = false;
        revisePlanBtn.disabled = false;
        if (analyzePlanBtn) {
            analyzePlanBtn.disabled = false;
        }
        
        // Hide any previous analysis
        if (planAnalysis) {
            planAnalysis.classList.add('hidden');
        }
    }

    // Function to show workflow progress
    function showWorkflowProgress() {
        planDisplay.classList.add('hidden');
        if (feedbackForm) {
            feedbackForm.classList.add('hidden');
        }
        if (planAnalysis) {
            planAnalysis.classList.add('hidden');
        }
        workflowProgress.classList.remove('hidden');
        progressUpdates.innerHTML = '';
        currentStep.textContent = 'Initializing workflow...';
    }

    // Function to add a progress update
    function addProgressUpdate(message) {
        const updateElement = document.createElement('div');
        updateElement.className = 'progress-update';
        updateElement.textContent = message;
        progressUpdates.appendChild(updateElement);
        progressUpdates.scrollTop = progressUpdates.scrollHeight;
        
        // Update current step text
        if (message.startsWith('Starting step')) {
            currentStep.textContent = message;
            
            // Extract step number and total steps
            const match = message.match(/Starting step (\d+)\/(\d+)/);
            if (match) {
                const current = parseInt(match[1]);
                const total = parseInt(match[2]);
                progressBar.setAttribute('data-total', total);
                const percentage = (current - 1) / total * 100;
                progressBar.style.width = `${percentage}%`;
            }
        } else if (message.startsWith('Completed step')) {
            const match = message.match(/Completed step (\d+)/);
            if (match) {
                const current = parseInt(match[1]);
                const total = parseInt(progressBar.getAttribute('data-total') || '1');
                const percentage = current / total * 100;
                progressBar.style.width = `${percentage}%`;
            }
        } else if (message === 'Workflow completed successfully!') {
            progressBar.style.width = '100%';
        }
    }

    // Function to show workflow result
    function showWorkflowResult(result) {
        workflowResult.classList.remove('hidden');
        resultContent.innerHTML = result.replace(/\n/g, '<br>');
    }

    // Function to show plan analysis
    function showPlanAnalysis(analysis) {
        if (planAnalysis && analysisContent) {
            planAnalysis.classList.remove('hidden');
            analysisContent.innerHTML = analysis.replace(/\n/g, '<br>');
            setStatus('ready', 'Plan analysis complete');
        }
    }

    // Function to set status
    function setStatus(state, text) {
        statusIndicator.className = 'status-indicator';
        if (state !== 'ready') {
            statusIndicator.classList.add(state);
        }
        statusText.textContent = text;
    }
});
