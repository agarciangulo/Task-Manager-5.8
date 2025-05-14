// Updated JavaScript for Task Manager with Chat Verification
$(document).ready(function() {
    // User ID for session tracking
    let userId = localStorage.getItem('chat_user_id') || generateUserId();
    
    // Function to generate a random user ID
    function generateUserId() {
        return 'user_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Function to show notifications
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = $(`
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `);
        
        // Add to container
        const container = $('#notificationContainer');
        if (container.length === 0) {
            // Create container if it doesn't exist
            $('body').append('<div id="notificationContainer" class="toast-container position-fixed bottom-0 end-0 p-3"></div>');
        }
        $('#notificationContainer').append(notification);
        
        // Initialize and show toast
        const toast = new bootstrap.Toast(notification, {
            autohide: true,
            delay: 5000
        });
        toast.show();
        
        // Remove from DOM after hiding
        notification.on('hidden.bs.toast', function() {
            notification.remove();
        });
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
        
        // Send AJAX request with raw text
        $.ajax({
            url: '/api/process_update',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                text: updateText
            }),
            success: function(response) {
                console.log("Received response:", response);  // Debug log
                
                // Hide loading indicators
                $('#loadingIndicator').hide();
                $('#typing-indicator').hide();
                $('#submitBtn').prop('disabled', false).html('<i class="bi bi-send"></i> Submit Update');
                
                if (response.success) {
                    console.log("Response successful, preparing to display results");  // Debug log
                    
                    // Ensure we have the required data
                    if (!response.processed_tasks) {
                        console.error("No processed tasks in response");  // Debug log
                        $('#results').html(`
                            <div class="alert alert-warning">
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                                No tasks were processed. Please try again.
                            </div>
                        `);
                        return;
                    }
                    
                    // Display results
                    try {
                        displayResults(response);
                        console.log("Results displayed successfully");  // Debug log
                    } catch (error) {
                        console.error("Error displaying results:", error);  // Debug log
                        $('#results').html(`
                            <div class="alert alert-danger">
                                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                                Error displaying results: ${error.message}
                            </div>
                        `);
                    }
                    
                    // Show success notification
                    showNotification('Update processed successfully!', 'success');
                } else {
                    console.error("Response indicated failure:", response);  // Debug log
                    // Handle error
                    $('#results').html(`
                        <div class="alert alert-danger">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            ${response.error || 'Failed to process update'}
                        </div>
                    `);
                    showNotification(response.error || 'Failed to process update', 'error');
                }
            },
            error: function(xhr, status, error) {
                console.error("Error processing update:", error);  // Debug log
                console.error("Server response:", xhr.responseText);  // Debug log
                
                // Hide loading indicators
                $('#loadingIndicator').hide();
                $('#typing-indicator').hide();
                $('#submitBtn').prop('disabled', false).html('<i class="bi bi-send"></i> Submit Update');
                
                // Show error message
                $('#results').html(`
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        Error processing update: ${error}
                    </div>
                `);
                showNotification('Error processing update: ' + error, 'error');
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
                <div class="message-content">
                    ${content}
                </div>
            </div>
        `;
        
        $('#chatMessages').append(messageHtml);
        scrollChatToBottom();
    }
    
    // Function to scroll chat to bottom
    function scrollChatToBottom() {
        $('#chatMessages').scrollTop($('#chatMessages')[0].scrollHeight);
    }
});