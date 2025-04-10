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

        const workflowResultDiv = document.getElementById('workflow-result');
        const artifactsDisplayDiv = document.getElementById('artifacts-display');
        const workflowProgressDiv = document.getElementById('workflow-progress'); // Get progress div

        // Hide progress by default, show in specific states
        if (workflowProgressDiv) workflowProgressDiv.style.display = 'none';

        switch (newState) {
            case UI_STATES.INITIAL:
                setStatus('ready', 'Ready');
                if(workflowResultDiv) workflowResultDiv.style.display = 'none';
                if(artifactsDisplayDiv) artifactsDisplayDiv.style.display = 'none';
                break;
            case UI_STATES.CREATING_PLAN:
                setStatus('thinking', 'Creating plan...');
                if(workflowResultDiv) workflowResultDiv.style.display = 'none';
                if(artifactsDisplayDiv) artifactsDisplayDiv.style.display = 'none';
                break;
            case UI_STATES.PLAN_DISPLAYED:
                setStatus('ready', 'Plan created');
                if(workflowResultDiv) workflowResultDiv.style.display = 'none';
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
                initializeWorkflowProgressView(); // Might make progress visible
                if (workflowProgressDiv) workflowProgressDiv.style.display = 'block'; // Ensure progress is visible
                setStatus('thinking', 'Executing plan...');
                if(workflowResultDiv) workflowResultDiv.style.display = 'none';
                break;
            case UI_STATES.COMPLETED:
                setStatus('ready', 'Workflow completed');
                // Let showWorkflowResult and file_artifact_update handler manage visibility
                // No explicit show/hide here for result/artifact divs
                // We might want to explicitly hide the progress view if it was shown
                if (workflowProgressDiv) workflowProgressDiv.style.display = 'none';
                
                // ADDITIONAL FIX: Explicitly show artifact container in COMPLETED state
                const artifactsDisplay = document.getElementById('artifacts-display');
                if (artifactsDisplay) {
                    console.log('COMPLETED state: Explicitly setting artifacts-display to visible');
                    artifactsDisplay.style.display = 'block';
                    
                    // Automatically trigger the scan button after a short delay
                    setTimeout(() => {
                        console.log('Auto-triggering artifact scan after workflow completion');
                        const scanButton = document.getElementById('scan-artifacts-btn');
                        if (scanButton) {
                            scanButton.click(); // Programmatically click the scan button
                        }
                    }, 500); // Short delay to ensure everything is ready
                }
                break;
            case UI_STATES.ERROR:
                setStatus('error', statusText.textContent || 'An error occurred'); // Keep last error message if possible
                // Hide progress on error
                if (workflowProgressDiv) workflowProgressDiv.style.display = 'none';
                break;
            default:
                setStatus('ready', 'Ready');
                if(workflowResultDiv) workflowResultDiv.style.display = 'none';
                if(artifactsDisplayDiv) artifactsDisplayDiv.style.display = 'none';
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
            if (!progressUpdates) {
                console.error('progressUpdates element not found');
            } else {
                // Add an item for this update
                const div = document.createElement('div');
                div.textContent = data.message;
                progressUpdates.appendChild(div);
                
                // Auto-scroll progress updates
                progressUpdates.scrollTop = progressUpdates.scrollHeight;
            }

            if (data.state && data.state.status) {
                console.log('State update received:', data.state);
                
                // Update the overall status
                const statusDisplay = document.getElementById('workflow-status-display'); 
                if (statusDisplay) {
                    statusDisplay.textContent = `Overall Status: ${data.state.status}`;
                }
                
                // Update statuses of individual steps
                if (data.state.step_statuses && window.stepStatusElements) {
                    for (const [stepId, status] of Object.entries(data.state.step_statuses)) {
                        const statusElement = window.stepStatusElements[stepId];
                        if (statusElement) {
                            // Remove all status classes first
                            statusElement.classList.remove('status-pending', 'status-running', 'status-completed', 'status-failed', 'status-skipped');
                            // Add the appropriate class
                            statusElement.classList.add(`status-${status.toLowerCase()}`);
                            statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
                        }
                    }
                }
                
                // If status is COMPLETED, show the result
                if (data.state.status.toUpperCase() === 'COMPLETED' || data.state.status.toUpperCase() === 'FAILED') {
                    // Show workflow result
                    if (data.state.final_result) {
                        showWorkflowResult(data.state.final_result);
                        
                        // Make sure to change UI state to COMPLETED
                        setUIState(UI_STATES.COMPLETED);
                        
                        // Ensure artifacts container is visible
                        const artifactsDisplay = document.getElementById('artifacts-display');
                        if (artifactsDisplay) {
                            console.log('Setting artifacts-display to visible on workflow completion');
                            artifactsDisplay.style.display = 'block';
                            
                            // Automatically trigger the scan button after a short delay
                            setTimeout(() => {
                                console.log('Auto-triggering artifact scan after workflow completion');
                                const scanButton = document.getElementById('scan-artifacts-btn');
                                if (scanButton) {
                                    scanButton.click(); // Programmatically click the scan button
                                }
                            }, 500); // Short delay to ensure everything is ready
                        }
                    }
                }
            }

        } else {
            console.warn('Received workflow_update event for wrong session ID:', data.session_id, 'Expected:', sessionId);
        }
    });

    socket.on('file_artifact_update', function(data) {
        console.log('Received file_artifact_update event:', data);
        if (data.session_id === sessionId) {
            const artifactsDisplay = document.getElementById('artifacts-display');
            if (!artifactsDisplay) {
                console.error('artifacts-display element not found in DOM');
                return;
            }

            const filename = data.filename;
            const fileContent = data.file_content;
            console.log(`Processing artifact: ${filename} with ${fileContent.length} characters of content`);
            
            // Create a safe ID for the element
            const artifactId = `artifact-${filename.replace(/[^a-zA-Z0-9_\-\.]/g, '-')}`;

            let artifactItem = artifactsDisplay.querySelector(`#${artifactId}`);

            if (artifactItem) {
                // Update existing artifact
                const preElement = artifactItem.querySelector('.artifact-content pre');
                if (preElement) {
                    preElement.textContent = fileContent;
                    console.log(`Updated artifact content for: ${filename}`);
                } else {
                     console.error(`Could not find content element for existing artifact: ${filename}`);
                }
            } else {
                // Create new artifact element
                console.log(`Creating new artifact display for: ${filename}`);
                artifactItem = document.createElement('div');
                artifactItem.className = 'artifact-item';
                artifactItem.id = artifactId;

                const filenameHeader = document.createElement('div');
                filenameHeader.className = 'artifact-filename';
                filenameHeader.textContent = filename;

                const contentDiv = document.createElement('div');
                contentDiv.className = 'artifact-content';
                const preElement = document.createElement('pre');
                preElement.textContent = fileContent;
                contentDiv.appendChild(preElement);

                artifactItem.appendChild(filenameHeader);
                artifactItem.appendChild(contentDiv);

                artifactsDisplay.appendChild(artifactItem);
                console.log(`Artifact element for ${filename} added to DOM`);
            }

            // Always explicitly make the artifacts container visible
            artifactsDisplay.style.display = 'block';
            console.log(`Set artifacts-display container to visible`);
            
            // Force layout refresh
            setTimeout(() => {
                console.log('Forcing layout refresh for artifacts display');
                artifactsDisplay.style.display = 'none';
                artifactsDisplay.offsetHeight; // Force reflow
                artifactsDisplay.style.display = 'block';
            }, 100);
        } else {
            console.warn('Received file_artifact_update event for wrong session ID:', data.session_id, 'Expected:', sessionId);
        }
    });
    
    // Handle artifact_post_update event to ensure UI refresh
    socket.on('artifact_post_update', function(data) {
        console.log('Received artifact_post_update event:', data);
        if (data.session_id === sessionId) {
            // Get the artifacts container and ensure it's visible
            const artifactsDisplay = document.getElementById('artifacts-display');
            if (artifactsDisplay) {
                console.log('Ensuring artifacts-display is visible after post-update');
                artifactsDisplay.style.display = 'block';
                
                // If in COMPLETED state, make sure UI reflects this
                if (workflowContainer.dataset.uiState === UI_STATES.COMPLETED) {
                    console.log('In COMPLETED state, ensuring all relevant elements are visible');
                    const workflowResultDiv = document.getElementById('workflow-result');
                    if (workflowResultDiv) workflowResultDiv.style.display = 'block';
                }
            }
        }
    });

    socket.on('plan_analysis', function(data) {
        if (data.session_id === sessionId) {
            // Analysis data is now a structured dictionary
            showPlanAnalysis(data.analysis);
            setStatus('ready', 'Plan analysis complete');
            // Remain visually in ANALYZING state via CSS until user acts
            setUIState(UI_STATES.ANALYZING);
        }
    });

    socket.on('error', function(data) {
        setStatus('error', data.message);
        // Optionally, set a general ERROR state if needed
        // setUIState(UI_STATES.ERROR);
        // Show error message somewhere more prominently?
        addProgressUpdate('Error: ' + data.message); // Add to progress log for now
    });

    socket.on('artifacts_check_complete', function(data) {
        console.log('Artifacts check complete:', data);
        if (data.session_id === sessionId) {
            const artifactsDisplay = document.getElementById('artifacts-display');
            if (artifactsDisplay) {
                // Remove any loading messages
                const loadingMessage = document.getElementById('artifact-loading-message');
                if (loadingMessage) {
                    loadingMessage.remove();
                }
                
                // If no artifacts were found but the workflow completed, check if we can
                // parse the file name from the final result and request it directly
                if (data.artifact_count === 0 && workflowContainer.dataset.uiState === UI_STATES.COMPLETED) {
                    console.log('No artifacts found but workflow completed. Checking final result for filenames.');
                    
                    // Get the final result text
                    const resultContent = document.getElementById('result-content');
                    if (resultContent && resultContent.textContent) {
                        const finalResultText = resultContent.textContent;
                        console.log('Checking final result text:', finalResultText.substring(0, 100));
                        
                        // Try to find filename in text
                        const filePatterns = [
                            /file:?\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)/i,
                            /in\s+the\s+file\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)/i,
                            /find\s+it\s+in\s+the\s+file\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)/i,
                            /access\s+it\s+in\s+the\s+file\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)/i,
                            /titled\s+"([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)"/i
                        ];
                        
                        let filenameFound = false;
                        for (const pattern of filePatterns) {
                            const match = finalResultText.match(pattern);
                            if (match && match[1]) {
                                filenameFound = true;
                                const filename = match[1];
                                console.log('Found filename in result:', filename);
                                
                                // Show a message that we're searching for the file
                                const loadingMessage = document.createElement('div');
                                loadingMessage.className = 'artifact-item loading-message';
                                loadingMessage.innerHTML = `<p>Searching for file: ${filename}...</p>`;
                                artifactsDisplay.appendChild(loadingMessage);
                                
                                // Show the artifacts container
                                artifactsDisplay.style.display = 'block';
                                
                                // We'll request the server to check for this file specifically
                                socket.emit('request_specific_file', {
                                    session_id: sessionId,
                                    filename: filename
                                });
                                break;
                            }
                        }
                        
                        // If no filename was found in the text, show a message
                        if (!filenameFound) {
                            console.log('No filename found in result text');
                            const noFilesMessage = document.createElement('div');
                            noFilesMessage.className = 'artifact-item no-files-message';
                            noFilesMessage.innerHTML = `<p>No artifact files were found for this workflow.</p>`;
                            artifactsDisplay.appendChild(noFilesMessage);
                            artifactsDisplay.style.display = 'block';
                        }
                    }
                } else if (data.artifact_count === 0) {
                    // Show "no artifacts" message if none were found
                    if (artifactsDisplay.children.length <= 1) { // Only heading exists
                        const noFilesMessage = document.createElement('div');
                        noFilesMessage.className = 'artifact-item no-files-message';
                        noFilesMessage.innerHTML = `<p>No artifact files were found for this workflow.</p>`;
                        artifactsDisplay.appendChild(noFilesMessage);
                    }
                }
                
                // Always ensure the container is visible
                artifactsDisplay.style.display = 'block';
            }
        }
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

    // Scan for artifacts button
    const scanArtifactsBtn = document.getElementById('scan-artifacts-btn');
    if (scanArtifactsBtn) {
        scanArtifactsBtn.addEventListener('click', function() {
            console.log('Manually scanning for artifacts with session ID:', sessionId);
            
            // Clear any "no artifacts" messages
            const artifactsDisplay = document.getElementById('artifacts-display');
            if (artifactsDisplay) {
                // Remove any no-files-message elements
                const noFilesMessages = artifactsDisplay.querySelectorAll('.no-files-message');
                noFilesMessages.forEach(el => el.remove());
                
                // Clear any existing artifact items to prevent duplicates
                const existingArtifacts = artifactsDisplay.querySelectorAll('.artifact-item:not(.loading-message)');
                existingArtifacts.forEach(el => el.remove());
                
                // Add a loading message
                const loadingMessage = document.createElement('div');
                loadingMessage.className = 'artifact-item loading-message';
                loadingMessage.id = 'artifact-loading-message';
                loadingMessage.innerHTML = `<p>Searching for artifacts from your current workflow...</p>`;
                artifactsDisplay.appendChild(loadingMessage);
                
                // Show the artifacts container
                artifactsDisplay.style.display = 'block';
            }
            
            // Get the final result text to extract the specific filename
            const resultContent = document.getElementById('result-content');
            if (resultContent && resultContent.textContent) {
                const finalResultText = resultContent.textContent;
                
                // Try to find filename in text using various patterns
                const filePatterns = [
                    /file:?\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)/i,
                    /in\s+the\s+file\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)/i,
                    /find\s+it\s+in\s+the\s+file\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)/i,
                    /access\s+it\s+in\s+the\s+file\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)/i,
                    /titled\s+"([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)"/i,
                    /file\s+([a-zA-Z0-9_\-.]+\.[a-zA-Z0-9]+)/i,
                    /titled\s+["']([^"']+)["']/i,  // Match names in quotes
                    /poem\s+titled\s+["']([^"']+)["']/i,
                    /\.txt/i  // If .txt extension is mentioned anywhere
                ];
                
                let foundSpecificFile = false;
                
                // First try to find a specific filename in the result text
                for (const pattern of filePatterns) {
                    const match = finalResultText.match(pattern);
                    if (match && match[1]) {
                        foundSpecificFile = true;
                        const filename = match[1];
                        console.log('Found filename in result for manual scan:', filename);
                        
                        // Request only this specific file
                        socket.emit('request_specific_file', {
                            session_id: sessionId,
                            filename: filename,
                            current_session_only: true
                        });
                        break;
                    }
                }
                
                // If no specific filename was found, but we see mentions of files
                if (!foundSpecificFile && finalResultText.includes('.txt')) {
                    // Request the server to check for artifacts but only for this session
                    socket.emit('check_artifacts', {
                        session_id: sessionId,
                        current_session_only: true
                    });
                } else if (!foundSpecificFile) {
                    // Last resort - look for any artifacts related to this session
                    socket.emit('check_artifacts', {
                        session_id: sessionId,
                        current_session_only: true
                    });
                }
            } else {
                // If no result text is available, request artifacts for the current session only
                socket.emit('check_artifacts', {
                    session_id: sessionId,
                    current_session_only: true
                });
            }
        });
    }

    // Function to display the plan
    function displayPlan(plan) {
        if (!plan || !plan.tasks) {
            console.error("Invalid plan data received", plan);
            setStatus('error', 'Failed to display plan: Invalid data');
            return;
        }

        planSteps.innerHTML = ''; // Clear previous steps
        window.stepStatusElements = {}; // Reset storage for status elements

        plan.tasks.forEach((task, index) => {
            const taskElement = document.createElement('li');
            taskElement.className = 'step-item';
            taskElement.dataset.stepId = task.id;

            // Create status badge container
            const statusBadge = document.createElement('span');
            statusBadge.className = 'status-badge status-pending'; // Default status
            statusBadge.textContent = 'Pending';
            // Store a reference to this badge element for later updates (using task ID)
            window.stepStatusElements[task.id] = statusBadge;

            taskElement.innerHTML = `
                <div class="step-header">
                    <strong class="step-title">${task.title || 'Untitled Task'}</strong>
                    <span class="step-agent-role">(Agent: ${task.agent_role || 'Default'})</span>
                    <!-- Placeholder for status badge -->
                </div>
                <p class="step-description">${task.description || 'No description.'}</p>
                <p class="step-dependencies">Dependencies: ${task.dependencies && task.dependencies.length > 0 ? task.dependencies.join(', ') : 'None'}</p>
            `;
            // Insert the status badge into the header
            const stepHeader = taskElement.querySelector('.step-header');
            if (stepHeader) {
                stepHeader.appendChild(statusBadge);
            }

            planSteps.appendChild(taskElement);
        });

        planSummary.textContent = plan.summary || 'No summary provided.';
        
        // Plan display visibility is handled by CSS via setUIState
        // Consider drawing dependency lines here if implementing visualization
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

    // Function to add a progress update message
    function addProgressUpdate(message) {
        console.log("Inside addProgressUpdate() with message:", message);
        if (!progressUpdates) return; // Exit if the log element doesn't exist

        // Only update the 'current step' display if the message indicates a step is starting
        if (message.startsWith('Starting step')) {
            const currentStepElement = document.getElementById('current-step');
            if (currentStepElement) {
                // Extract step title if possible, otherwise use the whole message
                const stepTitleMatch = message.match(/Starting step \'(.*?)\'/);
                currentStepElement.textContent = stepTitleMatch ? stepTitleMatch[1] : message;
            } else {
                console.warn('currentStep element not found in DOM when updating for starting step');
            }
        }

        // Always add the message to the log list
        const updateItem = document.createElement('li');
        updateItem.textContent = message;
        progressUpdates.appendChild(updateItem);
        
        // Auto-scroll to the bottom
        progressUpdates.scrollTop = progressUpdates.scrollHeight;
    }

    // Function to display the final workflow result
    function showWorkflowResult(resultText) {
        if (!resultContent || !workflowResult) return;

        if (resultText) {
            // Use marked library to render potential Markdown
            resultContent.innerHTML = marked.parse(resultText);
            // workflowResult.style.display = 'block'; // REMOVED - CSS handles this based on state
        } else {
            resultContent.textContent = 'Workflow completed, but no final result was provided.';
            // workflowResult.style.display = 'block'; // REMOVED - CSS handles this based on state
        }
    }

    // Function to show plan analysis
    function showPlanAnalysis(analysis) {
        // analysis is now an object like PlanAnalysisOutput
        if (!analysisContent || !analysis) {
            console.error("Cannot display analysis: element or data missing.");
            return;
        }

        let analysisHtml = `
            <h4>Analysis Scores (1-10):</h4>
            <ul>
                <li>Completeness: ${analysis.completeness_score ?? 'N/A'}</li>
                <li>Clarity: ${analysis.clarity_score ?? 'N/A'}</li>
                <li>Actionability: ${analysis.actionability_score ?? 'N/A'}</li>
                <li>Dependencies: ${analysis.dependency_score ?? 'N/A'}</li>
                <li>Role Assignment: ${analysis.role_assignment_score ?? 'N/A'}</li>
                <li>Feasibility: ${analysis.feasibility_score ?? 'N/A'}</li>
                <li><strong>Overall: ${analysis.overall_score?.toFixed(1) ?? 'N/A'}</strong></li>
            </ul>
            <h4>Suggestions:</h4>
            <p>${analysis.suggestions?.replace(/\n/g, '<br>') ?? 'No suggestions provided.'}</p>
        `;
        analysisContent.innerHTML = analysisHtml;
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
