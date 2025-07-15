// Dashboard JavaScript with filtering support
$(document).ready(function() {
    // Track current filters
    let currentFilters = {
        employee: 'all',
        project: 'all'
    };
    
    // Charts
    let taskTrendChart;
    let categoryChart;
    
    // Load dashboard data on page load
    loadDashboardData();
    
    // Handle refresh button
    $('#refreshBtn').on('click', function() {
        loadDashboardData();
    });
    
    // Handle apply filters button
    $('#applyFilterBtn').on('click', function() {
        // Get selected values
        currentFilters.employee = $('#employeeFilter').val();
        currentFilters.project = $('#projectFilter').val();
        
        // Reload data with new filters
        loadDashboardData();
    });
    
    // Function to load dashboard data
    function loadDashboardData() {
        // Show loading states
        $('#refreshBtn').prop('disabled', true).html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...');
        $('#applyFilterBtn').prop('disabled', true);
        
        // Show loading placeholders
        $('#keyMetrics').addClass('opacity-50');
        $('#projectHealthContainer').html(`
            <div class="text-center p-5">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-2 text-muted">Loading project health data...</p>
            </div>
        `);
        $('#employeeStatsContainer').html(`
            <div class="text-center p-5">
                <div class="spinner-border text-primary" role="status"></div>
                <p class="mt-2 text-muted">Loading employee data...</p>
            </div>
        `);
        
        // Add filter parameters to query string
        const queryParams = new URLSearchParams({
            employee: currentFilters.employee,
            project: currentFilters.project
        }).toString();
        
        $.ajax({
            url: `/api/dashboard_data?${queryParams}`,
            type: 'GET',
            dataType: 'json',
            headers: {
                'Authorization': 'Bearer ' + localStorage.getItem('authToken')
            },
            success: function(response) {
                if (response.success) {
                    updateDashboard(response);
                    
                    // Update filter dropdowns with all available options
                    updateFilterOptions(response.all_employees, response.all_categories);
                    
                    // Set current filter values in dropdowns
                    $('#employeeFilter').val(response.filters.employee);
                    $('#projectFilter').val(response.filters.project);
                    
                    // Show filter status
                    const employeeFilter = response.filters.employee !== 'all' 
                        ? `Employee: ${response.filters.employee}` 
                        : 'All Employees';
                        
                    const projectFilter = response.filters.project !== 'all' 
                        ? `Project: ${response.filters.project}` 
                        : 'All Projects';
                    
                    // Create toast notification
                    showFilterToast(employeeFilter, projectFilter);
                } else {
                    showNotification('Error loading dashboard data: ' + response.message, 'danger');
                }
            },
            error: function(xhr, status, error) {
                showNotification('Failed to load dashboard data. Please try again later.', 'danger');
                console.error('Error:', error);
            },
            complete: function() {
                // Restore button states
                $('#refreshBtn').prop('disabled', false).html('<i class="bi bi-arrow-clockwise"></i> Refresh Data');
                $('#applyFilterBtn').prop('disabled', false);
                
                // Remove loading effects
                $('#keyMetrics').removeClass('opacity-50');
            }
        });
    }
    
    // Function to update filter dropdowns
    function updateFilterOptions(employees, categories) {
        // Update employee filter options
        const employeeFilter = $('#employeeFilter');
        const currentEmployee = employeeFilter.val();
        
        // Store the current selection
        employeeFilter.empty();
        employeeFilter.append('<option value="all">All Employees</option>');
        
        employees.forEach(function(employee) {
            employeeFilter.append(`<option value="${employee}">${employee}</option>`);
        });
        
        // Restore selection if it still exists in the options
        if (employees.includes(currentEmployee) || currentEmployee === 'all') {
            employeeFilter.val(currentEmployee);
        }
        
        // Update project filter options
        const projectFilter = $('#projectFilter');
        const currentProject = projectFilter.val();
        
        projectFilter.empty();
        projectFilter.append('<option value="all">All Projects</option>');
        
        categories.forEach(function(category) {
            projectFilter.append(`<option value="${category}">${category}</option>`);
        });
        
        // Restore selection if it still exists in the options
        if (categories.includes(currentProject) || currentProject === 'all') {
            projectFilter.val(currentProject);
        }
    }
    
    // Function to update dashboard with new data
    function updateDashboard(data) {
        // Update key metrics
        updateKeyMetrics(data.metrics);
        
        // Update charts
        updateTaskTrendChart(data.trend_data);
        updateCategoryChart(data.category_data);
        
        // Update project health
        updateProjectHealth(data.project_health);
        
        // Update employee stats
        updateEmployeeStats(data.employee_stats);
    }
    
    // Function to update key metrics
    function updateKeyMetrics(metrics) {
        $('#totalTasks').text(metrics.total_tasks);
        $('#completedTasks').text(metrics.completed_tasks);
        $('#inProgressTasks').text(metrics.in_progress_tasks);
        $('#pendingTasks').text(metrics.pending_tasks);
        $('#blockedTasks').text(metrics.blocked_tasks);
        $('#completionRate').text(metrics.completion_rate + '%');
        
        // Add animations for changing numbers
        $('.metric-card h3').addClass('pulse-animation');
        setTimeout(function() {
            $('.metric-card h3').removeClass('pulse-animation');
        }, 1000);
    }
    
    // Function to update task trend chart
    function updateTaskTrendChart(trendData) {
        const ctx = document.getElementById('taskTrendChart').getContext('2d');
        
        // Convert data for Chart.js
        const labels = Object.keys(trendData);
        const data = Object.values(trendData);
        
        // Destroy previous chart if exists
        if (taskTrendChart) {
            taskTrendChart.destroy();
        }
        
        // Create new chart
        taskTrendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Completed Tasks',
                    data: data,
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 4,
                    pointBackgroundColor: 'rgba(16, 185, 129, 1)',
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: 'white',
                    pointHoverBorderWidth: 2,
                    pointHoverBorderColor: 'rgba(16, 185, 129, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',
                        padding: 10,
                        cornerRadius: 4,
                        titleFont: {
                            size: 14
                        },
                        bodyFont: {
                            size: 13
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                animation: {
                    duration: 1000
                }
            }
        });
        
        // Show "No data" message if chart is empty
        if (labels.length === 0) {
            const noDataText = currentFilters.employee !== 'all' || currentFilters.project !== 'all'
                ? 'No completed tasks found with the current filters'
                : 'No task completion data available';
                
            showChartOverlay('taskTrendChart', noDataText);
        }
    }
    
    // Function to update category chart
    function updateCategoryChart(categoryData) {
        const ctx = document.getElementById('categoryChart').getContext('2d');
        
        // Convert data for Chart.js
        const labels = Object.keys(categoryData);
        const data = Object.values(categoryData);
        
        // Generate colors
        const backgroundColors = generateColors(labels.length);
        
        // Destroy previous chart if exists
        if (categoryChart) {
            categoryChart.destroy();
        }
        
        // Create new chart
        categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: backgroundColors,
                    borderWidth: 1,
                    borderColor: 'white',
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    duration: 1000
                },
                cutout: '65%'
            }
        });
        
        // Show "No data" message if chart is empty
        if (labels.length === 0) {
            const noDataText = currentFilters.employee !== 'all' || currentFilters.project !== 'all'
                ? 'No tasks found with the current filters'
                : 'No category data available';
                
            showChartOverlay('categoryChart', noDataText);
        }
    }
    
    // Function to show overlay on empty charts
    function showChartOverlay(chartId, message) {
        // Get the chart container
        const container = document.getElementById(chartId).parentNode;
        
        // Create the overlay
        const overlay = document.createElement('div');
        overlay.className = 'chart-overlay';
        overlay.innerHTML = `
            <div class="chart-overlay-content">
                <i class="bi bi-exclamation-circle text-muted mb-2"></i>
                <p>${message}</p>
            </div>
        `;
        
        // Add overlay to container
        container.appendChild(overlay);
    }
    
    // Function to update project health
    function updateProjectHealth(projectHealth) {
        const container = $('#projectHealthContainer');
        
        if (Object.keys(projectHealth).length === 0) {
            container.html(`
                <div class="alert alert-info m-3">
                    <i class="bi bi-info-circle-fill me-2"></i>
                    No project health data available with the current filters.
                </div>
            `);
            return;
        }
        
        container.empty();
        
        // Sort projects by health score (descending)
        const sortedProjects = Object.entries(projectHealth).sort((a, b) => b[1].score - a[1].score);
        
        for (const [project, health] of sortedProjects) {
            const statusClass = getHealthStatusClass(health.status);
            const cardClass = `health-${health.status.toLowerCase().replace(' ', '-')}`;
            
            const progressColor = getProgressBarColor(health.score);
            
            const card = `
                <div class="project-card ${cardClass}" data-project="${project}">
                    <h6>
                        <span>${project}</span>
                        <span class="health-score">${health.score}</span>
                    </h6>
                    <div class="progress">
                        <div class="progress-bar ${progressColor}" role="progressbar" style="width: ${health.score}%" 
                            aria-valuenow="${health.score}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mt-1">
                        <small>${health.task_count} tasks</small>
                        <span class="health-status status-${health.status.toLowerCase().replace(' ', '-')}">${health.status}</span>
                    </div>
                </div>
            `;
            
            container.append(card);
        }
        
        // Add click event to filter by project
        $('.project-card').on('click', function() {
            const project = $(this).data('project');
            $('#projectFilter').val(project);
            currentFilters.project = project;
            
            // If employee is filtered, keep that filter
            currentFilters.employee = $('#employeeFilter').val();
            
            // Reload data with new filters
            loadDashboardData();
        });
    }
    
    // Function to update employee stats
    function updateEmployeeStats(employeeStats) {
        const container = $('#employeeStatsContainer');
        
        if (Object.keys(employeeStats).length === 0) {
            container.html(`
                <div class="alert alert-info m-3">
                    <i class="bi bi-info-circle-fill me-2"></i>
                    No employee data available with the current filters.
                </div>
            `);
            return;
        }
        
        container.empty();
        
        // Sort employees by completion rate (descending)
        const sortedEmployees = Object.entries(employeeStats).sort((a, b) => b[1].completion_rate - a[1].completion_rate);
        
        for (const [employee, stats] of sortedEmployees) {
            const completionClass = getCompletionRateClass(stats.completion_rate);
            
            const card = `
                <div class="employee-card" data-employee="${employee}">
                    <h6>
                        <span><i class="bi bi-person-fill text-primary me-1"></i> ${employee}</span>
                        <span class="completion-badge ${completionClass}">${stats.completion_rate}%</span>
                    </h6>
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" style="width: ${stats.completion_rate}%" 
                            aria-valuenow="${stats.completion_rate}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                    <div class="d-flex justify-content-between mt-2">
                        <small>${stats.completed_tasks} completed</small>
                        <small>${stats.total_tasks} total tasks</small>
                    </div>
                </div>
            `;
            
            container.append(card);
        }
        
        // Add click event to filter by employee
        $('.employee-card').on('click', function() {
            const employee = $(this).data('employee');
            $('#employeeFilter').val(employee);
            currentFilters.employee = employee;
            
            // If project is filtered, keep that filter
            currentFilters.project = $('#projectFilter').val();
            
            // Reload data with new filters
            loadDashboardData();
        });
    }
    
    // Helper function to generate colors for chart
    function generateColors(count) {
        const colors = [
            'rgba(16, 185, 129, 0.8)',  // Green
            'rgba(59, 130, 246, 0.8)',  // Blue
            'rgba(245, 158, 11, 0.8)',  // Yellow
            'rgba(239, 68, 68, 0.8)',   // Red
            'rgba(139, 92, 246, 0.8)',  // Purple
            'rgba(236, 72, 153, 0.8)',  // Pink
            'rgba(75, 85, 99, 0.8)',    // Gray
            'rgba(14, 165, 233, 0.8)',  // Sky
            'rgba(20, 184, 166, 0.8)',  // Teal
            'rgba(168, 85, 247, 0.8)'   // Violet
        ];
        
        // If more colors are needed, generate them
        if (count > colors.length) {
            for (let i = colors.length; i < count; i++) {
                const r = Math.floor(Math.random() * 255);
                const g = Math.floor(Math.random() * 255);
                const b = Math.floor(Math.random() * 255);
                colors.push(`rgba(${r}, ${g}, ${b}, 0.8)`);
            }
        }
        
        return colors.slice(0, count);
    }
    
    // Helper function to get health status class
    function getHealthStatusClass(status) {
        switch (status.toLowerCase()) {
            case 'healthy':
                return 'status-healthy';
            case 'needs attention':
                return 'status-needs-attention';
            case 'at risk':
                return 'status-at-risk';
            default:
                return 'status-unknown';
        }
    }
    
    // Helper function to get progress bar color
    function getProgressBarColor(score) {
        if (score >= 75) {
            return 'bg-success';
        } else if (score >= 50) {
            return 'bg-warning';
        } else {
            return 'bg-danger';
        }
    }
    
    // Helper function to get completion rate class
    function getCompletionRateClass(rate) {
        if (rate >= 75) {
            return 'completion-high';
        } else if (rate >= 50) {
            return 'completion-medium';
        } else {
            return 'completion-low';
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
    
    // Function to show filter toast
    function showFilterToast(employeeFilter, projectFilter) {
        // Remove existing toasts
        $('.filter-toast').remove();
        
        // If both filters are "all", don't show toast
        if (employeeFilter === 'All Employees' && projectFilter === 'All Projects') {
            return;
        }
        
        // Create new toast
        const toast = `
            <div class="toast filter-toast position-fixed top-0 end-0 m-3" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header bg-primary text-white">
                    <strong class="me-auto"><i class="bi bi-funnel-fill me-1"></i> Active Filters</strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    <div><strong>${employeeFilter}</strong></div>
                    <div><strong>${projectFilter}</strong></div>
                    <div class="mt-2">
                        <button id="clearFiltersBtn" class="btn btn-sm btn-outline-secondary">
                            Clear Filters
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Append and show toast
        $('body').append(toast);
        $('.filter-toast').toast({
            delay: 5000,
            animation: true
        }).toast('show');
        
        // Add event to clear filters button
        $('#clearFiltersBtn').on('click', function() {
            // Reset filters
            $('#employeeFilter').val('all');
            $('#projectFilter').val('all');
            currentFilters.employee = 'all';
            currentFilters.project = 'all';
            
            // Reload data with reset filters
            loadDashboardData();
            
            // Hide toast
            $('.filter-toast').toast('hide');
        });
    }
});