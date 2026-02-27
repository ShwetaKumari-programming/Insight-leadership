/**
 * Weekend.js - Weekend vs Weekday analysis page functionality
 * Compares metrics between weekends and weekdays
 */

let weekendAutoRefresh = null;

async function fetchWeekendMetrics() {
    try {
        console.log('Fetching weekend metrics...');
        const response = await fetch('/api/metrics/weekend');
        const data = await response.json();

        if (data.metrics) {
            updateWeekendDisplay(data.metrics);
        }
        // Update root cause analysis and recommendations
        if (data.root_cause_analysis) {
            updateRootCauseAnalysis(data.root_cause_analysis);
        }
    // Update the root cause analysis and recommendations section
    function updateRootCauseAnalysis(rootCauseData) {
        const rootCauseEl = document.getElementById('rootCauseAnalysis');
        if (!rootCauseEl) return;

        let html = '';
        // Add summary if available
        if (rootCauseData.summary) {
            html += `<div style="margin-bottom: 12px; color: #b39ddb;"><strong>Summary:</strong><br>`;
            for (const [key, value] of Object.entries(rootCauseData.summary)) {
                html += `<div><span style='color:#fff;'>${key.replace(/_/g, ' ')}:</span> <span style='color:#ffd54f;'>${value}</span></div>`;
            }
            html += '</div>';
        }
        // Add insights if available
        if (rootCauseData.insights && rootCauseData.insights.length > 0) {
            html += `<div style="margin-bottom: 8px;"><strong>Insights & Recommendations:</strong><ul style='margin: 8px 0 0 18px;'>`;
            for (const insight of rootCauseData.insights) {
                html += `<li style='color:#fff;'>${insight}</li>`;
            }
            html += '</ul></div>';
        }
        if (!html) {
            html = `<p style='color:#999; text-align:center;'>No root cause analysis available.</p>`;
        }
        rootCauseEl.innerHTML = html;
    }
    } catch (error) {
        console.error('Error fetching weekend metrics:', error);
        showErrorMessage('Could not load weekend metrics. Please try again.');
    }
}

function updateWeekendDisplay(metrics) {
    // Update weekend failure rate card
    const weekendFailureEl = document.getElementById('weekendFailure');
    if (weekendFailureEl) {
        weekendFailureEl.textContent = metrics.weekend_failure_rate.toFixed(2) + '%';
        const explanation = `Weekends show a ${metrics.weekend_failure_rate.toFixed(2)}% transaction failure rate. This is higher than weekdays (${metrics.weekday_failure_rate.toFixed(2)}%), often due to reduced operational support and monitoring during off-hours.`;
        updateMetricExplanation('weekendFailureExplanation', explanation);
    }
    
    // Update weekday failure rate card
    const weekdayFailureEl = document.getElementById('weekdayFailure');
    if (weekdayFailureEl) {
        weekdayFailureEl.textContent = metrics.weekday_failure_rate.toFixed(2) + '%';
        const explanation = `Weekdays have a ${metrics.weekday_failure_rate.toFixed(2)}% transaction failure rate. This is lower than weekends, as there is more active operational support and automated monitoring in place.`;
        updateMetricExplanation('weekdayFailureExplanation', explanation);
    }
    
    // Update failure ratio
    const failureRatioEl = document.getElementById('failureRatio');
    if (failureRatioEl) {
        failureRatioEl.textContent = metrics.weekend_ratio.toFixed(2) + 'x';
        const explanation = `Weekend failures are ${metrics.weekend_ratio.toFixed(2)} times higher than weekdays. This multiplier indicates the severity of the weekend issue and helps prioritize mitigation efforts.`;
        updateMetricExplanation('failureRatioExplanation', explanation);
    }
    
    // Update ratio status
    const ratioStatusEl = document.getElementById('ratioStatus');
    if (ratioStatusEl) {
        let status = '🟢 Normal';
        if (metrics.weekend_ratio > 2) {
            status = '🔴 Critical - Weekend failures much higher';
        } else if (metrics.weekend_ratio > 1.5) {
            status = '🟠 Warning - Weekend failures higher';
        } else if (metrics.weekend_ratio > 1) {
            status = '🟡 Elevated - Slightly higher on weekends';
        }
        ratioStatusEl.innerHTML = `<div style="font-size: 0.85em; margin-top: 5px;">${status}</div>`;
    }
    
    // Update difference
    const failureDiffEl = document.getElementById('failureDiff');
    if (failureDiffEl) {
        const difference = metrics.weekend_failure_rate - metrics.weekday_failure_rate;
        failureDiffEl.textContent = difference.toFixed(2) + '%';
        const explanation = `The absolute difference between weekend and weekday failure rates is ${difference.toFixed(2)} percentage points. This shows the baseline impact of reduced operations on weekends.`;
        updateMetricExplanation('failureDiffExplanation', explanation);
    }
    
    // Update comparison table
    updateComparisonTable(metrics);
    
    // Update error distributions
    updateErrorComparison(metrics);
}

function updateMetricExplanation(elementId, explanationText) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = explanationText;
        element.style.display = 'block';
    }
}

function updateComparisonTable(metrics) {
    const comparisonTableEl = document.getElementById('comparisonTable');
    if (!comparisonTableEl) return;
    
    const rows = [
        {
            metric: 'Weekend Failure Rate',
            value: metrics.weekend_failure_rate.toFixed(2) + '%',
            meaning: metrics.weekend_failure_rate > 5 ? 'Higher failures due to low monitoring & deployments' : 'Moderate failure rate'
        },
        {
            metric: 'Weekday Failure Rate',
            value: metrics.weekday_failure_rate.toFixed(2) + '%',
            meaning: 'Stable due to active teams'
        },
        {
            metric: 'Failure Ratio',
            value: metrics.weekend_ratio.toFixed(2) + '×',
            meaning: `Weekend failures are ~${metrics.weekend_ratio.toFixed(1)} times higher`
        },
        {
            metric: 'Difference',
            value: (metrics.weekend_failure_rate - metrics.weekday_failure_rate).toFixed(2) + '%',
            meaning: `${metrics.weekend_failure_rate > metrics.weekday_failure_rate ? '+' : ''}${(metrics.weekend_failure_rate - metrics.weekday_failure_rate).toFixed(1)}% reliability gap`
        },
        {
            metric: 'Weekend Transactions',
            value: metrics.weekend_transactions.toLocaleString(),
            meaning: `Total requests processed on weekends`
        },
        {
            metric: 'Weekday Transactions',
            value: metrics.weekday_transactions.toLocaleString(),
            meaning: `Total requests processed on weekdays`
        },
        {
            metric: 'Weekend Failures',
            value: metrics.weekend_failures.toLocaleString(),
            meaning: `Failed requests out of ${metrics.weekend_transactions.toLocaleString()} weekend requests`
        },
        {
            metric: 'Weekday Failures',
            value: metrics.weekday_failures.toLocaleString(),
            meaning: `Failed requests out of ${metrics.weekday_transactions.toLocaleString()} weekday requests`
        }
    ];
    
    const html = rows.map(row => `
        <tr>
            <td><strong>${row.metric}</strong></td>
            <td style="text-align: center; font-weight: bold; color: #3498db;">${row.value}</td>
            <td style="color: #ecf0f1;">${row.meaning}</td>
        </tr>
    `).join('');
    
    comparisonTableEl.innerHTML = html;
}

function updateErrorComparison(metrics) {
    const weekendErrorsEl = document.getElementById('weekendErrors');
    const weekdayErrorsEl = document.getElementById('weekdayErrors');
    
    if (weekendErrorsEl) {
        weekendErrorsEl.innerHTML = generateErrorDistributionHTML(metrics.weekend_error_dist || []);
    }
    
    if (weekdayErrorsEl) {
        weekdayErrorsEl.innerHTML = generateErrorDistributionHTML(metrics.weekday_error_dist || []);
    }
}

function generateErrorDistributionHTML(errorDist) {
    if (!errorDist || errorDist.length === 0) {
        return '<p style="color: #999;">No error data available</p>';
    }
    
    const errorDescriptions = {
        'timeout': 'Network Timeout',
        'payment_error': 'Payment Gateway Failure',
        'auth_failed': 'Authentication Error',
        'server_error': 'Internal Server Error',
        'db_error': 'Database Connection Failure',
        'NET_TIMEOUT': 'Network Timeout',
        'PAY_FAILED': 'Payment Gateway Failure',
        'AUTH_ERR': 'Authentication Error',
        'SERVER_ERR': 'Internal Server Error',
        'DB_CONN': 'Database Connection Failure',
        '500': 'Internal Server Error',
        '502': 'Bad Gateway',
        '503': 'Service Unavailable',
        '504': 'Gateway Timeout'
    };
    
    let html = '';
    errorDist.forEach(([code, percentage]) => {
        const description = errorDescriptions[code] || 'Unknown Error';
        html += `
            <div style="margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span><strong>${code}:</strong> ${description}</span>
                    <span style="color: #3498db; font-weight: bold;">${percentage.toFixed(1)}%</span>
                </div>
                <div style="background: #2c3e50; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 4px;">
                    <div style="background: linear-gradient(90deg, #3498db, #2980b9); width: ${percentage}%; height: 100%;"></div>
                </div>
            </div>
        `;
    });
    
    return html;
}

function setupWeekendActions() {
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', fetchWeekendMetrics);
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
    const container = document.querySelector('.weekend-container') || document.body;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    container.insertBefore(errorDiv, container.firstChild);
    
    setTimeout(() => errorDiv.remove(), 5000);
}

function startWeekendAutoRefresh(interval = 30000) {
    fetchWeekendMetrics();
    
    if (weekendAutoRefresh) {
        clearInterval(weekendAutoRefresh);
    }
    
    weekendAutoRefresh = setInterval(fetchWeekendMetrics, interval);
}

function stopWeekendAutoRefresh() {
    if (weekendAutoRefresh) {
        clearInterval(weekendAutoRefresh);
        weekendAutoRefresh = null;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Weekend analysis page loaded');
    setupWeekendActions();
    startWeekendAutoRefresh(30000);
});

// Cleanup
window.addEventListener('beforeunload', function() {
    stopWeekendAutoRefresh();
});

function setupWeekendActions() {
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', fetchWeekendMetrics);
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
    const container = document.querySelector('.weekend-container') || document.body;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    container.insertBefore(errorDiv, container.firstChild);
    
    setTimeout(() => errorDiv.remove(), 5000);
}

function startWeekendAutoRefresh(interval = 30000) {
    fetchWeekendMetrics();
    
    if (weekendAutoRefresh) {
        clearInterval(weekendAutoRefresh);
    }
    
    weekendAutoRefresh = setInterval(fetchWeekendMetrics, interval);
}

function stopWeekendAutoRefresh() {
    if (weekendAutoRefresh) {
        clearInterval(weekendAutoRefresh);
        weekendAutoRefresh = null;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Weekend analysis page loaded');
    setupWeekendActions();
    startWeekendAutoRefresh(30000);
});

// Cleanup
window.addEventListener('beforeunload', function() {
    stopWeekendAutoRefresh();
});
