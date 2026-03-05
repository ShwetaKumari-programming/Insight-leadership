/**
 * Trends.js - Trends and forecasting page functionality
 * Displays historical trends, anomaly detection, and forecasted metrics
 * Based on UPI transactions (Jan-Dec 2024)
 */

let trendsAutoRefresh = null;
const API_BASE = window.location.port === '5500' ? 'http://127.0.0.1:8001' : '';

function openChatWithQuestion(question) {
    if (!question) return;
    localStorage.setItem('pending_chat_question', question);
    window.location.href = '/chat.html';
}

function bindAskAssistantButtons() {
    const buttons = document.querySelectorAll('.ask-chat-btn');
    buttons.forEach((btn) => {
        btn.onclick = () => {
            const question = btn.getAttribute('data-chat-question') || '';
            openChatWithQuestion(question);
        };
    });
}

async function fetchTrendsMetrics() {
    try {
        const response = await fetch(`${API_BASE}/api/metrics/trends`);
        const data = await response.json();

        if (data.metrics) {
            updateTrendsDisplay(data.metrics);
        }
        if (data.trend_insights) {
            updateTrendInsights(data.trend_insights);
        }
    } catch (error) {
        console.error('Error fetching trends metrics:', error);
        showErrorMessage('Could not load trends metrics. Please try again.');
    }
}

function updateTrendInsights(insights) {
    const trendAnalysis = document.getElementById('trendAnalysis');
    if (trendAnalysis && insights && insights.length > 0) {
        trendAnalysis.innerHTML = insights.map(insight =>
            `<div style="padding: 8px 12px; margin-bottom: 6px; background: rgba(255,255,255,0.05); border-radius: 8px; font-size: 0.95em;">${insight}</div>`
        ).join('');
    }
}

function updateTrendsDisplay(metrics) {
    const trendDirection = document.getElementById('trendDirection');
    const trendStatus = document.getElementById('trendStatus');
    const trendConfidence = document.getElementById('trendConfidence');
    const forecast7d = document.getElementById('forecast7d');
    const anomalyCount = document.getElementById('anomalyCount');
    const trendAnalysis = document.getElementById('trendAnalysis');
    const anomalyTable = document.getElementById('anomalyTable');
    const volumeAnomalyTable = document.getElementById('volumeAnomalyTable');
    const forecast7dSummary = document.getElementById('forecast7dSummary');
    const forecast30dSummary = document.getElementById('forecast30dSummary');
    const updateTime = document.getElementById('updateTime');
    const monthlyTable = document.getElementById('monthlyTable');

    const trend = (metrics.trend || 'stable').toLowerCase();
    const confidence = Math.round((metrics.confidence || 0.75) * 100);

    if (trendDirection) {
        trendDirection.innerText = trend.toUpperCase();
        trendDirection.style.color = trend === 'increasing' ? '#ff5252' : trend === 'decreasing' ? '#4caf50' : '#ffc107';
    }

    if (trendStatus) {
        if (trend === 'increasing') {
            trendStatus.innerHTML = '<span style="color:#ff5252">⚠️ INCREASING</span>';
        } else if (trend === 'decreasing') {
            trendStatus.innerHTML = '<span style="color:#4caf50">✅ IMPROVING</span>';
        } else {
            trendStatus.innerHTML = '<span style="color:#ffc107">🟢 STABLE</span>';
        }
    }

    if (trendConfidence) {
        trendConfidence.innerText = confidence + '%';
    }

    if (forecast7d) {
        forecast7d.innerText = (metrics.forecast_7d || 0).toFixed(2) + '%';
    }

    if (anomalyCount) {
        const count = metrics.anomalies || 0;
        anomalyCount.innerText = count;
        anomalyCount.style.color = count > 5 ? '#ff5252' : count > 0 ? '#ffc107' : '#4caf50';
    }

    if (trendAnalysis) {
        const volatility = metrics.volatility || 0;
        const currentRate = metrics.current_rate || 0;
        const totalTxns = (metrics.total_transactions || 0).toLocaleString();
        const totalFails = (metrics.total_failures || 0).toLocaleString();
        const daysAnalyzed = metrics.days_analyzed || 0;

        trendAnalysis.innerHTML = `
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px;">
                <div style="padding:12px; background:rgba(255,255,255,0.05); border-radius:8px;">
                    <strong style="color:#64b5f6;">📊 Dataset</strong><br>
                    ${totalTxns} transactions analyzed<br>
                    ${daysAnalyzed} days (Jan–Dec 2024)
                </div>
                <div style="padding:12px; background:rgba(255,255,255,0.05); border-radius:8px;">
                    <strong style="color:#ff5252;">🔴 Failures</strong><br>
                    ${totalFails} failed (${currentRate.toFixed(2)}%)<br>
                    Volatility: σ = ${volatility.toFixed(2)}%
                </div>
                <div style="padding:12px; background:rgba(255,255,255,0.05); border-radius:8px;">
                    <strong style="color:#ffc107;">📈 Trend</strong><br>
                    Direction: ${trend.toUpperCase()}<br>
                    Confidence: ${confidence}%
                </div>
                <div style="padding:12px; background:rgba(255,255,255,0.05); border-radius:8px;">
                    <strong style="color:#e040fb;">🔮 Forecast (7d)</strong><br>
                    Predicted rate: ${(metrics.forecast_7d || 0).toFixed(2)}%<br>
                    Anomalies: ${metrics.anomalies || 0} detected
                </div>
            </div>
        `;
    }

    // Failure-rate anomaly table
    if (anomalyTable) {
        const rows = metrics.anomaly_list || [];
        if (rows.length === 0) {
            anomalyTable.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px; color: #4caf50;">✅ No failure-rate anomalies detected in the UPI transaction dataset</td></tr>';
        } else {
            anomalyTable.innerHTML = rows.map(row => `
                <tr>
                    <td>${row.date}</td>
                    <td style="color:#ff5252; font-weight:bold;">${row.failure_rate}%</td>
                    <td>${row.expected}%</td>
                    <td style="color:#ff9800;">${row.deviation}%</td>
                    <td>${row.severity}</td>
                    <td>${(row.failed_txns || 0).toLocaleString()} / ${(row.total_txns || 0).toLocaleString()}</td>
                </tr>
            `).join('');
        }
    }

    // Volume anomaly table
    if (volumeAnomalyTable) {
        const volRows = metrics.volume_anomalies || [];
        if (volRows.length === 0) {
            volumeAnomalyTable.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:30px;color:#4caf50;">✅ No volume anomalies detected</td></tr>';
        } else {
            volumeAnomalyTable.innerHTML = volRows.map(row => `
                <tr>
                    <td>${row.date}</td>
                    <td style="font-weight:bold;">${row.volume.toLocaleString()}</td>
                    <td>${row.expected.toLocaleString()}</td>
                    <td style="color:${row.deviation.startsWith('+') ? '#ff9800' : '#2196f3'};">${row.deviation}</td>
                    <td>${row.type}</td>
                </tr>
            `).join('');
        }
    }

    // Monthly stats table
    if (monthlyTable) {
        const monthlyRows = metrics.monthly_stats || [];
        if (monthlyRows.length > 0) {
            monthlyTable.innerHTML = monthlyRows.map(row => `
                <tr>
                    <td>${row.month}</td>
                    <td>${row.total_transactions.toLocaleString()}</td>
                    <td>${row.failures.toLocaleString()}</td>
                    <td style="color:${row.failure_rate > 5.0 ? '#ff5252' : '#4caf50'}; font-weight:bold;">${row.failure_rate}%</td>
                    <td>${row.fraud_count}</td>
                </tr>
            `).join('');
        }
    }

    if (forecast7dSummary) {
        forecast7dSummary.innerText = trend === 'increasing'
            ? 'Expected to increase. Monitor closely.'
            : trend === 'decreasing'
                ? 'Expected to improve. Keep monitoring.'
                : 'Expected to remain stable.';
    }

    if (forecast30dSummary) {
        forecast30dSummary.innerText = trend === 'increasing'
            ? 'Longer-term risk is rising. Investigate root causes.'
            : trend === 'decreasing'
                ? 'Longer-term outlook is improving.'
                : 'No major shifts expected in the next month.';
    }

    if (updateTime) {
        updateTime.innerText = new Date().toLocaleTimeString();
    }

    // ── Volume Analysis Section ──
    const vol = metrics.volume_analysis;
    if (vol) {
        updateVolumeAnalysis(vol);
    }
}

function fmt(n) {
    return (n || 0).toLocaleString('en-IN');
}

function updateVolumeAnalysis(vol) {
    // Summary cards
    const s = vol.summary || {};
    const el = id => document.getElementById(id);

    if (el('volTotalTxns')) el('volTotalTxns').innerText = fmt(s.total_transactions);
    if (el('volTotalAmount')) el('volTotalAmount').innerText = '₹' + fmt(s.total_amount);
    if (el('volDailyAvg')) el('volDailyAvg').innerText = fmt(Math.round(s.avg_daily_volume));
    if (el('volAvgTxn')) el('volAvgTxn').innerText = '₹' + fmt(s.avg_txn_amount);

    // Hourly volume table
    const hourlyTb = el('hourlyVolumeTable');
    if (hourlyTb) {
        if (vol.hourly && Array.isArray(vol.hourly) && vol.hourly.length > 0) {
            hourlyTb.innerHTML = vol.hourly.map(r => {
                const barWidth = Math.round((r.txn_count / 21232) * 100); // max hourly = ~21232
                return `<tr>
                    <td><strong>${r.label}</strong></td>
                    <td>
                        <div style="display:flex;align-items:center;gap:8px;">
                            <div style="background:linear-gradient(90deg,#64b5f6,#1976d2);height:12px;border-radius:6px;width:${barWidth}%;min-width:4px;"></div>
                            ${fmt(r.txn_count)}
                        </div>
                    </td>
                    <td>₹${fmt(r.total_amount)}</td>
                    <td>₹${fmt(r.avg_amount)}</td>
                    <td>${fmt(r.failures)}</td>
                    <td style="color:${r.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${r.failure_rate}%</td>
                </tr>`;
            }).join('');
        } else {
            console.error('No hourly volume data available:', vol.hourly);
            hourlyTb.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:#999;">No hourly volume data available</td></tr>';
        }
    }

    // Transaction type table
    const txnTypeTb = el('txnTypeVolumeTable');
    if (txnTypeTb && vol.transaction_types) {
        txnTypeTb.innerHTML = vol.transaction_types.map(r => `<tr>
            <td><strong>${r.type}</strong></td>
            <td>${fmt(r.txn_count)}</td>
            <td>${r.pct}%</td>
            <td>₹${fmt(r.total_amount)}</td>
            <td>₹${fmt(r.avg_amount)}</td>
            <td>${fmt(r.failures)}</td>
            <td style="color:${r.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${r.failure_rate}%</td>
        </tr>`).join('');
    }

    // Category table
    const catTb = el('categoryVolumeTable');
    if (catTb && vol.categories) {
        catTb.innerHTML = vol.categories.map(r => `<tr>
            <td><strong>${r.category}</strong></td>
            <td>${fmt(r.txn_count)}</td>
            <td>${r.pct}%</td>
            <td>₹${fmt(r.total_amount)}</td>
            <td>₹${fmt(r.avg_amount)}</td>
            <td>${fmt(r.failures)}</td>
            <td style="color:${r.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${r.failure_rate}%</td>
        </tr>`).join('');
    }

    // Bank table
    const bankTb = el('bankVolumeTable');
    if (bankTb && vol.banks) {
        bankTb.innerHTML = vol.banks.map(r => `<tr>
            <td><strong>${r.bank}</strong></td>
            <td>${fmt(r.txn_count)}</td>
            <td>${r.pct}%</td>
            <td>₹${fmt(r.total_amount)}</td>
            <td>₹${fmt(r.avg_amount)}</td>
            <td>${fmt(r.failures)}</td>
            <td style="color:${r.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${r.failure_rate}%</td>
        </tr>`).join('');
    }

    // State table
    const stateTb = el('stateVolumeTable');
    if (stateTb && vol.states) {
        stateTb.innerHTML = vol.states.map(r => `<tr>
            <td><strong>${r.state}</strong></td>
            <td>${fmt(r.txn_count)}</td>
            <td>${r.pct}%</td>
            <td>₹${fmt(r.total_amount)}</td>
            <td>₹${fmt(r.avg_amount)}</td>
            <td>${fmt(r.failures)}</td>
            <td style="color:${r.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${r.failure_rate}%</td>
        </tr>`).join('');
    }

    // Network table
    const netTb = el('networkVolumeTable');
    if (netTb && vol.networks) {
        netTb.innerHTML = vol.networks.map(r => `<tr>
            <td><strong>${r.network}</strong></td>
            <td>${fmt(r.txn_count)}</td>
            <td>${r.pct}%</td>
            <td>${fmt(r.failures)}</td>
            <td style="color:${r.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${r.failure_rate}%</td>
        </tr>`).join('');
    }

    // Device table
    const devTb = el('deviceVolumeTable');
    if (devTb && vol.devices) {
        devTb.innerHTML = vol.devices.map(r => `<tr>
            <td><strong>${r.device}</strong></td>
            <td>${fmt(r.txn_count)}</td>
            <td>${r.pct}%</td>
            <td>${fmt(r.failures)}</td>
            <td style="color:${r.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${r.failure_rate}%</td>
        </tr>`).join('');
    }

    // Amount distribution table
    const amtTb = el('amountDistTable');
    if (amtTb && vol.amount_distribution) {
        amtTb.innerHTML = vol.amount_distribution.map(r => {
            const barW = Math.round(r.pct * 2.5);
            return `<tr>
                <td><strong>${r.range}</strong></td>
                <td>
                    <div style="display:flex;align-items:center;gap:8px;">
                        <div style="background:linear-gradient(90deg,#ff9800,#f44336);height:12px;border-radius:6px;width:${barW}%;min-width:4px;"></div>
                        ${fmt(r.txn_count)}
                    </div>
                </td>
                <td>${r.pct}%</td>
                <td>${fmt(r.failures)}</td>
                <td style="color:${r.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${r.failure_rate}%</td>
            </tr>`;
        }).join('');
    }

    // Day of week table
    const dowTb = el('dowVolumeTable');
    if (dowTb && vol.day_of_week) {
        dowTb.innerHTML = vol.day_of_week.map(r => `<tr>
            <td><strong>${r.day}</strong></td>
            <td>${fmt(r.txn_count)}</td>
            <td>₹${fmt(r.total_amount)}</td>
            <td>₹${fmt(r.avg_amount)}</td>
            <td>${fmt(r.failures)}</td>
            <td style="color:${r.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${r.failure_rate}%</td>
        </tr>`).join('');
    }

    // Weekend vs Weekday comparison
    const wwComp = el('weekendWeekdayComparison');
    if (wwComp && vol.weekend_vs_weekday) {
        const wd = vol.weekend_vs_weekday.weekday;
        const we = vol.weekend_vs_weekday.weekend;
        wwComp.innerHTML = `
            <table style="width:100%;border-collapse:collapse;">
                <tr><th></th><th style="padding:6px;">Weekday</th><th style="padding:6px;">Weekend</th></tr>
                <tr><td style="padding:6px;color:#aaa;">Transactions</td><td style="padding:6px;font-weight:bold;">${fmt(wd.txn_count)}</td><td style="padding:6px;font-weight:bold;">${fmt(we.txn_count)}</td></tr>
                <tr><td style="padding:6px;color:#aaa;">Total Amount</td><td style="padding:6px;">₹${fmt(wd.total_amount)}</td><td style="padding:6px;">₹${fmt(we.total_amount)}</td></tr>
                <tr><td style="padding:6px;color:#aaa;">Avg Amount</td><td style="padding:6px;">₹${fmt(wd.avg_amount)}</td><td style="padding:6px;">₹${fmt(we.avg_amount)}</td></tr>
                <tr><td style="padding:6px;color:#aaa;">Failures</td><td style="padding:6px;">${fmt(wd.failures)}</td><td style="padding:6px;">${fmt(we.failures)}</td></tr>
                <tr><td style="padding:6px;color:#aaa;">Failure Rate</td>
                    <td style="padding:6px;color:${wd.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${wd.failure_rate}%</td>
                    <td style="padding:6px;color:${we.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${we.failure_rate}%</td></tr>
            </table>`;
    }

    // Peak vs Off-Peak comparison
    const poComp = el('peakOffpeakComparison');
    if (poComp && vol.peak_vs_offpeak) {
        const pk = vol.peak_vs_offpeak.peak;
        const op = vol.peak_vs_offpeak.offpeak;
        poComp.innerHTML = `
            <table style="width:100%;border-collapse:collapse;">
                <tr><th></th><th style="padding:6px;">Peak (9–6PM)</th><th style="padding:6px;">Off-Peak</th></tr>
                <tr><td style="padding:6px;color:#aaa;">Transactions</td><td style="padding:6px;font-weight:bold;">${fmt(pk.txn_count)} (${pk.pct}%)</td><td style="padding:6px;font-weight:bold;">${fmt(op.txn_count)} (${op.pct}%)</td></tr>
                <tr><td style="padding:6px;color:#aaa;">Total Amount</td><td style="padding:6px;">₹${fmt(pk.total_amount)}</td><td style="padding:6px;">₹${fmt(op.total_amount)}</td></tr>
                <tr><td style="padding:6px;color:#aaa;">Failures</td><td style="padding:6px;">${fmt(pk.failures)}</td><td style="padding:6px;">${fmt(op.failures)}</td></tr>
                <tr><td style="padding:6px;color:#aaa;">Failure Rate</td>
                    <td style="padding:6px;color:${pk.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${pk.failure_rate}%</td>
                    <td style="padding:6px;color:${op.failure_rate > 5 ? '#ff5252' : '#4caf50'};font-weight:bold;">${op.failure_rate}%</td></tr>
            </table>`;
    }
}

function setupTrendsActions() {
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', fetchTrendsMetrics);
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
    const container = document.querySelector('.trends-container') || document.body;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    container.insertBefore(errorDiv, container.firstChild);
    
    setTimeout(() => errorDiv.remove(), 5000);
}

function startTrendsAutoRefresh(interval = 30000) {
    fetchTrendsMetrics();
    
    if (trendsAutoRefresh) {
        clearInterval(trendsAutoRefresh);
    }
    
    trendsAutoRefresh = setInterval(fetchTrendsMetrics, interval);
}

function stopTrendsAutoRefresh() {
    if (trendsAutoRefresh) {
        clearInterval(trendsAutoRefresh);
        trendsAutoRefresh = null;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Trends page loaded');
    setupTrendsActions();
    bindAskAssistantButtons();
    startTrendsAutoRefresh(60000);
});

// Cleanup
window.addEventListener('beforeunload', function() {
    stopTrendsAutoRefresh();
});
