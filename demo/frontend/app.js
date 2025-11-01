// Bug Hunter Race - Frontend Logic

class RaceTracker {
    constructor(mode, trackId, responseId, timeId, tokensId, qualityId, strategiesId = null) {
        this.mode = mode;
        this.track = document.getElementById(trackId);
        this.responseBox = document.getElementById(responseId);
        this.timeDisplay = document.getElementById(timeId);
        this.tokensDisplay = document.getElementById(tokensId);
        this.qualityDisplay = document.getElementById(qualityId);
        this.strategiesDisplay = strategiesId ? document.getElementById(strategiesId) : null;
        
        this.totalSamples = 4; // Test samples only
        this.currentSample = 0;
        this.totalTime = 0;
        this.totalTokens = 0;
        this.accuracies = [];
        this.completed = false;
        this.startTime = null;
        this.timerInterval = null;
        
        this.initTrack();
    }
    
    initTrack() {
        this.track.innerHTML = '';
        for (let i = 1; i <= this.totalSamples; i++) {
            const dotContainer = document.createElement('div');
            dotContainer.className = 'sample-item';
            dotContainer.id = `${this.mode}-dot-container-${i}`;
            
            const dot = document.createElement('div');
            dot.className = 'dot';
            dot.id = `${this.mode}-dot-${i}`;
            
            const label = document.createElement('span');
            label.className = 'sample-label';
            label.textContent = `Sample ${i}`;
            
            const metrics = document.createElement('div');
            metrics.className = 'sample-metrics';
            metrics.id = `${this.mode}-metrics-${i}`;
            
            dotContainer.appendChild(dot);
            dotContainer.appendChild(label);
            dotContainer.appendChild(metrics);
            this.track.appendChild(dotContainer);
        }
        
        // Clear "waiting to start" message
        this.responseBox.innerHTML = '<div class="response-content"><em>Ready to start...</em></div>';
    }
    
    updateProgress(sampleId, status) {
        const dot = document.getElementById(`${this.mode}-dot-${sampleId}`);
        if (dot) {
            dot.className = `dot ${status}`;
        }
        
        // Update response box to show current sample processing
        if (status === 'processing') {
            this.responseBox.innerHTML = `
                <div class="response-content">
                    <strong>Processing Sample ${sampleId}...</strong><br>
                    <span class="processing-text">🔍 Analyzing code...</span>
                </div>
            `;
        }
    }
    
    updateResult(data) {
        this.currentSample = data.sample_id;
        this.totalTime = data.total_time;
        this.totalTokens = data.total_tokens;
        this.accuracies.push(data.accuracy);
        
        // Update progress dot
        const dot = document.getElementById(`${this.mode}-dot-${data.sample_id}`);
        if (dot) {
            dot.className = `dot complete`;
        }
        
        // Update metrics
        const metricsContainer = document.getElementById(`${this.mode}-metrics-${data.sample_id}`);
        if (metricsContainer) {
            const qualityEmoji = data.accuracy >= 0.8 ? '✅' : data.accuracy >= 0.6 ? '⚠️' : '❌';
            metricsContainer.innerHTML = `
                <span class="metric">${qualityEmoji} ${(data.accuracy * 100).toFixed(0)}%</span>
                <span class="metric">🪙 ${data.tokens}</span>
                <span class="metric">⏱️ ${data.time.toFixed(1)}s</span>
            `;
        }
        
        // Update displays (tokens update immediately)
        this.tokensDisplay.textContent = this.totalTokens.toLocaleString();
        
        // Add animation to token display
        this.tokensDisplay.style.transform = 'scale(1.1)';
        setTimeout(() => {
            this.tokensDisplay.style.transform = 'scale(1)';
        }, 200);
        
        const avgAccuracy = this.accuracies.reduce((a, b) => a + b, 0) / this.accuracies.length;
        this.qualityDisplay.textContent = `${(avgAccuracy * 100).toFixed(0)}%`;
        
        // Update strategies count if ACE
        if (this.strategiesDisplay && data.strategies_count !== undefined) {
            this.strategiesDisplay.textContent = data.strategies_count;
        }
        
        // Update response box with the actual response (escaping HTML)
        const escapedResponse = data.response.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>');
        this.responseBox.innerHTML = `
            <div class="response-content">
                <strong>Sample ${data.sample_id}:</strong><br><br>
                ${escapedResponse}
            </div>
        `;
        
        // Auto-scroll response box to top for new content
        this.responseBox.scrollTop = 0;
        
        // Scroll to current dot
        const currentDot = document.getElementById(`${this.mode}-dot-${data.sample_id}`);
        if (currentDot) {
            currentDot.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    startTimer() {
        this.startTime = Date.now();
        this.timerInterval = setInterval(() => {
            if (!this.completed) {
                const elapsed = (Date.now() - this.startTime) / 1000;
                this.timeDisplay.textContent = `${elapsed.toFixed(1)}s`;
            }
        }, 100); // Update every 100ms for smooth animation
    }
    
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }
    
    complete() {
        this.completed = true;
        this.stopTimer();
        const avgAccuracy = this.accuracies.reduce((a, b) => a + b, 0) / this.accuracies.length;
        return {
            totalTime: this.totalTime,
            totalTokens: this.totalTokens,
            avgAccuracy: avgAccuracy,
            highQualityCount: this.accuracies.filter(a => a >= 0.8).length
        };
    }
}

let baselineTracker = null;
let aceTracker = null;
let raceStartTime = 0;

async function pretrainACE() {
    return new Promise((resolve, reject) => {
        const pretrainStatus = document.getElementById('pretrainStatus');
        pretrainStatus.style.display = 'block';
        pretrainStatus.innerHTML = '<div class="pretrain-message">🧠 Pre-training ACE on training samples...</div>';
        
        const eventSource = new EventSource('/api/pretrain');
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'pretrain_start') {
                pretrainStatus.innerHTML = `<div class="pretrain-message">🧠 Pre-training ACE on ${data.total} training samples...</div>`;
            } else if (data.type === 'pretrain_progress') {
                pretrainStatus.innerHTML = `<div class="pretrain-message">📚 Training: ${data.sample_id}/${data.total}...</div>`;
            } else if (data.type === 'pretrain_update') {
                pretrainStatus.innerHTML = `<div class="pretrain-message">📚 Training: Sample ${data.sample_id} • Learned ${data.strategies} strategies</div>`;
            } else if (data.type === 'pretrain_complete') {
                pretrainStatus.innerHTML = `<div class="pretrain-message success">✅ Pre-training complete! Learned ${data.count} strategies</div>`;
                eventSource.close();
                setTimeout(() => {
                    pretrainStatus.style.display = 'none';
                    resolve();
                }, 2000);
            } else if (data.type === 'error') {
                pretrainStatus.innerHTML = `<div class="pretrain-message error">❌ Error: ${data.message}</div>`;
                eventSource.close();
                reject(new Error(data.message));
            }
        };
        
        eventSource.onerror = (error) => {
            console.error('Pretrain stream error:', error);
            pretrainStatus.innerHTML = '<div class="pretrain-message error">❌ Pre-training failed</div>';
            eventSource.close();
            reject(error);
        };
    });
}

async function checkPlaybookStatus() {
    const response = await fetch('/api/playbook/status');
    const status = await response.json();
    return status;
}

async function startRace() {
    // Reset UI
    document.getElementById('startRace').style.display = 'none';
    document.getElementById('resetRace').style.display = 'inline-block';
    document.getElementById('winnerBanner').style.display = 'none';
    document.getElementById('strategiesPanel').style.display = 'none';
    
    // Check if playbook is already loaded
    const playbookStatus = await checkPlaybookStatus();
    
    if (!playbookStatus.available) {
        // No pre-trained playbook available
        alert(`❌ No pre-trained playbook found!\n\nPlease run the pre-training script first:\n\npython demo/pretrain_playbook.py\n\nThis only needs to be done once.`);
        document.getElementById('startRace').style.display = 'inline-block';
        document.getElementById('resetRace').style.display = 'none';
        return;
    }
    
    // Show playbook loaded message
    const pretrainStatus = document.getElementById('pretrainStatus');
    pretrainStatus.style.display = 'block';
    pretrainStatus.innerHTML = `<div class="pretrain-message success">✅ Using pre-trained playbook (${playbookStatus.strategies_count} strategies)</div>`;
    
    setTimeout(() => {
        pretrainStatus.style.display = 'none';
    }, 2000);
    
    // Initialize trackers
    baselineTracker = new RaceTracker(
        'baseline',
        'baselineTrack',
        'baselineResponse',
        'baselineTime',
        'baselineTokens',
        'baselineQuality'
    );
    
    aceTracker = new RaceTracker(
        'ace',
        'aceTrack',
        'aceResponse',
        'aceTime',
        'aceTokens',
        'aceQuality',
        'aceStrategies'
    );
    
    raceStartTime = Date.now();
    
    // Mark lanes as active
    document.getElementById('baselineLane').classList.add('active');
    document.getElementById('aceLane').classList.add('active');
    
    // Step 3: Start both races in parallel
    await Promise.all([
        runBaseline(),
        runACE()
    ]);
    
    // Show winner
    showWinner();
}

async function runBaseline() {
    const eventSource = new EventSource('/api/stream/baseline');
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'start') {
            baselineTracker.startTimer();
        } else if (data.type === 'progress') {
            baselineTracker.updateProgress(data.sample_id, 'processing');
        } else if (data.type === 'result') {
            baselineTracker.updateResult(data);
        } else if (data.type === 'complete') {
            baselineTracker.complete();
            document.getElementById('baselineLane').classList.remove('active');
            eventSource.close();
        } else if (data.type === 'error') {
            console.error('Baseline error:', data.message);
            baselineTracker.stopTimer();
            eventSource.close();
        }
    };
    
    eventSource.onerror = (error) => {
        console.error('Baseline stream error:', error);
        baselineTracker.stopTimer();
        eventSource.close();
    };
    
    // Wait for completion
    return new Promise((resolve) => {
        const checkComplete = setInterval(() => {
            if (baselineTracker.completed) {
                clearInterval(checkComplete);
                resolve();
            }
        }, 100);
    });
}

async function runACE() {
    const eventSource = new EventSource('/api/stream/ace');
    let strategies = [];
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'start') {
            aceTracker.startTimer();
        } else if (data.type === 'progress') {
            aceTracker.updateProgress(data.sample_id, 'processing');
        } else if (data.type === 'result') {
            aceTracker.updateResult(data);
        } else if (data.type === 'strategies') {
            strategies = data.strategies;
        } else if (data.type === 'complete') {
            aceTracker.complete();
            document.getElementById('aceLane').classList.remove('active');
            
            // Show strategies
            if (strategies.length > 0) {
                showStrategies(strategies);
            }
            
            eventSource.close();
        } else if (data.type === 'error') {
            console.error('ACE error:', data.message);
            aceTracker.stopTimer();
            eventSource.close();
        }
    };
    
    eventSource.onerror = (error) => {
        console.error('ACE stream error:', error);
        aceTracker.stopTimer();
        eventSource.close();
    };
    
    // Wait for completion
    return new Promise((resolve) => {
        const checkComplete = setInterval(() => {
            if (aceTracker.completed) {
                clearInterval(checkComplete);
                resolve();
            }
        }, 100);
    });
}

function showStrategies(strategies) {
    const panel = document.getElementById('strategiesPanel');
    const list = document.getElementById('strategiesList');
    
    list.innerHTML = strategies.map((s, i) => `
        <div class="strategy-item">
            <strong>${i + 1}.</strong> ${s.content}
            <span class="strategy-stats">(✓ ${s.helpful} helpful, ✗ ${s.harmful} harmful)</span>
        </div>
    `).join('');
    
    panel.style.display = 'block';
}

function showWinner() {
    const baselineResults = baselineTracker.complete();
    const aceResults = aceTracker.complete();
    
    const tokenSavings = ((baselineResults.totalTokens - aceResults.totalTokens) / baselineResults.totalTokens * 100).toFixed(1);
    const timeSavings = ((baselineResults.totalTime - aceResults.totalTime) / baselineResults.totalTime * 100).toFixed(1);
    const qualityGain = ((aceResults.avgAccuracy - baselineResults.avgAccuracy) * 100).toFixed(1);
    
    const banner = document.getElementById('winnerBanner');
    document.getElementById('winnerTitle').textContent = aceResults.avgAccuracy > baselineResults.avgAccuracy ? 
        '🎉 ACE-Enhanced LLM WINS! 🎉' : '🏁 Race Complete!';
    
    document.getElementById('winnerStats').innerHTML = `
        <div class="winner-stat">
            <span class="stat-label">Token Savings</span>
            <span class="stat-value">${tokenSavings}%</span>
        </div>
        <div class="winner-stat">
            <span class="stat-label">Time Savings</span>
            <span class="stat-value">${timeSavings}%</span>
        </div>
        <div class="winner-stat">
            <span class="stat-label">Quality Gain</span>
            <span class="stat-value">+${qualityGain}%</span>
        </div>
        <div class="winner-stat">
            <span class="stat-label">High Quality</span>
            <span class="stat-value">${aceResults.highQualityCount}/${aceTracker.totalSamples}</span>
        </div>
    `;
    
    banner.style.display = 'block';
}

function resetRace() {
    // Reset via API
    fetch('/api/reset', { method: 'POST' })
        .then(() => {
            location.reload();
        })
        .catch(error => {
            console.error('Reset error:', error);
            location.reload();
        });
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('startRace').addEventListener('click', startRace);
    document.getElementById('resetRace').addEventListener('click', resetRace);
});
