// Updated JavaScript for Task Manager with Chat Verification
$(document).ready(function() {
    // User ID for session tracking
    let userId = localStorage.getItem('chat_user_id') || generateUserId();
    
    // Function to generate a random user ID
    function generateUserId() {
        return 'user_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Store the user ID
    localStorage.setItem('chat_user_id', userId);
    
    // Form submission handler with enhanced UX
    $('#updateForm').on('submit', function(e) {
        e.preventDefault();
        
        const updateText = $('#updateText').val().trim();
        if (!updateText) {
            showNotification('Please enter your update text', 'warning');
            return;
        }
        
        // Show loading indicator and disable button
        $('#submitBtn').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...');
        $('#loadingIndicator').fadeIn(300);
        
        // Hide chat verification container if it was previously shown
        $('#chatVerificationContainer').hide();
        
        // Clear chat messages
        $('#chatMessages').empty();
        
        // Placeholder loading text
        $('#results').html(`
            <div class="text-center p-4">
                <div class="spinner-border text-primary mb-3" role="status"></div>
                <p class="text-muted">Analyzing your update...</p>
                <p class="text-muted small">Extracting tasks and generating insights</p>
            </div>
        `);
        
        // Send AJAX request
        $.ajax({
            url: '/api/process_update',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                text: updateText,
                user_id: userId
            }),
            dataType: 'json',
            success: function(response) {
                console.log("Received response:", response);  // Debug log
                if (response.success) {
                    // Check if verification is needed
                    if (response.needs_verification) {
                        // Show notification
                        showNotification(`Processed ${response.complete_count} tasks. Some tasks need more information.`, 'info');
                        
                        // Show chat verification interface
                        $('#chatVerificationContainer').show();
                        
                        // Add bot message
                        addChatMessage('bot', response.verification_message);
                        
                        // Update results
                        if (response.complete_count > 0) {
                            $('#results').html(`
                                <div class="alert alert-success">
                                    <i class="bi bi-check-circle-fill me-2"></i>
                                    Successfully processed ${response.complete_count} tasks with complete information.
                                </div>
                                <div class="alert alert-info">
                                    <i class="bi bi-info-circle-fill me-2"></i>
                                    ${response.incomplete_count} tasks need more information. Please check the verification chat below.
                                </div>
                            `);
                        } else {
                            $('#results').html(`
                                <div class="alert alert-info">
                                    <i class="bi bi-info-circle-fill me-2"></i>
                                    All ${response.incomplete_count} tasks need more information. Please check the verification chat below.
                                </div>
                            `);
                        }
                        
                        // Scroll to chat
                        $('html, body').animate({
                            scrollTop: $('#chatVerificationContainer').offset().top - 20
                        }, 500);
                        
                        // Focus on chat input
                        $('#chatInput').focus();
                    } else {
                        // Display normal results
                        console.log("Displaying results:", response);  // Debug log
                        displayResults(response);
                        showNotification('Update processed successfully!', 'success');
                    }
                } else {
                    console.error("Error in response:", response);  // Debug log
                    $('#results').html(`
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            ${response.message || 'An error occurred while processing your update.'}
                        </div>
                    `);
                    showNotification('Error processing update', 'danger');
                }
            },
            error: function(xhr, status, error) {
                console.error("AJAX error:", error);  // Debug log
                $('#results').html(`
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        An error occurred while processing your update. Please try again.
                    </div>
                `);
                showNotification('Server error. Please try again.', 'danger');
            },
            complete: function() {
                // Hide loading indicator and restore button
                $('#submitBtn').prop('disabled', false).html('<i class="bi bi-send"></i> Submit Update');
                $('#loadingIndicator').fadeOut(300);
                
                // Refresh categories dropdown
                refreshCategories();
                
                // Collapse tools section if it was hidden
                if (!$('#toolsCollapse').hasClass('show')) {
                    $('#toolsCollapse').collapse('show');
                }
            }
        });
    });
    
    // Chat submission handler
    $('#chatForm').on('submit', function(e) {
        e.preventDefault();
        
        const message = $('#chatInput').val().trim();
        if (!message) return;
        
        // Add user message to chat
        addChatMessage('user', message);
        
        // Clear input
        $('#chatInput').val('');
        
        // Show typing indicator
        const typingIndicator = $('<div class="chat-message bot-message typing-indicator"><div class="message-content">Typing<span class="dot">.</span><span class="dot">.</span><span class="dot">.</span></div></div>');
        $('#chatMessages').append(typingIndicator);
        scrollChatToBottom();
        
        // Send message to server
        $.ajax({
            url: '/api/chat',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                message: message,
                user_id: userId
            }),
            success: function(response) {
                // Remove typing indicator
                $('.typing-indicator').remove();
                
                if (response.success) {
                    // Add bot response to chat
                    addChatMessage('bot', response.message);
                    
                    console.log('Chat response:', response);  // Debug
                    
                    // Check if all tasks have been processed
                    if (response.has_pending_tasks === false) {
                        // Show success notification
                        showNotification('All tasks have been processed successfully!', 'success');
                        
                        // Process final results if available
                        if (response.processed_tasks && response.coaching) {
                            // Display tasks and coaching insights in the results section
                            let html = '';
                            
                            // Display extracted tasks
                            if (response.processed_tasks.length > 0) {
                                html += `
                                    <div class="mb-4">
                                        <h6 class="mb-3">
                                            <i class="bi bi-list-check text-primary me-2"></i>
                                            Processed Tasks (${response.processed_tasks.length})
                                        </h6>
                                        <ul class="task-list">
                                `;
                                
                                response.processed_tasks.forEach(function(task) {
                                    const statusClass = getStatusClass(task.status);
                                    html += `
                                        <li class="task-item">
                                            <div class="d-flex justify-content-between align-items-start">
                                                <div>
                                                    ${task.task}
                                                    <span class="task-status ${statusClass}">${task.status}</span>
                                                </div>
                                                <small class="text-muted ms-2">${task.category}</small>
                                            </div>
                                            <div class="mt-1">
                                                <small class="text-muted">Assigned to: ${task.employee}</small>
                                            </div>
                                        </li>
                                    `;
                                });
                                
                                html += `
                                        </ul>
                                        <div class="alert alert-success mt-3">
                                            <i class="bi bi-check-circle-fill me-2"></i>
                                            ${response.processed_tasks.length} tasks synced to Notion.
                                        </div>
                                    </div>
                                `;
                            }
                            
                            // Display coaching insights
                            if (response.coaching) {
                                html += `
                                    <div class="insights-section">
                                        <h6 class="mb-3">
                                            <i class="bi bi-lightbulb text-warning me-2"></i>
                                            AI Assessment
                                        </h6>
                                        <p>${response.coaching}</p>
                                    </div>
                                `;
                            }
                            
                            // Display logs if in debug mode
                            if (response.logs && response.logs.length > 0) {
                                html += `
                                    <details class="mt-3">
                                        <summary class="text-muted small">Technical Details</summary>
                                        <div class="tech-details">
                                            ${response.logs.join('<br>')}
                                        </div>
                                    </details>
                                `;
                            }
                            
                            $('#results').html(html);
                        } else {
                            // Get final results with a separate call
                            $.ajax({
                                url: '/api/chat',
                                type: 'POST',
                                contentType: 'application/json',
                                data: JSON.stringify({
                                    message: "get_final_results",
                                    user_id: userId
                                }),
                                success: function(finalResponse) {
                                    if (finalResponse.success && finalResponse.processed_tasks) {
                                        // Display the final results
                                        let html = '';
                                        
                                        // Display extracted tasks
                                        if (finalResponse.processed_tasks.length > 0) {
                                            html += `
                                                <div class="mb-4">
                                                    <h6 class="mb-3">
                                                        <i class="bi bi-list-check text-primary me-2"></i>
                                                        Processed Tasks (${finalResponse.processed_tasks.length})
                                                    </h6>
                                                    <ul class="task-list">
                                            `;
                                            
                                            finalResponse.processed_tasks.forEach(function(task) {
                                                const statusClass = getStatusClass(task.status);
                                                html += `
                                                    <li class="task-item">
                                                        <div class="d-flex justify-content-between align-items-start">
                                                            <div>
                                                                ${task.task}
                                                                <span class="task-status ${statusClass}">${task.status}</span>
                                                            </div>
                                                            <small class="text-muted ms-2">${task.category}</small>
                                                        </div>
                                                        <div class="mt-1">
                                                            <small class="text-muted">Assigned to: ${task.employee}</small>
                                                        </div>
                                                    </li>
                                                `;
                                            });
                                            
                                            html += `
                                                    </ul>
                                                    <div class="alert alert-success mt-3">
                                                        <i class="bi bi-check-circle-fill me-2"></i>
                                                        ${finalResponse.processed_tasks.length} tasks synced to Notion.
                                                    </div>
                                                </div>
                                            `;
                                        }
                                        
                                        // Display coaching insights
                                        if (finalResponse.coaching) {
                                            html += `
                                                <div class="insights-section">
                                                    <h6 class="mb-3">
                                                        <i class="bi bi-lightbulb text-warning me-2"></i>
                                                        AI Assessment
                                                    </h6>
                                                    <p>${finalResponse.coaching}</p>
                                                </div>
                                            `;
                                        }
                                        
                                        // Display logs if in debug mode
                                        if (finalResponse.logs && finalResponse.logs.length > 0) {
                                            html += `
                                                <details class="mt-3">
                                                    <summary class="text-muted small">Technical Details</summary>
                                                    <div class="tech-details">
                                                        ${finalResponse.logs.join('<br>')}
                                                    </div>
                                                </details>
                                            `;
                                        }
                                        
                                        $('#results').html(html);
                                    } else {
                                        // Simple success message
                                        $('#results').html(`
                                            <div class="alert alert-success">
                                                <i class="bi bi-check-circle-fill me-2"></i>
                                                All tasks have been successfully processed and saved to Notion.
                                            </div>
                                        `);
                                    }
                                },
                                error: function() {
                                    // Simple success message on error
                                    $('#results').html(`
                                        <div class="alert alert-success">
                                            <i class="bi bi-check-circle-fill me-2"></i>
                                            Tasks processed. Coaching insights unavailable.
                                        </div>
                                    `);
                                }
                            });
                        }
                        
                        // Maybe hide the chat container after a delay
                        setTimeout(function() {
                            $('#chatVerificationContainer').slideUp(500);
                        }, 5000);
                    }
                } else {
                    // Handle error
                    addChatMessage('error', 'Sorry, there was an error processing your message. Please try again.');
                    showNotification('Error processing chat message', 'danger');
                }
            },
            error: function() {
                // Remove typing indicator
                $('.typing-indicator').remove();
                
                addChatMessage('error', 'Sorry, there was an error connecting to the server. Please try again.');
                showNotification('Server error. Please try again.', 'danger');
            }
        });
    });
    
    // Function to add message to chat
    function addChatMessage(type, content) {
        const messageClass = type === 'user' ? 'user-message' : 
                            (type === 'bot' ? 'bot-message' : 'error-message');
        
        // Process the content to highlight task items
        if (type === 'bot') {
            // Look for numbered task lists and add styling
            content = content.replace(/(\d+\.\s+Task:\s+"[^"]+")(\n\s+\-\s+[^\n]+)/g, '<div class="task-item">$1$2</div>');
        }
        
        const messageHtml = `
            <div class="chat-message ${messageClass}">
                <div class="message-content">${content}</div>
            </div>
        `;
        
        $('#chatMessages').append(messageHtml);
        
        // Scroll to bottom
        scrollChatToBottom();
    }
    
    function scrollChatToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Auto-resize textarea
    $('#chatInput').on('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Check for overdue tasks with enhanced UX
    $('#reminderBtn').on('click', function() {
        const $btn = $(this);
        $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Checking...');
        
        $('#reminderOutput').html(`
            <div class="text-center p-3">
                <div class="spinner-border text-danger spinner-border-sm" role="status"></div>
                <p class="text-muted small">Checking for overdue tasks...</p>
            </div>
        `);
        
        $.ajax({
            url: '/api/stale_tasks',
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    if (response.has_stale) {
                        displayStaleTasks(response.tasks_by_employee);
                        showNotification('Found overdue tasks that need attention', 'warning');
                    } else {
                        $('#reminderOutput').html(`
                            <div class="alert alert-success">
                                <i class="bi bi-check-circle-fill me-2"></i>
                                ${response.message}
                            </div>
                        `);
                        showNotification('No overdue tasks found!', 'success');
                    }
                } else {
                    $('#reminderOutput').html(`
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            ${response.message}
                        </div>
                    `);
                    showNotification('Error checking overdue tasks', 'danger');
                }
            },
            error: function(xhr, status, error) {
                $('#reminderOutput').html(`
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        <strong>Error:</strong> Could not fetch overdue tasks. Please try again later.
                    </div>
                `);
                showNotification('Server error. Please try again.', 'danger');
                console.error('Error:', error);
            },
            complete: function() {
                $btn.prop('disabled', false).html('<i class="bi bi-search"></i> Check Overdue Tasks');
            }
        });
    });
    
    // View tasks by category with enhanced UX
    $('#categoryBtn').on('click', function() {
        const category = $('#categoryDropdown').val();
        if (!category) {
            showNotification('Please select a category', 'warning');
            return;
        }
        
        const $btn = $(this);
        $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...');
        
        $('#categoryResult').html(`
            <div class="text-center p-3">
                <div class="spinner-border text-primary spinner-border-sm" role="status"></div>
                <p class="text-muted small">Fetching tasks for ${category}...</p>
            </div>
        `);
        
        $.ajax({
            url: `/api/tasks_by_category?category=${encodeURIComponent(category)}`,
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    if (response.has_tasks) {
                        displayCategoryTasks(response, category);
                        showNotification(`Loaded ${category} tasks successfully`, 'success');
                    } else {
                        $('#categoryResult').html(`
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle-fill me-2"></i>
                                ${response.message}
                            </div>
                        `);
                        showNotification('No open tasks found', 'info');
                    }
                } else {
                    $('#categoryResult').html(`
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            ${response.message}
                        </div>
                    `);
                    showNotification('Error fetching tasks', 'danger');
                }
            },
            error: function(xhr, status, error) {
                $('#categoryResult').html(`
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        <strong>Error:</strong> Could not fetch tasks. Please try again later.
                    </div>
                `);
                showNotification('Server error. Please try again.', 'danger');
                console.error('Error:', error);
            },
            complete: function() {
                $btn.prop('disabled', false).html('<i class="bi bi-filter"></i> View Tasks by Project');
            }
        });
    });
    
    // Function to refresh categories
    function refreshCategories() {
        $.ajax({
            url: '/api/categories',
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    const dropdown = $('#categoryDropdown');
                    dropdown.empty();
                    
                    response.categories.forEach(function(category) {
                        dropdown.append(`<option value="${category}">${category}</option>`);
                    });
                }
            },
            error: function(xhr, status, error) {
                console.error('Error refreshing categories:', error);
            }
        });
    }
    
    // Function to display task processing results
    function displayResults(response) {
        let html = '';
        
        // Display extracted tasks
        if (response.tasks && response.tasks.length > 0) {
            html += `
                <div class="mb-4">
                    <h6 class="mb-3">
                        <i class="bi bi-list-check text-primary me-2"></i>
                        Extracted Tasks (${response.tasks.length})
                    </h6>
                    <ul class="task-list">
            `;
            
            response.tasks.forEach(function(task) {
                const statusClass = getStatusClass(task.status);
                html += `
                    <li class="task-item">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                ${task.task}
                                <span class="task-status ${statusClass}">${task.status}</span>
                            </div>
                            <small class="text-muted ms-2">${task.category}</small>
                        </div>
                        <div class="mt-1">
                            <small class="text-muted">Assigned to: ${task.employee}</small>
                        </div>
                    </li>
                `;
            });
            
            html += `
                    </ul>
                    <div class="alert alert-success mt-3">
                        <i class="bi bi-check-circle-fill me-2"></i>
                        ${response.tasks.length} tasks synced to Notion.
                    </div>
                </div>
            `;
        }
        
        // Display coaching insights
        if (response.coaching) {
            html += `
                <div class="insights-section">
                    <h6 class="mb-3">
                        <i class="bi bi-lightbulb text-warning me-2"></i>
                        AI Assessment
                    </h6>
                    <p>${response.coaching}</p>
                </div>
            `;
        }
        
        // Display logs if in debug mode
        if (response.logs && response.logs.length > 0) {
            html += `
                <details class="mt-3">
                    <summary class="text-muted small">Technical Details</summary>
                    <div class="tech-details">
                        ${response.logs.join('<br>')}
                    </div>
                </details>
            `;
        }
        
        $('#results').html(html);
    }
    
    // Function to display stale tasks
    function displayStaleTasks(tasksByEmployee) {
        let html = `
            <h6 class="mb-3">
                <i class="bi bi-exclamation-triangle-fill text-danger me-2"></i>
                Overdue Tasks
            </h6>
        `;
        
        for (const employee in tasksByEmployee) {
            html += `
                <div class="employee-section">
                    <div class="employee-name">
                        <i class="bi bi-person-fill me-1"></i>
                        ${employee}
                    </div>
                    <ul class="task-list">
            `;
            
            tasksByEmployee[employee].forEach(function(task) {
                const statusClass = getStatusClass(task.status);
                html += `
                    <li class="task-item">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                ${task.task}
                                <span class="task-status ${statusClass}">${task.status}</span>
                            </div>
                        </div>
                        <div class="mt-1 d-flex justify-content-between">
                            <small class="text-muted">Since: ${task.date}</small>
                            <small class="text-danger fw-bold">${task.days_old} days overdue</small>
                        </div>
                    </li>
                `;
            });
            
            html += `
                    </ul>
                </div>
            `;
        }
        
        $('#reminderOutput').html(html);
    }
    
    // Function to display category tasks
    function displayCategoryTasks(response, category) {
        let html = `
            <h6 class="mb-3">
                <i class="bi bi-folder-fill text-primary me-2"></i>
                Tasks for "${category}"
            </h6>
        `;
        
        // Display tasks by employee
        const tasksByEmployee = response.tasks_by_employee;
        for (const employee in tasksByEmployee) {
            html += `
                <div class="employee-section">
                    <div class="employee-name">
                        <i class="bi bi-person-fill me-1"></i>
                        ${employee}
                    </div>
                    <ul class="task-list">
            `;
            
            tasksByEmployee[employee].forEach(function(task) {
                const statusClass = getStatusClass(task.status);
                html += `
                    <li class="task-item">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                ${task.task}
                                <span class="task-status ${statusClass}">${task.status}</span>
                            </div>
                        </div>
                        <div class="mt-1">
                            <small class="text-muted">Date: ${task.date}</small>
                        </div>
                    </li>
                `;
            });
            
            html += `
                    </ul>
                </div>
            `;
        }
        
        // Display status summary
        if (response.status_summary) {
            html += `<div class="mt-3">
                <h6 class="mb-2">
                    <i class="bi bi-bar-chart-fill text-primary me-2"></i>
                    Project Status Summary
                </h6>
                <div class="d-flex flex-wrap gap-2 mb-3">
            `;
            
            for (const status in response.status_summary) {
                const statusClass = getStatusClass(status);
                html += `
                    <div class="badge bg-light text-dark p-2">
                        <span class="task-status ${statusClass} me-1">${status}</span>
                        <span class="fw-bold">${response.status_summary[status]}</span> task(s)
                    </div>
                `;
            }
            
            html += `
                </div>
            </div>`;
        }
        
        // Display AI insight
        if (response.insight) {
            html += `
                <div class="insights-section mt-3">
                    <h6 class="mb-2">
                        <i class="bi bi-lightbulb text-warning me-2"></i>
                        AI Project Insight
                    </h6>
                    <p>${response.insight}</p>
                </div>
            `;
        }
        
        $('#categoryResult').html(html);
    }
    
    // Helper function to get status class
    function getStatusClass(status) {
        const statusLower = status.toLowerCase();
        if (statusLower.includes('completed')) {
            return 'status-completed';
        } else if (statusLower.includes('progress')) {
            return 'status-in-progress';
        } else if (statusLower.includes('pending')) {
            return 'status-pending';
        } else if (statusLower.includes('blocked')) {
            return 'status-blocked';
        } else {
            return '';
        }
    }
    
    // Function to show toast notifications
    function showNotification(message, type = 'info') {
        // Remove existing toasts
        $('.toast').remove();
        
        // Create new toast
        const toast = `
            <div class="toast position-fixed bottom-0 end-0 m-3" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header bg-${type} text-white">
                    <strong class="me-auto">Task Manager</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        // Append and show toast
        $('body').append(toast);
        $('.toast').toast({
            delay: 3000,
            animation: true
        }).toast('show');
    }
    
    // Initialize tooltips and popovers
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});