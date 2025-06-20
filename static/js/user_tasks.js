// User Tasks Management JavaScript

let allTasks = [];
let filteredTasks = [];

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    loadTasks();
    setupEventListeners();
});

function setupEventListeners() {
    // Filter event listeners
    document.getElementById('statusFilter').addEventListener('change', filterTasks);
    document.getElementById('priorityFilter').addEventListener('change', filterTasks);
    document.getElementById('searchFilter').addEventListener('input', filterTasks);
}

function loadTasks() {
    const token = localStorage.getItem('authToken');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    fetch('/api/user/tasks', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.status === 401) {
            localStorage.removeItem('authToken');
            window.location.href = '/login';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.tasks) {
            allTasks = data.tasks;
            filteredTasks = [...allTasks];
            renderTasks();
        } else {
            showEmptyState();
        }
    })
    .catch(error => {
        console.error('Error loading tasks:', error);
        showError('Failed to load tasks. Please try again.');
    });
}

function renderTasks() {
    const container = document.getElementById('tasksContainer');
    
    if (filteredTasks.length === 0) {
        showEmptyState();
        return;
    }

    let html = '';
    filteredTasks.forEach(task => {
        html += createTaskCard(task);
    });
    
    container.innerHTML = html;
}

function createTaskCard(task) {
    const statusClass = getStatusClass(task.status);
    const priorityClass = getPriorityClass(task.priority);
    const dueDate = task.due_date ? new Date(task.due_date).toLocaleDateString() : 'No due date';
    const createdDate = task.created ? new Date(task.created).toLocaleDateString() : 'Unknown';
    
    return `
        <div class="task-card">
            <div class="task-header">
                <div class="flex-grow-1">
                    <div class="task-title">${escapeHtml(task.task)}</div>
                    <div class="task-meta">
                        <span class="status-badge ${statusClass}">${task.status}</span>
                        <span class="priority-badge ${priorityClass} ms-2">${task.priority}</span>
                        <span class="ms-3">Due: ${dueDate}</span>
                        <span class="ms-3">Created: ${createdDate}</span>
                    </div>
                </div>
            </div>
            
            ${task.notes ? `<div class="task-notes mt-2">${escapeHtml(task.notes)}</div>` : ''}
            ${task.category ? `<div class="task-category mt-1"><small class="text-muted">Category: ${escapeHtml(task.category)}</small></div>` : ''}
            
            <div class="task-actions">
                <button class="btn btn-sm btn-outline-primary" onclick="editTask('${task.id}')">
                    <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn btn-sm btn-outline-danger" onclick="deleteTask('${task.id}')">
                    <i class="bi bi-trash"></i> Delete
                </button>
            </div>
        </div>
    `;
}

function getStatusClass(status) {
    const statusMap = {
        'Not Started': 'status-not-started',
        'In Progress': 'status-in-progress',
        'Completed': 'status-completed',
        'On Hold': 'status-on-hold'
    };
    return statusMap[status] || 'status-not-started';
}

function getPriorityClass(priority) {
    const priorityMap = {
        'Low': 'priority-low',
        'Medium': 'priority-medium',
        'High': 'priority-high',
        'Urgent': 'priority-urgent'
    };
    return priorityMap[priority] || 'priority-medium';
}

function showEmptyState() {
    const container = document.getElementById('tasksContainer');
    container.innerHTML = `
        <div class="empty-state">
            <i class="bi bi-list-task" style="font-size: 3rem; color: #dee2e6;"></i>
            <h4 class="mt-3">No tasks yet</h4>
            <p>Get started by creating your first task!</p>
            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addTaskModal">
                <i class="bi bi-plus"></i> Add Your First Task
            </button>
        </div>
    `;
}

function filterTasks() {
    const statusFilter = document.getElementById('statusFilter').value;
    const priorityFilter = document.getElementById('priorityFilter').value;
    const searchFilter = document.getElementById('searchFilter').value.toLowerCase();

    filteredTasks = allTasks.filter(task => {
        const matchesStatus = !statusFilter || task.status === statusFilter;
        const matchesPriority = !priorityFilter || task.priority === priorityFilter;
        const matchesSearch = !searchFilter || 
            task.task.toLowerCase().includes(searchFilter) ||
            (task.notes && task.notes.toLowerCase().includes(searchFilter)) ||
            (task.category && task.category.toLowerCase().includes(searchFilter));

        return matchesStatus && matchesPriority && matchesSearch;
    });

    renderTasks();
}

function addTask() {
    const taskData = {
        task: document.getElementById('taskTitle').value,
        notes: document.getElementById('taskDescription').value,
        status: document.getElementById('taskStatus').value,
        priority: document.getElementById('taskPriority').value,
        category: document.getElementById('taskCategory').value,
        due_date: document.getElementById('taskDueDate').value || null
    };

    if (!taskData.task.trim()) {
        showError('Task title is required');
        return;
    }

    const token = localStorage.getItem('authToken');
    
    fetch('/api/user/tasks', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskData)
    })
    .then(response => {
        if (response.status === 401) {
            localStorage.removeItem('authToken');
            window.location.href = '/login';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.task) {
            // Close modal and reset form
            const modal = bootstrap.Modal.getInstance(document.getElementById('addTaskModal'));
            modal.hide();
            document.getElementById('addTaskForm').reset();
            
            // Reload tasks
            loadTasks();
            showSuccess('Task created successfully!');
        } else {
            showError(data.error || 'Failed to create task');
        }
    })
    .catch(error => {
        console.error('Error creating task:', error);
        showError('Failed to create task. Please try again.');
    });
}

function editTask(taskId) {
    const task = allTasks.find(t => t.id === taskId);
    if (!task) {
        showError('Task not found');
        return;
    }

    // Populate edit form
    document.getElementById('editTaskId').value = task.id;
    document.getElementById('editTaskTitle').value = task.task;
    document.getElementById('editTaskDescription').value = task.notes || '';
    document.getElementById('editTaskStatus').value = task.status;
    document.getElementById('editTaskPriority').value = task.priority;
    document.getElementById('editTaskCategory').value = task.category || '';
    document.getElementById('editTaskDueDate').value = task.due_date || '';

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('editTaskModal'));
    modal.show();
}

function updateTask() {
    const taskId = document.getElementById('editTaskId').value;
    const taskData = {
        task: document.getElementById('editTaskTitle').value,
        notes: document.getElementById('editTaskDescription').value,
        status: document.getElementById('editTaskStatus').value,
        priority: document.getElementById('editTaskPriority').value,
        category: document.getElementById('editTaskCategory').value,
        due_date: document.getElementById('editTaskDueDate').value || null
    };

    if (!taskData.task.trim()) {
        showError('Task title is required');
        return;
    }

    const token = localStorage.getItem('authToken');
    
    fetch(`/api/user/tasks/${taskId}`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(taskData)
    })
    .then(response => {
        if (response.status === 401) {
            localStorage.removeItem('authToken');
            window.location.href = '/login';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.message) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('editTaskModal'));
            modal.hide();
            
            // Reload tasks
            loadTasks();
            showSuccess('Task updated successfully!');
        } else {
            showError(data.error || 'Failed to update task');
        }
    })
    .catch(error => {
        console.error('Error updating task:', error);
        showError('Failed to update task. Please try again.');
    });
}

function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task? This action cannot be undone.')) {
        return;
    }

    const token = localStorage.getItem('authToken');
    
    fetch(`/api/user/tasks/${taskId}`, {
        method: 'DELETE',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.status === 401) {
            localStorage.removeItem('authToken');
            window.location.href = '/login';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.message) {
            loadTasks();
            showSuccess('Task deleted successfully!');
        } else {
            showError(data.error || 'Failed to delete task');
        }
    })
    .catch(error => {
        console.error('Error deleting task:', error);
        showError('Failed to delete task. Please try again.');
    });
}

function refreshTasks() {
    loadTasks();
}

function showSuccess(message) {
    // Create a temporary success message
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 3000);
}

function showError(message) {
    // Create a temporary error message
    const alert = document.createElement('div');
    alert.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
} 