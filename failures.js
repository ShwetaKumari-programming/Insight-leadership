/**
 * Failures.js - Failure analysis page functionality
 * Displays detailed failure metrics and error breakdown
 */

let failureAutoRefresh = null;

async function fetchFailureMetrics() {
    try {
        console.log('Fetching failure metrics...');
        const response = await fetch('/api/metrics/failures');
        const data = await response.json();
        
        // Handle new router response format
        if (data.summary && data.error_distribution && data.failure_insights) {
            updateFailureDisplayNew(data);
        } else if (data.metrics) {
            // Fallback to old format
            updateFailureDisplay(data.metrics);
        }
    } catch (error) {
        console.error('Error fetching failure metrics:', error);
        showErrorMessage('Could not load failure metrics. Please try again.');
    }
}

function updateFailureDisplayNew(data) {
    // Extract summary data
    const summary = data.summary;
    const errorDist = data.error_distribution || [];
    const insights = data.failure_insights || [];
    
    // Update metric cards
    const overallFailure = document.getElementById('overallFailure');
    const totalFailures = document.getElementById('totalFailures');
    const successRate = document.getElementById('successRate');
    const mtbf = document.getElementById('mtbf');
    const severityBadge = document.getElementById('severityBadge');
    
    if (overallFailure) {
        overallFailure.textContent = summary.failure_rate.toFixed(2) + '%';
        // Add explanation
        const explanation = `This metric shows the percentage of transactions that failed in the system. A rate of ${summary.failure_rate.toFixed(2)}% means approximately 1 in ${Math.round(100/summary.failure_rate)} transactions is failing.`;
        updateMetricExplanation('failureRateExplanation', explanation);
    }
    
    if (totalFailures) {
        totalFailures.textContent = summary.total_failures.toLocaleString();
        // Add explanation
        const explanation = `Out of ${summary.total_transactions?.toLocaleString() || 'analyzed'} total transactions, ${summary.total_failures.toLocaleString()} have failed. This is the absolute count of failures in the dataset.`;
        updateMetricExplanation('totalFailuresExplanation', explanation);
    }
    
    if (successRate) {
        successRate.textContent = summary.success_rate.toFixed(2) + '%';
        // Add explanation
        const explanation = `This represents the complement to the failure rate. A ${summary.success_rate.toFixed(2)}% success rate indicates system reliability and successful transaction processing.`;
        updateMetricExplanation('successRateExplanation', explanation);
    }
    
    if (mtbf) {
        mtbf.textContent = summary.mtbf || '-';
        // Add explanation
        const explanation = `Mean Time Between Failures (MTBF) measures how long the system typically runs before encountering a failure. Higher MTBF values indicate better reliability and system stability.`;
        updateMetricExplanation('mtbfExplanation', explanation);
    }
    
    // Update severity badge
    if (severityBadge) {
        const severity = getSeverity(summary.failure_rate);
        severityBadge.innerHTML = `<span class="status-badge status-${severity.level}">${severity.label}</span>`;
    }
    
    // Update error distribution table
    updateErrorDistributionNew(errorDist);
    
    // Update failure insights
    updateFailureInsights(insights);
    
    // Update recommended actions based on top error
    if (errorDist.length > 0) {
        updateRecommendedActionsNew(errorDist);
    }
}

/**
 * NEW FUNCTIONS FOR THE RESTRUCTURED API RESPONSE
 */

function updateErrorDistributionNew(errorDist) {
    const tableBody = document.getElementById('errorTable');
    if (!tableBody) return;
    
    if (!Array.isArray(errorDist) || errorDist.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 30px;">No error data available</td></tr>';
        return;
    }
    
    const rows = errorDist.map(err => `
        <tr>
            <td><strong>${err.error_code}</strong></td>
            <td>${err.error_type}</td>
            <td>${err.count.toLocaleString()}</td>
            <td>${err.percentage.toFixed(2)}%</td>
            <td>${err.recommendation}</td>
        </tr>
    `);
    
    tableBody.innerHTML = rows.join('');
}

function updateFailureInsights(insights) {
    const insightsContainer = document.getElementById('failureInsights');
    if (!insightsContainer) return;
    // Always clear loading state
    if (!Array.isArray(insights) || insights.length === 0) {
        insightsContainer.innerHTML = '<p style="text-align: center; color: #999;">No insights available</p>';
        return;
    }
    const insightHTML = insights.map(insight => `<li style="margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #f0f0f0;">${insight}</li>`).join('');
    insightsContainer.innerHTML = `<ul style="list-style: none; padding-left: 0; margin: 0;">${insightHTML}</ul>`;
}

function updateRecommendedActionsNew(errorDist) {
    const actionsList = document.getElementById('actionsList');
    if (!actionsList) return;
    
    // Get top 3 errors and their recommendations
    const topActions = errorDist.slice(0, 3).map((err, idx) => `
        <li style="padding: 8px 0; border-bottom: 1px solid #eee;">
            <strong>${idx + 1}. ${err.error_code}</strong> - ${err.recommendation}
        </li>
    `);
    
    actionsList.innerHTML = topActions.join('');
}

function updateFailureDisplay(metrics) {
    // Update failure rate cards using actual IDs
    const overallFailure = document.getElementById('overallFailure');
    const totalFailures = document.getElementById('totalFailures');
    const successRate = document.getElementById('successRate');
    const mtbf = document.getElementById('mtbf');
    const severityBadge = document.getElementById('severityBadge');
    const updateTime = document.getElementById('updateTime');
    
    if (overallFailure) {
        overallFailure.textContent = metrics.failure_rate.toFixed(2) + '%';
    }
    
    const failedCount = Math.round(metrics.failure_rate / 100 * metrics.total_transactions);
    if (totalFailures) {
        totalFailures.textContent = failedCount.toLocaleString();
    }
    
    if (successRate) {
        successRate.textContent = metrics.success_rate.toFixed(2) + '%';
    }
    
    if (mtbf) {
        mtbf.textContent = formatTime(metrics.mtbf || 0);
    }
    
    // Update severity badge
    if (severityBadge) {
        const severity = getSeverity(metrics.failure_rate);
        severityBadge.innerHTML = `<span class="status-badge status-${severity.level}">${severity.label}</span>`;
    }
    
    // Update timestamp
    if (updateTime) {
        updateTime.textContent = new Date().toLocaleTimeString();
    }
    
    // Update error distribution table
    updateErrorDistribution(metrics.error_type_distribution || metrics);
    
    // Update failure insights
    generateFailureInsights(metrics);
    
    // Update recommended actions
    updateRecommendedActions(metrics);
}

function updateErrorDistribution(data) {
    const tableBody = document.getElementById('errorTable');
    if (!tableBody) return;
    
    const errorDescriptions = {
        'timeout': 'Network Timeout',
        'payment_error': 'Payment Gateway Failure',
        'auth_failed': 'Authentication Error',
        'server_error': 'Internal Server Error',
        'db_error': 'Database Connection Failure',
        '500': 'Internal Server Error',
        '502': 'Bad Gateway',
        '503': 'Service Unavailable',
        '504': 'Gateway Timeout'
    };
    
    const recommendations = {
        'timeout': 'Improve retry logic and network stability',
        'payment_error': 'Check payment gateway logs and integrations',
        'auth_failed': 'Validate authentication tokens and sessions',
        'server_error': 'Inspect server logs and CPU usage',
        'db_error': 'Verify DB connection pool and health',
        '500': 'Review application logs for exceptions',
        '502': 'Check backend service health',
        '503': 'Increase capacity or implement auto-scaling',
        '504': 'Optimize slow queries and add caching'
    };
    
    // Extract error distribution - it might be nested in error_type_distribution
    let errorDist = data.error_type_distribution || data;
    
    // If errorDist is still not an object with error codes, show empty state
    if (!errorDist || typeof errorDist !== 'object' || Object.keys(errorDist).length === 0) {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 30px;">No error data available</td></tr>';
        return;
    }
    
    const totalErrors = Object.values(errorDist).reduce((a, b) => a + b, 0);
    
    const rows = Object.entries(errorDist)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([code, count]) => {
            const percentage = totalErrors > 0 ? (count / totalErrors * 100).toFixed(1) : 0;
            const errorType = errorDescriptions[code] || 'Unknown Error';
            const recommendation = recommendations[code] || 'Monitor closely';
            
            return `
                <tr>
                    <td><strong>${code}</strong></td>
                    <td>${errorType}</td>
                    <td>${count.toLocaleString()}</td>
                    <td>${percentage}%</td>
                    <td>${recommendation}</td>
                </tr>
            `;
        });
    
    if (rows.length > 0) {
        tableBody.innerHTML = rows.join('');
    } else {
        tableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 30px;">No error data available</td></tr>';
    }
}

function generateFailureInsights(metrics) {
    const insightsContainer = document.getElementById('failureInsights');
    if (!insightsContainer) return;
    
    const failureRate = metrics.failure_rate;
    const totalTransactions = metrics.total_transactions;
    const failedCount = Math.round(failureRate / 100 * totalTransactions);
    
    let analysisHTML = '';
    
    if (failureRate > 20) {
        analysisHTML = `
            <div style="background: #fee; padding: 15px; border-left: 4px solid #e74c3c; border-radius: 4px; margin-bottom: 20px;">
                <strong style="color: #e74c3c;">🔴 CRITICAL SITUATION</strong><br>
                Your system is experiencing a critically high failure rate of <strong>${failureRate.toFixed(2)}%</strong>.
                This requires immediate attention and investigation.
            </div>
            <p><strong>Key Findings:</strong></p>
            <ul style="padding-left: 20px; line-height: 1.8;">
                <li><strong>${failedCount.toLocaleString()}</strong> out of <strong>${totalTransactions.toLocaleString()}</strong> transactions failed</li>
                <li>System reliability is severely compromised</li>
                <li>User experience is likely severely degraded</li>
                <li>Revenue and reputation impact expected</li>
            </ul>
            <p style="margin-top: 15px;"><strong>Root Causes to Investigate:</strong></p>
            <ul style="padding-left: 20px; line-height: 1.8;">
                <li><strong>Service Overload:</strong> System may be experiencing resource exhaustion</li>
                <li><strong>Database Issues:</strong> Check for connection pool exhaustion or query timeouts</li>
                <li><strong>Recent Deployments:</strong> Review any code changes or configuration updates</li>
                <li><strong>Infrastructure Problems:</strong> Verify network, storage, and compute resources</li>
                <li><strong>External Dependencies:</strong> Check third-party services and APIs</li>
            </ul>
        `;
    } else if (failureRate > 10) {
        analysisHTML = `
            <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #f39c12; border-radius: 4px; margin-bottom: 20px;">
                <strong style="color: #f39c12;">🟡 WARNING - ELEVATED FAILURES</strong><br>
                Failure rate of <strong>${failureRate.toFixed(2)}%</strong> is above acceptable thresholds.
                Monitor closely and investigate trends.
            </div>
            <p><strong>Current Status:</strong></p>
            <ul style="padding-left: 20px; line-height: 1.8;">
                <li><strong>${failedCount.toLocaleString()}</strong> transactions failed in the last 30 days</li>
                <li>System stability is degraded but manageable</li>
                <li>Some users experiencing issues</li>
            </ul>
            <p style="margin-top: 15px;"><strong>Recommended Actions:</strong></p>
            <ul style="padding-left: 20px; line-height: 1.8;">
                <li>Review error logs for patterns and trends</li>
                <li>Check resource utilization (CPU, memory, disk)</li>
                <li>Compare with historical baselines</li>
                <li>Investigate top error codes from distribution table above</li>
                <li>Consider scaling resources if traffic increased</li>
            </ul>
        `;
    } else {
        analysisHTML = `
            <div style="background: #d4edda; padding: 15px; border-left: 4px solid #28a745; border-radius: 4px; margin-bottom: 20px;">
                <strong style="color: #28a745;">🟢 HEALTHY STATUS</strong><br>
                System failure rate is at acceptable levels: <strong>${failureRate.toFixed(2)}%</strong>.
                Continue monitoring and maintain current practices.
            </div>
            <p><strong>System Health Summary:</strong></p>
            <ul style="padding-left: 20px; line-height: 1.8;">
                <li><strong>${failedCount.toLocaleString()}</strong> transactions failed (acceptable level)</li>
                <li><strong>${metrics.success_rate.toFixed(2)}%</strong> success rate</li>
                <li>System performance is within normal parameters</li>
                <li>No immediate action required</li>
            </ul>
            <p style="margin-top: 15px;"><strong>Maintenance Recommendations:</strong></p>
            <ul style="padding-left: 20px; line-height: 1.8;">
                <li>Continue regular monitoring and logging</li>
                <li>Maintain current operational practices</li>
                <li>Review trends weekly to catch early warning signs</li>
                <li>Plan for capacity expansion if growth continues</li>
                <li>Document successful practices for team knowledge</li>
            </ul>
        `;
    }
    
    insightsContainer.innerHTML = analysisHTML;
}

function updateRecommendedActions(metrics) {
    const actionsList = document.getElementById('actionsList');
    if (!actionsList) return;
    
    const failureRate = metrics.failure_rate;
    let actions = [];
    
    if (failureRate > 20) {
        actions = [
            '🚨 Trigger incident response team immediately',
            '📊 Analyze error logs and stack traces urgently',
            '🔄 Consider rolling back recent deployments',
            '📞 Notify stakeholders of system degradation',
            '⚡ Scale resources or implement circuit breakers'
        ];
    } else if (failureRate > 10) {
        actions = [
            '📊 Review application and infrastructure logs',
            '🔍 Investigate top error codes and patterns',
            '📈 Monitor resource utilization trends',
            '🔧 Optimize slow queries and bottlenecks',
            '📋 Schedule deep-dive analysis session'
        ];
    } else {
        actions = [
            '✅ Maintain current monitoring practices',
            '📊 Continue regular log review',
            '🔄 Plan for capacity based on growth trends',
            '📚 Document learnings and best practices',
            '🎯 Focus on preventative maintenance'
        ];
    }
    
    actionsList.innerHTML = actions.map(action => 
        `<li style="padding: 8px 0; border-bottom: 1px solid #eee;">${action}</li>`
    ).join('');
}

function formatTime(seconds) {
    if (!seconds || seconds === 0) return 'N/A';
    if (seconds >= 3600) {
        return (seconds / 3600).toFixed(1) + ' hours';
    } else if (seconds >= 60) {
        return (seconds / 60).toFixed(1) + ' min';
    } else {
        return seconds.toFixed(1) + ' sec';
    }
}

function getSeverity(failureRate) {
    if (failureRate > 20) {
        return { level: 'critical', label: '🔴 CRITICAL' };
    } else if (failureRate > 10) {
        return { level: 'high', label: '🟠 HIGH' };
    } else if (failureRate > 5) {
        return { level: 'medium', label: '🟡 MEDIUM' };
    } else {
        return { level: 'low', label: '🟢 LOW' };
    }
}

function updateMetricExplanation(elementId, explanationText) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = explanationText;
        element.style.display = 'block';
    }
}

function setupFailureActions() {
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', fetchFailureMetrics);
    }
    
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
        });
    });
}

function showErrorMessage(message) {
    const container = document.querySelector('.failures-container') || document.body;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    container.insertBefore(errorDiv, container.firstChild);
    
    setTimeout(() => errorDiv.remove(), 5000);
}

function startFailureAutoRefresh(interval = 30000) {
    fetchFailureMetrics();
    
    if (failureAutoRefresh) {
        clearInterval(failureAutoRefresh);
    }
    
    failureAutoRefresh = setInterval(fetchFailureMetrics, interval);
}

function stopFailureAutoRefresh() {
    if (failureAutoRefresh) {
        clearInterval(failureAutoRefresh);
        failureAutoRefresh = null;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Failure analysis page loaded');
    setupFailureActions();
    fetchFailureMetrics(); // Load data immediately on page load
    startFailureAutoRefresh(30000);
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopFailureAutoRefresh();
});
