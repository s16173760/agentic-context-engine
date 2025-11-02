// Comparative Demo Frontend JavaScript

const state = {
    totalRounds: 4,
    completedRounds: 0,
    baselineTotalTokens: 0,
    aceTotalTokens: 0,
    judgeTotalTokens: 0,
    baselineTotalScore: 0,
    aceTotalScore: 0
};

// Start button handler
document.getElementById('start-btn').addEventListener('click', async () => {
    const btn = document.getElementById('start-btn');
    const statusText = document.getElementById('status-text');
    
    // Check playbook status first
    try {
        const playbookResponse = await fetch('/api/playbook/status');
        const playbookStatus = await playbookResponse.json();
        
        if (!playbookStatus.ready) {
            statusText.innerHTML = `
                ❌ ${playbookStatus.message}
                <br>
                Please run: <code>python demo/pretrain_playbook.py</code>
            `;
            return;
        }
        
        statusText.innerHTML = `✅ Playbook loaded with ${playbookStatus.strategies} strategies!`;
        
    } catch (error) {
        statusText.textContent = `Error checking playbook: ${error.message}`;
        return;
    }
    
    // Disable button and start race
    btn.disabled = true;
    statusText.innerHTML = '<span class="spinner"></span> Starting competition...';
    
    // Clear previous results
    document.getElementById('rounds-container').innerHTML = '';
    state.completedRounds = 0;
    state.baselineTotalTokens = 0;
    state.aceTotalTokens = 0;
    state.judgeTotalTokens = 0;
    state.baselineTotalScore = 0;
    state.aceTotalScore = 0;
    
    // Start SSE stream
    const eventSource = new EventSource('/api/stream/comparative');
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleEvent(data);
    };
    
    eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        statusText.textContent = '❌ Connection error. Please refresh and try again.';
        eventSource.close();
        btn.disabled = false;
    };
});

function handleEvent(data) {
    const statusText = document.getElementById('status-text');
    
    switch (data.type) {
        case 'start':
            state.totalRounds = data.total;
            statusText.textContent = `🏁 Starting ${data.total} rounds...`;
            break;
            
        case 'round_start':
            createRoundCard(data.round);
            statusText.textContent = `Round ${data.round}/${state.totalRounds} starting...`;
            break;
            
        case 'baseline_start':
            updateRoundStatus(data.round, '🔵 Baseline analyzing...');
            break;
            
        case 'baseline_complete':
            updateRoundStatus(data.round, '✅ Baseline complete');
            break;
            
        case 'ace_start':
            updateRoundStatus(data.round, '🟢 ACE analyzing...');
            break;
            
        case 'ace_complete':
            updateRoundStatus(data.round, '✅ ACE complete');
            break;
            
        case 'judging_start':
            updateRoundStatus(data.round, '⚖️ Judge comparing...');
            break;
            
        case 'round_complete':
            displayRoundResults(data);
            state.completedRounds++;
            statusText.textContent = `✅ Round ${data.round} complete! (${state.completedRounds}/${state.totalRounds})`;
            break;
            
        case 'final_summary':
            displayFinalSummary(data);
            statusText.textContent = '🏆 Competition complete!';
            document.getElementById('start-btn').disabled = false;
            break;
            
        case 'error':
            statusText.textContent = `❌ Error: ${data.message}`;
            document.getElementById('start-btn').disabled = false;
            break;
    }
}

function createRoundCard(roundNum) {
    const container = document.getElementById('rounds-container');
    
    const card = document.createElement('div');
    card.className = 'round-card';
    card.id = `round-${roundNum}`;
    
    card.innerHTML = `
        <div class="round-header">
            <div class="round-title">Round ${roundNum}</div>
            <div class="round-status status-processing" id="round-${roundNum}-status">
                <span class="spinner"></span> Starting...
            </div>
        </div>
        <div id="round-${roundNum}-content">
            <p style="text-align:center; color:#6b7280;">Waiting for results...</p>
        </div>
    `;
    
    container.appendChild(card);
    card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function updateRoundStatus(roundNum, statusText) {
    const statusEl = document.getElementById(`round-${roundNum}-status`);
    if (statusEl) {
        statusEl.innerHTML = statusText;
    }
}

function displayRoundResults(data) {
    const contentEl = document.getElementById(`round-${data.round}-content`);
    const statusEl = document.getElementById(`round-${data.round}-status`);
    
    // Update status to complete
    statusEl.className = 'round-status status-complete';
    statusEl.textContent = '✅ Judged';
    
    // Get score classes
    const baselineScoreClass = getScoreClass(data.baseline.score);
    const aceScoreClass = getScoreClass(data.ace.score);
    
    // Determine winner emoji
    let winnerEmoji = '🤝';
    if (data.judge.winner === 'baseline') winnerEmoji = '🔵';
    else if (data.judge.winner === 'ace') winnerEmoji = '🟢';
    
    contentEl.innerHTML = `
        <div class="comparison-grid">
            <!-- Baseline Results -->
            <div class="comparison-box baseline">
                <h4>🔵 Baseline (Junior)</h4>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Time</div>
                        <div class="metric-value">${data.baseline.time.toFixed(1)}s</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Tokens</div>
                        <div class="metric-value">${data.baseline.tokens.toLocaleString()}</div>
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">Judge Score</div>
                    <div class="metric-value score-highlight ${baselineScoreClass}">${data.baseline.score}/100</div>
                </div>
                <div class="analysis-section">
                    <h5>✅ Strengths:</h5>
                    <p class="strengths">${data.baseline.strengths}</p>
                </div>
                <div class="analysis-section">
                    <h5>❌ Weaknesses:</h5>
                    <p class="weaknesses">${data.baseline.weaknesses}</p>
                </div>
                <details class="code-display">
                    <summary>View Full Answer</summary>
                    <pre>${escapeHtml(data.baseline.answer)}</pre>
                </details>
            </div>
            
            <!-- ACE Results -->
            <div class="comparison-box ace">
                <h4>🟢 ACE (Senior Expert)</h4>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Time</div>
                        <div class="metric-value">${data.ace.time.toFixed(1)}s</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Tokens</div>
                        <div class="metric-value">${data.ace.tokens.toLocaleString()}</div>
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">Judge Score</div>
                    <div class="metric-value score-highlight ${aceScoreClass}">${data.ace.score}/100</div>
                </div>
                <div class="analysis-section">
                    <h5>✅ Strengths:</h5>
                    <p class="strengths">${data.ace.strengths}</p>
                </div>
                <div class="analysis-section">
                    <h5>❌ Weaknesses:</h5>
                    <p class="weaknesses">${data.ace.weaknesses}</p>
                </div>
                <details class="code-display">
                    <summary>View Full Answer</summary>
                    <pre>${escapeHtml(data.ace.answer)}</pre>
                </details>
            </div>
        </div>
        
        <!-- Judge Verdict -->
        <div class="judge-verdict">
            <h4>⚖️ Judge Verdict</h4>
            <div class="winner-text">Winner: ${winnerEmoji} ${capitalizeFirst(data.judge.winner)}</div>
            <div class="judge-reasoning">${data.judge.reasoning}</div>
            <div style="margin-top:10px; font-size:0.9rem;">Judge tokens: ${data.judge.tokens}</div>
        </div>
        
        <!-- Code Sample -->
        <details class="code-display">
            <summary>📝 View Original Code & Ground Truth</summary>
            <h5 style="margin-top:10px;">Code:</h5>
            <pre>${escapeHtml(data.code_sample)}</pre>
            <h5 style="margin-top:15px;">Ground Truth (Expected Bugs):</h5>
            <p style="padding:10px; background:#f3f4f6; border-radius:5px; margin-top:5px;">${escapeHtml(data.ground_truth)}</p>
        </details>
    `;
    
    // Update running totals
    state.baselineTotalTokens += data.baseline.tokens;
    state.aceTotalTokens += data.ace.tokens;
    state.judgeTotalTokens += data.judge.tokens;
    state.baselineTotalScore += data.baseline.score;
    state.aceTotalScore += data.ace.score;
    
    updateOverallStats();
}

function displayFinalSummary(data) {
    const winnerBanner = document.getElementById('winner-banner');
    
    const baselineAvg = data.baseline.avg_score.toFixed(1);
    const aceAvg = data.ace.avg_score.toFixed(1);
    
    let winner = 'Tie!';
    let winnerColor = '#f59e0b';
    
    if (aceAvg > baselineAvg) {
        winner = '🟢 ACE Wins!';
        winnerColor = '#10b981';
    } else if (baselineAvg > aceAvg) {
        winner = '🔵 Baseline Wins!';
        winnerColor = '#3b82f6';
    }
    
    winnerBanner.style.background = `linear-gradient(135deg, ${winnerColor} 0%, ${shadeColor(winnerColor, -20)} 100%)`;
    winnerBanner.innerHTML = `
        <h2>${winner}</h2>
        <p>Average Scores: Baseline ${baselineAvg}% vs ACE ${aceAvg}%</p>
        <p style="margin-top:20px; font-size:1.2rem;">
            Total Tokens: Baseline ${data.baseline.total_tokens.toLocaleString()} | ACE ${data.ace.total_tokens.toLocaleString()}
        </p>
    `;
    winnerBanner.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        winnerBanner.style.display = 'none';
    }, 5000);
}

function updateOverallStats() {
    const rounds = state.completedRounds;
    if (rounds === 0) return;
    
    document.getElementById('baseline-avg-score').textContent = `${(state.baselineTotalScore / rounds).toFixed(1)}%`;
    document.getElementById('baseline-total-tokens').textContent = `${state.baselineTotalTokens.toLocaleString()} tokens`;
    
    document.getElementById('ace-avg-score').textContent = `${(state.aceTotalScore / rounds).toFixed(1)}%`;
    document.getElementById('ace-total-tokens').textContent = `${state.aceTotalTokens.toLocaleString()} tokens`;
    
    document.getElementById('judge-total-tokens').textContent = `${state.judgeTotalTokens.toLocaleString()} tokens`;
}

function getScoreClass(score) {
    if (score >= 90) return 'score-100';
    if (score >= 70) return 'score-80';
    if (score >= 50) return 'score-60';
    if (score >= 30) return 'score-40';
    return 'score-0';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function shadeColor(color, percent) {
    const num = parseInt(color.slice(1), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = (num >> 8 & 0x00FF) + amt;
    const B = (num & 0x0000FF) + amt;
    return "#" + (0x1000000 + (R<255?R<1?0:R:255)*0x10000 +
        (G<255?G<1?0:G:255)*0x100 + (B<255?B<1?0:B:255))
        .toString(16).slice(1);
}

