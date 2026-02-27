/**
 * Performance.js - Performance metrics page functionality
 * Deep analysis of UPI transactions (2024 dataset)
 * Displays latency, throughput, APDEX, device/network/bank/state/category breakdowns
 */

let performanceAutoRefresh = null;

async function fetchPerformanceMetrics() {
    try {
        const response = await fetch('/api/performance');
        const data = await response.json();

        if (data.message) {
            return;
        }

        updatePerformanceDisplay(data);
        renderPerformanceAnalysis(data);
    } catch (error) {
        console.error('Error fetching performance metrics:', error);
        showErrorMessage('Could not load performance metrics. Please try again.');
    }
}

function updatePerformanceDisplay(data) {
    const avgLatency = document.getElementById('avg-latency');
    const p95Latency = document.getElementById('p95-latency');
    const p99Latency = document.getElementById('p99-latency');
    const maxLatency = document.getElementById('max-latency');
    const throughput = document.getElementById('throughput');
    const successRate = document.getElementById('success-rate');
    const apdex = document.getElementById('apdex');
    const updateTime = document.getElementById('updateTime');

    if (avgLatency) avgLatency.innerText = data.average_latency + ' ms';
    if (p95Latency) p95Latency.innerText = data.p95_latency + ' ms';
    if (p99Latency) p99Latency.innerText = data.p99_latency + ' ms';
    if (maxLatency) maxLatency.innerText = data.max_latency + ' ms';
    if (throughput) throughput.innerText = data.throughput + ' req/min';
    if (successRate) successRate.innerText = data.success_rate + '%';
    if (apdex) apdex.innerText = data.apdex;
    if (updateTime) updateTime.innerText = new Date().toLocaleTimeString();

    // Update status badges
    const latencyStatus = document.getElementById('latencyStatus');
    if (latencyStatus) {
        if (data.average_latency < 100) {
            latencyStatus.innerHTML = '<span style="color: #28a745; font-weight: bold;">✅ FAST</span>';
        } else if (data.average_latency < 300) {
            latencyStatus.innerHTML = '<span style="color: #f39c12; font-weight: bold;">⚠️ MODERATE</span>';
        } else {
            latencyStatus.innerHTML = '<span style="color: #e74c3c; font-weight: bold;">🔴 SLOW</span>';
        }
    }

    const apdexStatus = document.getElementById('apdexStatus');
    if (apdexStatus) {
        if (data.apdex >= 0.94) {
            apdexStatus.innerHTML = '<span style="color: #28a745; font-weight: bold;">✅ EXCELLENT</span>';
        } else if (data.apdex >= 0.85) {
            apdexStatus.innerHTML = '<span style="color: #28a745; font-weight: bold;">✅ GOOD</span>';
        } else if (data.apdex >= 0.70) {
            apdexStatus.innerHTML = '<span style="color: #f39c12; font-weight: bold;">⚠️ FAIR</span>';
        } else {
            apdexStatus.innerHTML = '<span style="color: #e74c3c; font-weight: bold;">🔴 POOR</span>';
        }
    }

    updateLatencyTable(data.latency_distribution || []);
}

function updateLatencyTable(rows) {
    const tableBody = document.getElementById('latency-table');
    if (!tableBody) return;

    tableBody.innerHTML = rows.map(row => {
        const statusColor = row.status === 'Healthy' ? '#28a745' : row.status === 'Warning' ? '#f39c12' : '#e74c3c';
        const pctText = row.pct !== undefined ? ` (${row.pct}%)` : '';
        return `
        <tr>
            <td>${row.metric}</td>
            <td><strong>${Number(row.value).toLocaleString()}</strong>${pctText}</td>
            <td><span style="color: ${statusColor}; font-weight: bold;">${row.status}</span></td>
            <td>${row.trend}</td>
        </tr>
    `;}).join('');
}

// ══════════════════════════════════════════════════════════
// MAIN PERFORMANCE ANALYSIS RENDERER
// Builds comprehensive analysis from UPI transactions
// ══════════════════════════════════════════════════════════
function renderPerformanceAnalysis(data) {
    const container = document.getElementById('performanceAnalysis');
    if (!container) return;

    const analysis = data.analysis || {};
    const health = analysis.health_assessment || {};
    let html = '';

    // ── 1. Overall Health Assessment ──
    const healthColors = { green: '#28a745', orange: '#f39c12', red: '#e74c3c' };
    const healthIcons = { EXCELLENT: '🟢', GOOD: '🟢', FAIR: '🟡', POOR: '🔴' };
    const hColor = healthColors[health.color] || '#28a745';
    const hIcon = healthIcons[health.status] || '🟢';

    html += `
        <div style="background: ${hColor}15; padding: 20px; border-left: 4px solid ${hColor}; border-radius: 8px; margin-bottom: 25px;">
            <strong style="color: ${hColor}; font-size: 1.15em;">${hIcon} ${health.status || 'HEALTHY'} — Performance Assessment</strong>
            <p style="margin: 10px 0 0; color: #ddd; line-height: 1.7;">${health.message || ''}</p>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 25px;">
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; text-align: center;">
                <div style="color: #999; font-size: 0.85em;">Total Analyzed</div>
                <div style="color: #00bcd4; font-size: 1.5em; font-weight: bold;">${(data.total_transactions || 0).toLocaleString()}</div>
            </div>
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; text-align: center;">
                <div style="color: #999; font-size: 0.85em;">Successful</div>
                <div style="color: #28a745; font-size: 1.5em; font-weight: bold;">${(data.total_success || 0).toLocaleString()}</div>
            </div>
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; text-align: center;">
                <div style="color: #999; font-size: 0.85em;">Failed</div>
                <div style="color: #e74c3c; font-size: 1.5em; font-weight: bold;">${(data.total_failures || 0).toLocaleString()}</div>
            </div>
            <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; text-align: center;">
                <div style="color: #999; font-size: 0.85em;">Median Latency</div>
                <div style="color: #f39c12; font-size: 1.5em; font-weight: bold;">${data.median_latency || '-'} ms</div>
            </div>
        </div>
    `;

    // ── 2. Device Performance ──
    if (analysis.device_performance && analysis.device_performance.length > 0) {
        html += `<h3 style="color: #00bcd4; margin: 30px 0 15px; border-bottom: 1px solid rgba(0,188,212,0.3); padding-bottom: 8px;">📱 Device Type Performance</h3>`;
        html += `<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead><tr style="background: rgba(255,255,255,0.05);">
                <th style="padding: 10px; text-align: left; color: #aaa;">Device</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Transactions</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Share</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Avg Latency</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">P95 Latency</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Success Rate</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Failures</th>
            </tr></thead><tbody>`;
        analysis.device_performance.forEach(d => {
            const srColor = d.success_rate >= 95 ? '#28a745' : d.success_rate >= 90 ? '#f39c12' : '#e74c3c';
            html += `<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 10px; font-weight: bold;">${getDeviceIcon(d.device)} ${d.device}</td>
                <td style="padding: 10px; text-align: right;">${d.count.toLocaleString()}</td>
                <td style="padding: 10px; text-align: right;">${d.pct}%</td>
                <td style="padding: 10px; text-align: right;">${d.avg_latency} ms</td>
                <td style="padding: 10px; text-align: right;">${d.p95_latency} ms</td>
                <td style="padding: 10px; text-align: right; color: ${srColor}; font-weight: bold;">${d.success_rate}%</td>
                <td style="padding: 10px; text-align: right; color: #e74c3c;">${d.failure_count.toLocaleString()}</td>
            </tr>`;
        });
        html += `</tbody></table>`;
    }

    // ── 3. Network Type Performance ──
    if (analysis.network_performance && analysis.network_performance.length > 0) {
        html += `<h3 style="color: #00bcd4; margin: 30px 0 15px; border-bottom: 1px solid rgba(0,188,212,0.3); padding-bottom: 8px;">🌐 Network Type Performance</h3>`;
        html += `<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead><tr style="background: rgba(255,255,255,0.05);">
                <th style="padding: 10px; text-align: left; color: #aaa;">Network</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Transactions</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Share</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Avg Latency</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">P95 Latency</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Success Rate</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Failures</th>
            </tr></thead><tbody>`;
        analysis.network_performance.forEach(n => {
            const srColor = n.success_rate >= 95 ? '#28a745' : n.success_rate >= 90 ? '#f39c12' : '#e74c3c';
            html += `<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 10px; font-weight: bold;">${getNetworkIcon(n.network)} ${n.network}</td>
                <td style="padding: 10px; text-align: right;">${n.count.toLocaleString()}</td>
                <td style="padding: 10px; text-align: right;">${n.pct}%</td>
                <td style="padding: 10px; text-align: right;">${n.avg_latency} ms</td>
                <td style="padding: 10px; text-align: right;">${n.p95_latency} ms</td>
                <td style="padding: 10px; text-align: right; color: ${srColor}; font-weight: bold;">${n.success_rate}%</td>
                <td style="padding: 10px; text-align: right; color: #e74c3c;">${n.failure_count.toLocaleString()}</td>
            </tr>`;
        });
        html += `</tbody></table>`;
    }

    // ── 4. Category/Merchant Performance ──
    if (analysis.category_performance && analysis.category_performance.length > 0) {
        html += `<h3 style="color: #00bcd4; margin: 30px 0 15px; border-bottom: 1px solid rgba(0,188,212,0.3); padding-bottom: 8px;">🏷️ Merchant Category Performance</h3>`;
        html += `<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead><tr style="background: rgba(255,255,255,0.05);">
                <th style="padding: 10px; text-align: left; color: #aaa;">Category</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Transactions</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Share</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Avg Latency</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Success Rate</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Failures</th>
            </tr></thead><tbody>`;
        analysis.category_performance.forEach(c => {
            const srColor = c.success_rate >= 95 ? '#28a745' : c.success_rate >= 90 ? '#f39c12' : '#e74c3c';
            html += `<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 10px; font-weight: bold;">${getCategoryIcon(c.category)} ${c.category}</td>
                <td style="padding: 10px; text-align: right;">${c.count.toLocaleString()}</td>
                <td style="padding: 10px; text-align: right;">${c.pct}%</td>
                <td style="padding: 10px; text-align: right;">${c.avg_latency} ms</td>
                <td style="padding: 10px; text-align: right; color: ${srColor}; font-weight: bold;">${c.success_rate}%</td>
                <td style="padding: 10px; text-align: right; color: #e74c3c;">${c.failure_count.toLocaleString()}</td>
            </tr>`;
        });
        html += `</tbody></table>`;
    }

    // ── 5. Bank Performance (Top 10) ──
    if (analysis.bank_performance && analysis.bank_performance.length > 0) {
        html += `<h3 style="color: #00bcd4; margin: 30px 0 15px; border-bottom: 1px solid rgba(0,188,212,0.3); padding-bottom: 8px;">🏦 Bank Performance (Top 10 by Volume)</h3>`;
        html += `<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead><tr style="background: rgba(255,255,255,0.05);">
                <th style="padding: 10px; text-align: left; color: #aaa;">Bank</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Transactions</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Share</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Avg Latency</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Success Rate</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Failures</th>
            </tr></thead><tbody>`;
        analysis.bank_performance.forEach(b => {
            const srColor = b.success_rate >= 95 ? '#28a745' : b.success_rate >= 90 ? '#f39c12' : '#e74c3c';
            html += `<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 10px; font-weight: bold;">🏦 ${b.bank}</td>
                <td style="padding: 10px; text-align: right;">${b.count.toLocaleString()}</td>
                <td style="padding: 10px; text-align: right;">${b.pct}%</td>
                <td style="padding: 10px; text-align: right;">${b.avg_latency} ms</td>
                <td style="padding: 10px; text-align: right; color: ${srColor}; font-weight: bold;">${b.success_rate}%</td>
                <td style="padding: 10px; text-align: right; color: #e74c3c;">${b.failure_count.toLocaleString()}</td>
            </tr>`;
        });
        html += `</tbody></table>`;
    }

    // ── 6. State/Region Performance (Top 10) ──
    if (analysis.state_performance && analysis.state_performance.length > 0) {
        html += `<h3 style="color: #00bcd4; margin: 30px 0 15px; border-bottom: 1px solid rgba(0,188,212,0.3); padding-bottom: 8px;">📍 State/Region Performance (Top 10)</h3>`;
        html += `<table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead><tr style="background: rgba(255,255,255,0.05);">
                <th style="padding: 10px; text-align: left; color: #aaa;">State</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Transactions</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Share</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Avg Latency</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Success Rate</th>
                <th style="padding: 10px; text-align: right; color: #aaa;">Failures</th>
            </tr></thead><tbody>`;
        analysis.state_performance.forEach(s => {
            const srColor = s.success_rate >= 95 ? '#28a745' : s.success_rate >= 90 ? '#f39c12' : '#e74c3c';
            html += `<tr style="border-bottom: 1px solid rgba(255,255,255,0.05);">
                <td style="padding: 10px; font-weight: bold;">📍 ${s.state}</td>
                <td style="padding: 10px; text-align: right;">${s.count.toLocaleString()}</td>
                <td style="padding: 10px; text-align: right;">${s.pct}%</td>
                <td style="padding: 10px; text-align: right;">${s.avg_latency} ms</td>
                <td style="padding: 10px; text-align: right; color: ${srColor}; font-weight: bold;">${s.success_rate}%</td>
                <td style="padding: 10px; text-align: right; color: #e74c3c;">${s.failure_count.toLocaleString()}</td>
            </tr>`;
        });
        html += `</tbody></table>`;
    }

    // ── 7. Age Group Performance ──
    if (analysis.age_group_performance && analysis.age_group_performance.length > 0) {
        html += `<h3 style="color: #00bcd4; margin: 30px 0 15px; border-bottom: 1px solid rgba(0,188,212,0.3); padding-bottom: 8px;">👤 Age Group Performance</h3>`;
        html += `<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">`;
        analysis.age_group_performance.forEach(a => {
            const srColor = a.success_rate >= 95 ? '#28a745' : a.success_rate >= 90 ? '#f39c12' : '#e74c3c';
            html += `
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px;">
                    <div style="font-weight: bold; color: #00bcd4; margin-bottom: 8px;">👤 ${a.age_group}</div>
                    <div style="color: #ddd; font-size: 0.9em; line-height: 1.8;">
                        Transactions: <strong>${a.count.toLocaleString()}</strong> (${a.pct}%)<br>
                        Avg Latency: <strong>${a.avg_latency} ms</strong><br>
                        Success Rate: <strong style="color: ${srColor};">${a.success_rate}%</strong>
                    </div>
                </div>`;
        });
        html += `</div>`;
    }

    // ── 8. Hourly Performance Pattern ──
    if (analysis.hourly_performance && analysis.hourly_performance.length > 0) {
        html += `<h3 style="color: #00bcd4; margin: 30px 0 15px; border-bottom: 1px solid rgba(0,188,212,0.3); padding-bottom: 8px;">🕐 Hourly Performance Pattern (24h)</h3>`;

        // Visual bar chart
        const maxCount = Math.max(...analysis.hourly_performance.map(h => h.count));
        html += `<div style="margin-bottom: 15px;">`;
        analysis.hourly_performance.forEach(h => {
            const barWidth = Math.max(2, (h.count / maxCount) * 100);
            const barColor = h.success_rate >= 95.5 ? '#28a745' : h.success_rate >= 94 ? '#f39c12' : '#e74c3c';
            const label = h.hour.toString().padStart(2, '0') + ':00';
            html += `
                <div style="display: flex; align-items: center; margin-bottom: 4px;">
                    <span style="width: 50px; color: #aaa; font-size: 0.85em; text-align: right; margin-right: 10px;">${label}</span>
                    <div style="flex: 1; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; height: 22px; position: relative;">
                        <div style="width: ${barWidth}%; background: ${barColor}; height: 100%; border-radius: 4px; transition: width 0.3s;"></div>
                    </div>
                    <span style="width: 90px; text-align: right; color: #ddd; font-size: 0.82em; margin-left: 8px;">${h.count.toLocaleString()} txns</span>
                    <span style="width: 55px; text-align: right; color: ${barColor}; font-size: 0.82em; margin-left: 5px;">${h.success_rate}%</span>
                </div>`;
        });
        html += `</div>`;

        // Peak vs off-peak summary
        if (analysis.peak_vs_offpeak) {
            const pvop = analysis.peak_vs_offpeak;
            html += `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 15px 0 20px;">
                    <div style="background: rgba(255,193,7,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #ffc107;">
                        <div style="color: #ffc107; font-weight: bold; margin-bottom: 5px;">☀️ Peak Hours (9AM-9PM)</div>
                        <div style="color: #ddd; font-size: 0.9em; line-height: 1.8;">
                            Transactions: <strong>${pvop.peak_transactions.toLocaleString()}</strong><br>
                            Avg Latency: <strong>${pvop.peak_avg_latency} ms</strong>
                        </div>
                    </div>
                    <div style="background: rgba(63,81,181,0.1); padding: 15px; border-radius: 8px; border-left: 3px solid #3f51b5;">
                        <div style="color: #7986cb; font-weight: bold; margin-bottom: 5px;">🌙 Off-Peak Hours (9PM-9AM)</div>
                        <div style="color: #ddd; font-size: 0.9em; line-height: 1.8;">
                            Transactions: <strong>${pvop.offpeak_transactions.toLocaleString()}</strong><br>
                            Avg Latency: <strong>${pvop.offpeak_avg_latency} ms</strong>
                        </div>
                    </div>
                </div>`;
        }
    }

    // ── 9. Weekend vs Weekday ──
    if (analysis.weekend_vs_weekday) {
        const wk = analysis.weekend_vs_weekday.weekend;
        const wd = analysis.weekend_vs_weekday.weekday;
        html += `<h3 style="color: #00bcd4; margin: 30px 0 15px; border-bottom: 1px solid rgba(0,188,212,0.3); padding-bottom: 8px;">📅 Weekend vs Weekday Performance</h3>`;
        html += `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                <div style="background: rgba(156,39,176,0.1); padding: 20px; border-radius: 8px; border-left: 3px solid #9c27b0;">
                    <div style="color: #ce93d8; font-weight: bold; font-size: 1.05em; margin-bottom: 10px;">🏖️ Weekend</div>
                    <div style="color: #ddd; line-height: 2;">
                        Transactions: <strong>${wk.count.toLocaleString()}</strong><br>
                        Avg Latency: <strong>${wk.avg_latency} ms</strong><br>
                        Success Rate: <strong style="color: ${wk.success_rate >= 95 ? '#28a745' : '#f39c12'};">${wk.success_rate}%</strong><br>
                        Failures: <strong style="color: #e74c3c;">${wk.failure_count.toLocaleString()}</strong>
                    </div>
                </div>
                <div style="background: rgba(33,150,243,0.1); padding: 20px; border-radius: 8px; border-left: 3px solid #2196f3;">
                    <div style="color: #64b5f6; font-weight: bold; font-size: 1.05em; margin-bottom: 10px;">💼 Weekday</div>
                    <div style="color: #ddd; line-height: 2;">
                        Transactions: <strong>${wd.count.toLocaleString()}</strong><br>
                        Avg Latency: <strong>${wd.avg_latency} ms</strong><br>
                        Success Rate: <strong style="color: ${wd.success_rate >= 95 ? '#28a745' : '#f39c12'};">${wd.success_rate}%</strong><br>
                        Failures: <strong style="color: #e74c3c;">${wd.failure_count.toLocaleString()}</strong>
                    </div>
                </div>
            </div>`;
    }

    // ── 10. Fraud Analysis ──
    if (analysis.fraud_analysis) {
        const fraud = analysis.fraud_analysis;
        html += `<h3 style="color: #00bcd4; margin: 30px 0 15px; border-bottom: 1px solid rgba(0,188,212,0.3); padding-bottom: 8px;">🛡️ Fraud Detection Summary</h3>`;
        const fraudColor = fraud.fraud_rate_pct > 1 ? '#e74c3c' : fraud.fraud_rate_pct > 0.1 ? '#f39c12' : '#28a745';
        html += `
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px;">
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="color: #999; font-size: 0.85em;">Flagged Transactions</div>
                    <div style="color: #e74c3c; font-size: 1.5em; font-weight: bold;">${fraud.total_flagged.toLocaleString()}</div>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="color: #999; font-size: 0.85em;">Fraud Rate</div>
                    <div style="color: ${fraudColor}; font-size: 1.5em; font-weight: bold;">${fraud.fraud_rate_pct}%</div>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="color: #999; font-size: 0.85em;">Clean Transactions</div>
                    <div style="color: #28a745; font-size: 1.5em; font-weight: bold;">${fraud.clean_transactions.toLocaleString()}</div>
                </div>
            </div>`;
    }

    // ── 11. Key Findings Summary ──
    html += `<h style="color: #00bcd4; margin: 30px 0 15px; border-bottom: 1px solid rgba(0,188,212,0.3); padding-bottom: 8px;"> Key Findings from ${(data.total_transactions || 0).toLocaleString()} >`;
    html += `<ul style="padding-left: 20px; line-height: 2.2; color:#ddd;">`;
    html += `<li><strong>${(data.total_transactions || 0).toLocaleString()}</strong> </li>`;
    html += `<li>Average latency: <strong>${data.average_latency} ms</strong> | Median: <strong>${data.median_latency || '-'} ms</strong> | P95: <strong>${data.p95_latency} ms</strong> | P99: <strong>${data.p99_latency} ms</strong></li>`;
    html += `<li>Success rate: <strong style="color: #28a745;">${data.success_rate}%</strong> (${(data.total_success || 0).toLocaleString()} successful) | Failure rate: <strong style="color: #e74c3c;">${data.failure_rate}%</strong> (${(data.total_failures || 0).toLocaleString()} failed)</li>`;
    html += `<li>APDEX score: <strong>${data.apdex}</strong> — ${data.apdex >= 0.94 ? 'Excellent user satisfaction' : data.apdex >= 0.85 ? 'Good user satisfaction' : 'Needs improvement'}</li>`;

    if (analysis.device_performance && analysis.device_performance.length > 0) {
        const topDevice = analysis.device_performance[0];
        html += `<li>Most used device: <strong>${topDevice.device}</strong> (${topDevice.count.toLocaleString()} transactions, ${topDevice.pct}%)</li>`;
    }
    if (analysis.network_performance && analysis.network_performance.length > 0) {
        const fastestNet = [...analysis.network_performance].sort((a, b) => a.avg_latency - b.avg_latency)[0];
        html += `<li>Fastest network: <strong>${fastestNet.network}</strong> with avg latency <strong>${fastestNet.avg_latency} ms</strong></li>`;
    }
    if (analysis.bank_performance && analysis.bank_performance.length > 0) {
        const topBank = analysis.bank_performance[0];
        html += `<li>Top bank by volume: <strong>${topBank.bank}</strong> (${topBank.count.toLocaleString()} transactions, ${topBank.success_rate}% success rate)</li>`;
    }
    if (analysis.fraud_analysis) {
        html += `<li>Fraud flagged: <strong>${analysis.fraud_analysis.total_flagged.toLocaleString()}</strong> transactions (${analysis.fraud_analysis.fraud_rate_pct}% rate)</li>`;
    }
    html += `</ul>`;

    // ── 12. Source attribution ──
    html += `
        <div style="margin-top: 30px; padding: 15px; background: rgba(0,188,212,0.08); border-radius: 8px; text-align: center; color: #888; font-size: 0.9em;">
    
        </div>`;

    container.innerHTML = html;
}

// Helper: Device icons
function getDeviceIcon(device) {
    const icons = { 'Android': '🤖', 'iOS': '🍎', 'Web': '🌐' };
    return icons[device] || '📱';
}

// Helper: Network icons
function getNetworkIcon(network) {
    const icons = { '4G': '📶', '5G': '🚀', '3G': '📡', 'WiFi': '📡', 'Wi-Fi': '📡' };
    return icons[network] || '🌐';
}

// Helper: Category icons
function getCategoryIcon(category) {
    const icons = {
        'Entertainment': '🎬', 'Grocery': '🛒', 'Fuel': '⛽', 'Food': '🍔',
        'Shopping': '🛍️', 'Utilities': '💡', 'Travel': '✈️', 'Education': '📚',
        'Healthcare': '🏥', 'Recharge': '📱', 'Transfer': '💸', 'Bills': '📄',
        'Investment': '📈', 'Insurance': '🛡️'
    };
    return icons[category] || '🏷️';
}

function setupPerformanceActions() {
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', fetchPerformanceMetrics);
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
    const container = document.querySelector('.performance-container') || document.body;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    container.insertBefore(errorDiv, container.firstChild);

    setTimeout(() => errorDiv.remove(), 5000);
}

function startPerformanceAutoRefresh(interval = 30000) {
    fetchPerformanceMetrics();

    if (performanceAutoRefresh) {
        clearInterval(performanceAutoRefresh);
    }

    performanceAutoRefresh = setInterval(fetchPerformanceMetrics, interval);
}

function stopPerformanceAutoRefresh() {
    if (performanceAutoRefresh) {
        clearInterval(performanceAutoRefresh);
        performanceAutoRefresh = null;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Performance metrics page loaded — analyzing UPI transactions');
    setupPerformanceActions();
    startPerformanceAutoRefresh(30000);
});

// Cleanup
window.addEventListener('beforeunload', function() {
    stopPerformanceAutoRefresh();
});
