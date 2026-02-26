const API_BASE = '/api/orchestrator';

async function deployChange() {
    const prompt = document.getElementById('change-prompt').value.trim();
    if (!prompt) return alert('Please describe the change first.');

    const btn = document.getElementById('deploy-btn');
    btn.classList.add('loading');
    btn.disabled = true;

    const isValidation = document.getElementById('validation-rule').checked;

    // Show immediate feedback
    const container = document.getElementById('changes-container');
    const loadingHtml = `
        <div class="change-item" id="pending-change" style="border-left: 4px solid #3b82f6;">
            <div class="change-header">
                <span class="change-id">Initializing...</span>
                <span class="change-time">Just now</span>
            </div>
            <div class="change-desc">
                <strong>Prompt:</strong> ${prompt}
            </div>
            <div class="agents-grid">
                <div class="agent-card">
                    <div class="agent-header">
                        <span class="agent-name">NPCI Agent</span>
                        <span class="status-pill status-received">Processing...</span>
                    </div>
                    <div class="agent-logs">
                        <div class="log-entry">
                            <span class="log-time">Now</span>
                            <span class="log-msg">Sending prompt to NPCI agent: "${prompt}"</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = loadingHtml + container.innerHTML;

    // Build receivers and affected_components from selected agents (all four by default)
    const remitterChecked = document.getElementById('agent-remitter')?.checked !== false;
    const beneficiaryChecked = document.getElementById('agent-beneficiary')?.checked !== false;
    const payerPspChecked = document.getElementById('agent-payer-psp')?.checked !== false;
    const payeePspChecked = document.getElementById('agent-payee-psp')?.checked !== false;

    const receivers = [];
    const affectedComponents = [];
    if (remitterChecked) { receivers.push('REMITTER_BANK_AGENT'); affectedComponents.push('rem_bank'); }
    if (beneficiaryChecked) { receivers.push('BENEFICIARY_BANK_AGENT'); affectedComponents.push('bene_bank'); }
    if (payerPspChecked) { receivers.push('PAYER_PSP_AGENT'); affectedComponents.push('payer_psp'); }
    if (payeePspChecked) { receivers.push('PAYEE_PSP_AGENT'); affectedComponents.push('payee_psp'); }

    if (receivers.length === 0) {
        alert('Please select at least one agent (Remitter Bank, Beneficiary Bank, Payer PSP, or Payee PSP).');
        btn.classList.remove('loading');
        btn.disabled = false;
        return;
    }

    // Payload matching what NPCI agent expects
    const payload = {
        description: prompt,
        change_type: isValidation ? 'validation_rule' : 'api_change',
        receivers: receivers,
        code_changes: {
            prompt: prompt
        },
        affected_components: affectedComponents
    };

    try {
        console.log('[UI] Sending deploy request:', payload);

        // Call the proxy endpoint on Orchestrator
        const res = await fetch('/api/ui/deploy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        console.log('[UI] Deploy response:', data);

        if (res.ok) {
            const changeId = data.change_id || (data.manifest && data.manifest.change_id);
            console.log('[UI] Change ID:', changeId);

            // Clear input
            document.getElementById('change-prompt').value = '';

            // Wait for change to be registered, then remove pending indicator
            let attempts = 0;
            const checkRegistered = setInterval(() => {
                fetchChanges().then(() => {
                    // Check if change appears in the list
                    const container = document.getElementById('changes-container');
                    const changeExists = container.textContent.includes(changeId ? changeId.substring(0, 8) : '');

                    if (changeExists || attempts >= 10) {
                        clearInterval(checkRegistered);
                        const pendingEl = document.getElementById('pending-change');
                        if (pendingEl) pendingEl.remove();
                    }
                    attempts++;
                });
            }, 300);

            // Do immediate refresh
            fetchChanges();

            // Show notification that agents are processing
            showNotification('✅ Change deployed! Agents are now processing. Click "Refresh" to see updates.', 'success');
        } else {
            alert('Error deploying change: ' + (data.error || 'Unknown error'));
            const pendingEl = document.getElementById('pending-change');
            if (pendingEl) pendingEl.remove();
        }
    } catch (e) {
        console.error('[UI] Deploy error:', e);
        alert('Network error: ' + e.message);
        const pendingEl = document.getElementById('pending-change');
        if (pendingEl) pendingEl.remove();
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

async function fetchChanges() {
    try {
        const res = await fetch(`${API_BASE}/changes`);
        if (!res.ok) {
            console.error(`Failed to fetch changes: ${res.status} ${res.statusText}`);
            return;
        }
        const data = await res.json(); // Returns dict of change_id -> change_obj

        const container = document.getElementById('changes-container');

        // Don't clear if we have a pending change that's not yet registered
        const pendingEl = document.getElementById('pending-change');

        // Convert to array and sort by created_at desc
        const changes = Object.values(data).sort((a, b) =>
            new Date(b.created_at) - new Date(a.created_at)
        );

        if (changes.length === 0) {
            // Only show empty state if there's no pending change
            if (!pendingEl) {
                container.innerHTML = '<div class="empty-state" style="text-align:center; padding: 2rem; color: #64748b;">Waiting for new changes...</div>';
            }
            return;
        }

        // Remove pending indicator if we have real changes now
        if (pendingEl) {
            pendingEl.remove();
        }

        container.innerHTML = changes.map(change => {
            const date = new Date(change.created_at).toLocaleTimeString();
            const manifest = change.manifest || {};

            // PR statuses
            const changeId = manifest.change_id;
            const prs = window.prStatuses && window.prStatuses[changeId] ? window.prStatuses[changeId] : {};
            let prStatusHtml = '';

            if (Object.keys(prs).length > 0) {
                const allMerged = Object.values(prs).every(pr => pr.merged);
                const prBadges = Object.entries(prs).map(([agent, pr]) => {
                    const cleanName = agent.replace('_AGENT', '').replace('_', ' ');
                    const badgeClass = pr.merged ? 'status-ready' : 'status-tested';
                    const statusText = pr.merged ? 'Merged' : 'Pending';
                    return `<a href="${pr.url}" target="_blank" class="status-pill ${badgeClass}" style="text-decoration:none; margin-right: 0.5rem; display:inline-block;" title="View PR on GitHub">${cleanName}: ${statusText}</a>`;
                }).join('');

                prStatusHtml = `
                    <div style="margin-bottom: 1rem; padding: 0.75rem; background: #f8fafc; border-radius: 6px; border-left: 4px solid ${allMerged ? '#10b981' : '#f59e0b'};">
                        <strong style="display:block; margin-bottom: 0.5rem;">Associated Pull Requests:</strong>
                        <div>${prBadges}</div>
                        ${allMerged ? '<div style="margin-top:0.5rem; color:#10b981; font-weight:bold;">✅ All Pull Requests Merged! Ready for deployment.</div>' : '<div style="margin-top:0.5rem; color:#64748b; font-size: 0.9em;">Waiting for PRs to be reviewed and merged.</div>'}
                    </div>
                 `;
            }

            // Build agent status indicators
            const statuses = change.statuses || {};
            const details = change.details || {}; // Get detailed logs

            const agentHtml = Object.entries(statuses).map(([agent, status]) => {
                const cleanName = agent.replace('_AGENT', '').replace('_', ' ');
                const statusLower = status.toLowerCase();

                // Get logs for this agent
                const agentDetails = details[agent] || {};
                const logs = agentDetails.logs || [];

                // Render logs with better formatting
                let logsHtml = '';
                if (logs.length > 0) {
                    logsHtml = logs.map(log => {
                        const time = new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                        const message = log.message || '';

                        // Check for structured data
                        const data = log.data || {};
                        let extraContent = '';

                        // Render prompt if present
                        if (data.prompt) {
                            extraContent += `
                                <details class="log-details">
                                    <summary>View Prompt</summary>
                                    <pre class="log-code">${escapeHtml(data.prompt)}</pre>
                                </details>
                            `;
                        }

                        // Render response if present
                        if (data.response) {
                            extraContent += `
                                <details class="log-details">
                                    <summary>View Response</summary>
                                    <pre class="log-code">${escapeHtml(data.response)}</pre>
                                </details>
                            `;
                        }

                        // Render diff if present
                        if (data.diff) {
                            extraContent += `
                                <details class="log-details">
                                    <summary>File Changes: ${data.file || 'Unknown file'}</summary>
                                    <pre class="log-diff">${escapeHtml(data.diff)}</pre>
                                </details>
                            `;
                        }

                        // Highlight important messages
                        const isImportant = message.toLowerCase().includes('prompt') ||
                            message.toLowerCase().includes('dispatching') ||
                            message.toLowerCase().includes('received') ||
                            message.toLowerCase().includes('processing') ||
                            message.toLowerCase().includes('applying') ||
                            message.toLowerCase().includes('updated') ||
                            message.toLowerCase().includes('ready');

                        return `
                        <div class="log-entry ${isImportant ? 'log-important' : ''}">
                            <div class="log-main">
                                <span class="log-time">${time}</span>
                                <span class="log-msg">${message || 'Status update'}</span>
                            </div>
                            ${extraContent}
                        </div>`;
                    }).join('');
                } else {
                    // Show status-based message instead of generic "waiting"
                    const statusMsg = status === 'RECEIVED' ? 'Manifest received, processing...' :
                        status === 'APPLIED' ? 'Changes applied, testing...' :
                            status === 'TESTED' ? 'Tests passed, finalizing...' :
                                status === 'READY' ? 'Ready for deployment' :
                                    status === 'ERROR' ? 'Error occurred during processing' :
                                        'Initializing...';
                    logsHtml = `<div class="log-entry"><span class="log-msg" style="color:var(--text-secondary)">${statusMsg}</span></div>`;
                }

                return `
                    <div class="agent-card">
                        <div class="agent-header">
                            <span class="agent-name">${cleanName}</span>
                            <span class="status-pill status-${statusLower}">${status}</span>
                        </div>
                        <div class="agent-logs">
                            ${logsHtml}
                        </div>
                    </div>
                `;
            }).join('');

            return `
                <div class="change-item">
                    <div class="change-header">
                        <span class="change-id">ID: ${change.manifest.change_id.slice(0, 8)}...</span>
                        <span class="change-time">${date}</span>
                    </div>
                    <div class="change-desc">
                        ${manifest.description || 'No description provided'}
                    </div>
                    ${prStatusHtml}
                    <div class="agents-grid">
                        ${agentHtml}
                    </div>
                </div>
            `;
        }).join('');

    } catch (e) {
        console.error("Failed to fetch changes:", e);
        // Show error message in UI
        const container = document.getElementById('changes-container');
        const pendingEl = document.getElementById('pending-change');
        if (!pendingEl) {
            container.innerHTML = `<div class="empty-state" style="text-align:center; padding: 2rem; color: #ef4444;">Error loading changes: ${e.message}. Please try refreshing.</div>`;
        }
    }
}

// Handle refresh button click with visual feedback
async function handleRefresh() {
    const btn = document.getElementById('refresh-btn');
    const text = document.getElementById('refresh-text');
    const spinner = document.getElementById('refresh-spinner');

    // Show spinner
    text.style.display = 'none';
    spinner.style.display = 'inline-block';
    spinner.style.animation = 'spin 1s linear infinite';

    // Fetch changes
    await fetchChanges();

    // Hide spinner after a short delay
    setTimeout(() => {
        spinner.style.display = 'none';
        text.style.display = 'inline';
    }, 500);
}

// Initial load
fetchChanges();

// Utility to escape HTML to prevent XSS in logs
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

window.prStatuses = {};

async function pollPrStatuses() {
    const changesRes = await fetch(`${API_BASE}/changes`);
    if (!changesRes.ok) return;
    const data = await changesRes.json();

    // For each change, poll its PR statuses
    for (const changeId of Object.keys(data)) {
        try {
            const res = await fetch(`${API_BASE}/changes/${changeId}/pr_status`);
            if (res.ok) {
                const prData = await res.json();
                if (prData.prs && Object.keys(prData.prs).length > 0) {
                    window.prStatuses[changeId] = prData.prs;
                }
            }
        } catch (e) {
            console.error("Failed to poll PR status for " + changeId, e);
        }
    }
    // Refresh UI with new statuses
    fetchChanges();
}

// Start PR polling every 10 seconds
setInterval(pollPrStatuses, 10000);
pollPrStatuses(); // initial fetch

// Show notification helper
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}
