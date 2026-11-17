async function pasteUrl() {
    try {
        const text = await navigator.clipboard.readText();
        document.getElementById('urlInput').value = text;
    } catch (err) {
        alert('Failed to read clipboard.');
    }
}

let currentFilter = 'all';
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        currentFilter = e.target.getAttribute('data-filter');
        
        document.querySelectorAll('.task-item').forEach(item => {
            const status = item.getAttribute('data-status');
            if (currentFilter === 'all' || status === currentFilter) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    });
});

async function startRealDownload() {
    const query = document.getElementById('urlInput').value.trim();
    if (!query) return alert("Please enter a URL.");

    document.getElementById('empty-state')?.remove();
    document.getElementById('urlInput').value = '';

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: query })
        });

        const data = await response.json();
        if (response.ok) {
            createTaskUI(data.task_id, "Extracting metadata...");
            pollStatus(data.task_id);
        } else {
            alert(data.error);
        }
    } catch (err) {
        alert("Server error.");
    }
}

function createTaskUI(taskId, initialTitle) {
    const list = document.getElementById('task-list');
    const item = document.createElement('div');
    item.className = 'task-item';
    item.id = `task-${taskId}`;
    item.setAttribute('data-status', 'PENDING');
    
    item.innerHTML = `
        <div class="task-info">
            <div class="task-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"></path><circle cx="6" cy="18" r="3"></circle><circle cx="18" cy="16" r="3"></circle></svg>
            </div>
            <div class="task-details">
                <h4 id="title-${taskId}" style="max-width: 300px; word-break: break-word;">${initialTitle}</h4>
                <div class="progress-container" id="progress-container-${taskId}">
                    <div class="progress-bar"><div class="progress-fill" id="progress-${taskId}" style="width: 0%"></div></div>
                </div>
            </div>
        </div>
        <div class="status-badge status-downloading" id="badge-${taskId}">PENDING</div>
    `;
    list.prepend(item);
}

function pollStatus(taskId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${taskId}`);
            const data = await response.json();
            
            updateTaskUI(taskId, data);

            if (data.status === 'SUCCESS' || data.status === 'FAILED') {
                clearInterval(interval);
            }
        } catch (error) {
            clearInterval(interval);
        }
    }, 1000);
}

function updateTaskUI(taskId, data) {
    const item = document.getElementById(`task-${taskId}`);
    if (!item) return;

    const progressBar = document.getElementById(`progress-${taskId}`);
    const badge = document.getElementById(`badge-${taskId}`);
    const titleEl = document.getElementById(`title-${taskId}`);

    progressBar.style.width = `${data.progress}%`;
    if (data.title) titleEl.innerText = data.title;

    if (data.status === 'SUCCESS') {
        item.setAttribute('data-status', 'SUCCESS');
        badge.className = 'status-badge status-completed';
        badge.innerText = 'READY';
        document.getElementById(`progress-container-${taskId}`).innerHTML = `
            <a href="/api/downloads/${encodeURIComponent(data.filename)}" class="btn btn-primary" style="height: 30px; font-size: 0.8rem; padding: 0 12px; margin-top: 8px; text-decoration: none;">Save to Device</a>
        `;
    } else if (data.status === 'FAILED') {
        item.setAttribute('data-status', 'FAILED');
        badge.className = 'status-badge status-failed';
        badge.innerText = 'FAILED';
        titleEl.innerText = "Error: " + (data.error || "Unknown");
        progressBar.style.backgroundColor = 'var(--danger)';
    } else {
        item.setAttribute('data-status', data.status === 'TAGGING' ? 'PROCESSING' : data.status);
        badge.className = 'status-badge status-downloading';
        badge.innerText = data.status;
    }
}


