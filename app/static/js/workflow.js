// Workflow management JavaScript for Agents_Q
document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const workflowContainer = document.querySelector('.workflow-container'); // Get main container
    const workflowForm = document.getElementById('workflow-form');
    const userInput = document.getElementById('user-input');
    let sessionId = document.getElementById('session-id').value;
    const sessionIdInput = document.getElementById('session-id');
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

    // UI State definition
    const UI_STATES = {
        INITIAL: 'INITIAL',
        CREATING_PLAN: 'CREATING_PLAN',
        PLAN_DISPLAYED: 'PLAN_DISPLAYED',
        AWAITING_FEEDBACK: 'AWAITING_FEEDBACK',
        REFINING_PLAN: 'REFINING_PLAN',
        ANALYZING: 'ANALYZING',
        EXECUTING: 'EXECUTING',
        COMPLETED: 'COMPLETED',
        ERROR: 'ERROR' // Optional: For showing a general error state
    };

    // Connect to Socket.IO
    const socket = io();

    // Function to set the UI state and update status text
    function setUIState(newState) {
        workflowContainer.dataset.uiState = newState;
        console.log(`UI State changed to: ${newState}`);
        
        // Update status text based on state
        switch (newState) {
            case UI_STATES.INITIAL:
                setStatus('ready', 'Ready');
                break;
            case UI_STATES.CREATING_PLAN:
                setStatus('thinking', 'Creating plan...');
                break;
            case UI_STATES.PLAN_DISPLAYED:
                setStatus('ready', 'Plan created');
                break;
             case UI_STATES.AWAITING_FEEDBACK:
                 setStatus('ready', 'Plan ready. Accept or provide feedback.');
                 feedbackInput.value = ''; // Clear feedback input
                 feedbackInput.disabled = false;
                 submitFeedbackBtn.disabled = false;
                 feedbackInput.focus();
                 break;
            case UI_STATES.REFINING_PLAN:
                setStatus('thinking', 'Refining plan...');
                break;
            case UI_STATES.ANALYZING:
                setStatus('thinking', 'Analyzing plan...');
                break;
            case UI_STATES.EXECUTING:
                initializeWorkflowProgressView();
                setStatus('thinking', 'Executing plan...');
                break;
            case UI_STATES.COMPLETED:
                setStatus('ready', 'Workflow completed');
                break;
            case UI_STATES.ERROR:
                // Assuming status is already set by the error handler
                break;
            default:
                setStatus('ready', 'Ready');
        }
    }

    // Socket.IO event handlers
    socket.on('connect', function() {
        // If session ID exists from a previous state, might want to fetch status?
        // For now, just set initial state if it's not already set by HTML
        if (!workflowContainer.dataset.uiState) {
             setUIState(UI_STATES.INITIAL);
        }
        setStatus('ready', 'Connected to server'); // Keep simple status update
    });

    socket.on('disconnect', function() {
        setStatus('error', 'Disconnected from server');
    });

    socket.on('status', function(data) {
        // This seems like a basic connection status message, less relevant now
        // setStatus('ready', data.message);
    });

    socket.on('plan_created', function(data) {
        sessionId = data.session_id;
        if (sessionIdInput) {
            sessionIdInput.value = sessionId;
        }
        
        displayPlan(data.plan); // Populate the plan details
        setUIState(UI_STATES.PLAN_DISPLAYED); // Set the UI state to show the plan
        
        // Hide feedback form initially when a new plan is created
        // User clicks 'Revise Plan' to show it
    });

    socket.on('plan_accepted', function(data) {
        console.log('Received plan_accepted event:', data);
        if (data.session_id === sessionId) {
            console.log('Session ID matches. Setting UI state to EXECUTING.');
            setUIState(UI_STATES.EXECUTING);
            // initializeWorkflowProgressView() is called inside setUIState
        } else {
            console.warn('Received plan_accepted event for wrong session ID:', data.session_id, 'Expected:', sessionId);
        }
    });

    socket.on('workflow_update', function(data) {
        console.log('Received workflow_update event:', data);
        if (data.session_id === sessionId) {
            // Ensure we are in the executing state before trying to update progress
            if (workflowContainer.dataset.uiState === UI_STATES.EXECUTING) {
                console.log('Session ID matches. Calling addProgressUpdate():', data.message);
                addProgressUpdate(data.message);
            } else {
                 console.warn('Received workflow_update while not in EXECUTING state.');
            }
        } else {
            console.warn('Received workflow_update event for wrong session ID:', data.session_id, 'Expected:', sessionId);
        }
    });

    socket.on('workflow_completed', function(data) {
        console.log('Received workflow_completed event:', data);
        if (data.session_id === sessionId) {
            console.log('Session ID matches. Setting UI state to COMPLETED.');
            showWorkflowResult(data.result);
            setUIState(UI_STATES.COMPLETED);
        } else {
            console.warn('Received workflow_completed event for wrong session ID:', data.session_id, 'Expected:', sessionId);
        }
    });

    socket.on('plan_analysis', function(data) {
        if (data.session_id === sessionId) {
            showPlanAnalysis(data.analysis);
            // Assuming analysis stays visible until plan is accepted/recreated
            // Status is set within showPlanAnalysis for now
            setStatus('ready', 'Plan analysis complete');
            // We remain in the ANALYZING state visually via CSS
        }
    });

    socket.on('error', function(data) {
        setStatus('error', data.message);
        // Optionally, set a general ERROR state if needed
        // setUIState(UI_STATES.ERROR);
        // Show error message somewhere more prominently?
        addProgressUpdate('Error: ' + data.message); // Add to progress log for now
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
        setUIState(UI_STATES.CREATING_PLAN);
        
        // Send message to server
        socket.emit('create_plan', {
            message: message,
            session_id: sessionId
        });
    });

    // Accept plan button
    acceptPlanBtn.addEventListener('click', function() {
        console.log('Accept Plan button clicked. Emitting accept_plan event for session:', sessionId);
        // Don't change state here, wait for server confirmation via 'plan_accepted' event
        socket.emit('accept_plan', {
            session_id: sessionId
        });
    });

    // Revise plan button
    revisePlanBtn.addEventListener('click', function() {
        setUIState(UI_STATES.AWAITING_FEEDBACK);
        // The state change handles showing the feedback form via CSS
    });

    // Analyze plan button
    if (analyzePlanBtn) {
        analyzePlanBtn.addEventListener('click', function() {
            setUIState(UI_STATES.ANALYZING);
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
            
            setUIState(UI_STATES.REFINING_PLAN);
            
            // Send feedback to server
            socket.emit('refine_plan', {
                session_id: sessionId,
                feedback: feedback
            });
            
            // UI will update when 'plan_created' is received with the refined plan
        });
    }

    // Function to display the plan
    function displayPlan(plan) {
        // Plan display visibility is now handled by CSS based on state
        
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
        
        // Hide any previous analysis (now handled by CSS state)
    }

    // Function to initialize the workflow progress view
    function initializeWorkflowProgressView() {
        console.log('Inside initializeWorkflowProgressView()');
        // Visibility is handled by CSS based on state
        
        if (!progressUpdates || !currentStep) {
            console.error('initializeWorkflowProgressView: progressUpdates or currentStep element not found!');
            return;
        }
        progressUpdates.innerHTML = ''; // Clear old updates
        currentStep.textContent = 'Initializing workflow...'; // Set initial step text
        progressBar.style.width = '0%'; // Reset progress bar
        progressBar.removeAttribute('data-total'); // Clear total steps
        console.log('initializeWorkflowProgressView() finished.');
    }

    // Function to add a progress update
    function addProgressUpdate(message) {
        console.log('Inside addProgressUpdate() with message:', message);

        // --- Add explicit check for element validity --- 
        if (!progressUpdates || !document.body.contains(progressUpdates)) {
             console.error('progressUpdates element not found or not in DOM when addProgressUpdate called!');
             return;
        }
         if (!currentStep || !document.body.contains(currentStep)) {
             console.error('currentStep element not found or not in DOM when addProgressUpdate called!');
             return;
        }
        if (!progressBar || !document.body.contains(progressBar)) { // Also check progressBar
             console.error('progressBar element not found or not in DOM when addProgressUpdate called!');
             // Decide if we should return or just skip progress bar update
             // For now, let's just log and continue if possible
        }
        // --- End check ---

        // If the checks above passed, proceed with DOM manipulation
        const updateElement = document.createElement('div');
        updateElement.className = 'progress-update';
        updateElement.textContent = message;
        progressUpdates.appendChild(updateElement);
        // --- Force reflow diagnostic ---
        // updateElement.offsetHeight; // Reading offsetHeight can trigger reflow  << REVERTED
        // --- End diagnostic ---
        progressUpdates.scrollTop = progressUpdates.scrollHeight;
        
        // Update current step text
        if (message.startsWith('Starting step')) {
            currentStep.textContent = message;
            // --- Force reflow diagnostic ---
            // currentStep.offsetHeight; // Reading offsetHeight can trigger reflow << REVERTED
            // --- End diagnostic ---
            
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
        console.log('Inside showWorkflowResult.');
        // Visibility is handled by CSS based on state
        resultContent.innerHTML = result.replace(/\n/g, '<br>');
    }

    // Function to show plan analysis
    function showPlanAnalysis(analysis) {
        // Visibility is handled by CSS based on state
        if (analysisContent) {
            analysisContent.innerHTML = analysis.replace(/\n/g, '<br>');
            // Status update is now handled in setUIState or the event handler
        }
    }

    // Function to set status indicator and text separately
    function setStatus(state, text) {
        statusIndicator.className = 'status-indicator'; // Reset classes
        if (state !== 'ready') {
            statusIndicator.classList.add(state);
        }
        statusText.textContent = text;
    }

    // Initial UI state setup on load
    setUIState(workflowContainer.dataset.uiState || UI_STATES.INITIAL);
});
