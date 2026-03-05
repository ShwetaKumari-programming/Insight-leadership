/**
 * Dashboard.js - Main dashboard page functionality
 * Fetches metrics from the backend and displays them
 */

let autoRefreshInterval = null;
const API_BASE = window.location.port === '5500' ? 'http://127.0.0.1:8001' : '';

async function fetchDashboardMetrics() {
    try {
        console.log('Fetching dashboard metrics...');
        const response = await fetch(`${API_BASE}/api/metrics/dashboard`);
        const data = await response.json();
        
        if (data.metrics) {
            updateDashboardDisplay(data.metrics);
        }
    } catch (error) {
        console.error('Error fetching metrics:', error);
        showErrorMessage('Could not load metrics. Please try again.');
    }
}

function updateDashboardDisplay(metrics) {
    // Update quick stat cards using IDs
    const failureRateElement = document.getElementById('failureRate');
    const latencyElement = document.getElementById('avgLatency');
    const transactionsElement = document.getElementById('totalTransactions');
    const weekendRatioElement = document.getElementById('weekendRatio');
    
    if (failureRateElement) {
        failureRateElement.textContent = metrics.failure_rate.toFixed(2) + '%';
    }
    
    if (latencyElement) {
        latencyElement.textContent = Math.round(metrics.avg_latency) + 'ms';
    }
    
    if (transactionsElement) {
        transactionsElement.textContent = metrics.total_transactions.toLocaleString();
    }
    
    if (weekendRatioElement) {
        weekendRatioElement.textContent = metrics.weekend_ratio.toFixed(2) + 'x';
    }

    // Update footer data count dynamically
    const footerCount = document.getElementById('footerDataCount');
    if (footerCount && metrics.total_transactions) {
        footerCount.textContent = metrics.total_transactions.toLocaleString();
    }
    
    // Update status badges
    updateStatusBadges(metrics);
    
    // Update metrics table with real data
    updateMetricsTable(metrics);
}

function updateStatusBadges(metrics) {
    // Update failure status
    const failureStatus = document.getElementById('failureStatus');
    if (failureStatus) {
        if (metrics.failure_rate > 15) {
            failureStatus.innerHTML = '<span class="status-badge status-critical">⚠️ CRITICAL</span>';
        } else if (metrics.failure_rate > 10) {
            failureStatus.innerHTML = '<span class="status-badge status-warning">⚠️ WARNING</span>';
        } else {
            failureStatus.innerHTML = '<span class="status-badge status-healthy">✅ HEALTHY</span>';
        }
    }
    
    // Update latency status
    const latencyStatus = document.getElementById('latencyStatus');
    if (latencyStatus) {
        if (metrics.avg_latency > 500) {
            latencyStatus.innerHTML = '<span class="status-badge status-warning">⚠️ SLOW</span>';
        } else {
            latencyStatus.innerHTML = '<span class="status-badge status-healthy">✅ FAST</span>';
        }
    }
    
    // Update weekend status
    const weekendStatus = document.getElementById('weekendStatus');
    if (weekendStatus) {
        if (metrics.weekend_ratio > 2.5) {
            weekendStatus.innerHTML = '<span class="status-badge status-critical">🔴 CRITICAL</span>';
        } else if (metrics.weekend_ratio > 1.5) {
            weekendStatus.innerHTML = '<span class="status-badge status-warning">⚠️ ELEVATED</span>';
        } else {
            weekendStatus.innerHTML = '<span class="status-badge status-healthy">✅ NORMAL</span>';
        }
    }
}

function updateMetricsTable(metrics) {
    const tableBody = document.getElementById('metricsTable');
    if (!tableBody) return;
    
    const now = new Date().toLocaleTimeString();
    
    const rows = [
        {
            metric: 'Failure Rate',
            value: metrics.failure_rate.toFixed(2) + '%',
            status: getStatus(metrics.failure_rate, [10, 15]),
            updated: now
        },
        {
            metric: 'Average Latency',
            value: Math.round(metrics.avg_latency) + 'ms',
            status: getLatencyStatus(metrics.avg_latency),
            updated: now
        },
        {
            metric: 'P95 Latency',
            value: Math.round(metrics.p95_latency) + 'ms',
            status: getLatencyStatus(metrics.p95_latency),
            updated: now
        },
        {
            metric: 'Success Rate',
            value: metrics.success_rate.toFixed(2) + '%',
            status: getSuccessStatus(metrics.success_rate),
            updated: now
        },
        {
            metric: 'Total Transactions',
            value: metrics.total_transactions.toLocaleString(),
            status: '✅ OK',
            updated: now
        },
        {
            metric: 'Weekend Ratio',
            value: metrics.weekend_ratio.toFixed(2) + 'x',
            status: getStatus(metrics.weekend_ratio, [1.5, 2.5]),
            updated: now
        },
        {
            metric: 'MTBF',
            value: formatTime(metrics.mtbf),
            status: '✅ OK',
            updated: now
        },
        {
            metric: 'MTTR',
            value: formatTime(metrics.mttr),
            status: '✅ OK',
            updated: now
        }
    ];
    
    tableBody.innerHTML = rows.map(row => `
        <tr>
            <td><strong>${row.metric}</strong></td>
            <td>${row.value}</td>
            <td>${row.status}</td>
            <td>${row.updated}</td>
        </tr>
    `).join('');
}

function getStatus(value, thresholds) {
    if (value > thresholds[1]) return '🔴 CRITICAL';
    if (value > thresholds[0]) return '🟡 WARNING';
    return '🟢 HEALTHY';
}

function getLatencyStatus(latency) {
    if (latency > 500) return '🔴 VERY SLOW';
    if (latency > 300) return '🟡 SLOW';
    if (latency > 100) return '🟢 ACCEPTABLE';
    return '🟢 FAST';
}

function getSuccessStatus(rate) {
    if (rate >= 99) return '🟢 EXCELLENT';
    if (rate >= 95) return '🟢 GOOD';
    if (rate >= 90) return '🟡 ACCEPTABLE';
    return '🔴 POOR';
}

function formatTime(seconds) {
    if (seconds >= 3600) {
        return (seconds / 3600).toFixed(1) + 'h';
    } else if (seconds >= 60) {
        return (seconds / 60).toFixed(1) + 'min';
    } else {
        return seconds.toFixed(1) + 's';
    }
}

function setupNavigationListeners() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            // Remove active class from all
            navItems.forEach(nav => nav.classList.remove('active'));
            // Add active class to clicked item
            item.classList.add('active');
            // Navigate to page
            const href = item.getAttribute('href');
            if (href) {
                navigateTo(href);
            }
        });
    });
}

function navigateTo(page) {
    window.location.href = page;
}

function showErrorMessage(message) {
    const container = document.querySelector('.dashboard-container') || document.body;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    container.insertBefore(errorDiv, container.firstChild);
    
    setTimeout(() => errorDiv.remove(), 5000);
}

function startAutoRefresh(interval = 30000) {
    // Fetch immediately
    fetchDashboardMetrics();
    
    // Then refresh at interval
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    autoRefreshInterval = setInterval(fetchDashboardMetrics, interval);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard page loaded');
    setupNavigationListeners();
    startAutoRefresh(30000); // Refresh every 30 seconds
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});
