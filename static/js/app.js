let brands = [];
let selectedBrands = [];
let currentSession = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeBrands();
    setupTabNavigation();
    loadFiles();
});

async function initializeBrands() {
    try {
        const response = await fetch('/api/brands');
        const data = await response.json();
        brands = data.brands;
        renderBrandsList();
    } catch (error) {
        console.error('Error loading brands:', error);
    }
}

function renderBrandsList() {
    const brandsList = document.getElementById('brands-list');
    brandsList.innerHTML = '';
    
    brands.forEach(brand => {
        const label = document.createElement('label');
        label.className = 'brand-checkbox';
        label.innerHTML = `
            <input type="checkbox" value="${brand.key}" onchange="toggleBrand('${brand.key}')">
            <span>${brand.name}</span>
        `;
        brandsList.appendChild(label);
    });
}

function toggleBrand(brandKey) {
    const index = selectedBrands.indexOf(brandKey);
    if (index > -1) {
        selectedBrands.splice(index, 1);
    } else {
        selectedBrands.push(brandKey);
    }
}

function setupTabNavigation() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
}

function showOption(optionName) {
    document.querySelectorAll('.option-content').forEach(el => {
        el.style.display = 'none';
    });
    document.getElementById(optionName + '-option').style.display = 'block';
}

async function scrapeUrl() {
    const url = document.getElementById('url-input').value.trim();
    
    if (!url) {
        alert('Please paste a URL');
        return;
    }
    
    if (!url.includes('facebook.com/ads/library')) {
        alert('Please paste a valid Meta Ads Library URL');
        return;
    }
    
    const taskId = 'scrape_' + Date.now();
    currentSession = taskId;
    
    document.getElementById('scrape-progress').style.display = 'block';
    
    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, task_id: taskId })
        });
        
        const data = await response.json();
        if (data.success) {
            monitorProgress(taskId, 'scrape');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error starting scrape: ' + error);
    }
}

async function scrapeBrands() {
    if (selectedBrands.length === 0) {
        alert('Please select at least one brand');
        return;
    }
    
    const taskId = 'brand_' + Date.now();
    currentSession = taskId;
    
    document.getElementById('scrape-progress').style.display = 'block';
    document.getElementById('progress-text').textContent = `Scraping ${selectedBrands.length} brands...`;
    
    try {
        const response = await fetch('/api/multi-brand-scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                brand_keys: selectedBrands,
                task_id: taskId
            })
        });
        
        const data = await response.json();
        if (data.success) {
            monitorProgress(taskId, 'scrape');
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error);
    }
}

async function monitorProgress(sessionId, type) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/scrape-status/${sessionId}`);
            const data = await response.json();
            const status = data.status;
            
            const progress = parseInt(status.progress || 0);
            document.getElementById('progress-fill').style.width = progress + '%';
            document.getElementById('progress-text').textContent = `Progress: ${progress}% - Status: ${status.status}`;
            
            if (status.ads_found) {
                document.getElementById('scrape-status').innerHTML = `
                    <strong>Ads Found:</strong> ${status.ads_found}<br>
                    <strong>Output File:</strong> ${status.output_file ? status.output_file.split('/').pop() : 'Processing...'}
                `;
            }
            
            if (status.status.includes('completed') || status.status.includes('error')) {
                clearInterval(interval);
                
                if (status.status.includes('error')) {
                    alert('Scraping error: ' + status.error);
                } else {
                    alert('✅ Scraping completed! ' + status.ads_found + ' ads found.');
                    loadFiles();
                }
            }
        } catch (error) {
            console.error('Error monitoring progress:', error);
            clearInterval(interval);
        }
    }, 2000);
}

async function startClustering() {
    const filename = document.getElementById('file-select').value;
    
    if (!filename) {
        alert('Please select a file to analyze');
        return;
    }
    
    const taskId = 'cluster_' + Date.now();
    
    document.getElementById('cluster-progress').style.display = 'block';
    document.getElementById('cluster-results').style.display = 'none';
    
    try {
        const response = await fetch('/api/cluster', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                excel_file: `output/${filename}`,
                task_id: taskId
            })
        });
        
        const data = await response.json();
        if (data.success) {
            monitorClustering(taskId);
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error);
    }
}

async function monitorClustering(taskId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/scrape-status/${taskId}`);
            const data = await response.json();
            const status = data.status;
            
            const progress = parseInt(status.progress || 0);
            document.getElementById('cluster-progress-fill').style.width = progress + '%';
            document.getElementById('cluster-status-text').textContent = `${status.status}... ${progress}%`;
            
            if (status.status.includes('completed') || status.status.includes('error')) {
                clearInterval(interval);
                
                if (status.status.includes('error')) {
                    alert('Clustering error: ' + status.error);
                } else {
                    document.getElementById('cluster-progress').style.display = 'none';
                    document.getElementById('cluster-results').style.display = 'block';
                    document.getElementById('cluster-summary').innerHTML = `
                        <p><strong>✅ Clustering Completed!</strong></p>
                        <p>Clusters Created: ${status.clusters}</p>
                        <p><a href="${status.report_file}" target="_blank">📄 View Report</a></p>
                    `;
                    loadFiles();
                }
            }
        } catch (error) {
            console.error('Error monitoring clustering:', error);
            clearInterval(interval);
        }
    }, 2000);
}

async function loadFiles() {
    try {
        const response = await fetch('/api/files');
        const data = await response.json();
        
        const fileSelect = document.getElementById('file-select');
        fileSelect.innerHTML = '<option value="">Select a file...</option>';
        
        const excelFiles = data.files.filter(f => f.name.endsWith('.xlsx'));
        excelFiles.forEach(file => {
            const option = document.createElement('option');
            option.value = file.path;
            option.textContent = file.name;
            fileSelect.appendChild(option);
        });
        
        const filesList = document.getElementById('files-list');
        filesList.innerHTML = '';
        
        data.files.slice(0, 12).forEach(file => {
            const card = document.createElement('div');
            card.className = 'file-card';
            card.innerHTML = `
                <div class="file-name">📄 ${file.name}</div>
                <div class="file-info">${formatFileSize(file.size)}</div>
                <div class="file-date">${new Date(file.modified).toLocaleDateString()}</div>
            `;
            card.onclick = () => downloadFile(file.path);
            filesList.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

function downloadFile(filename) {
    if (!filename) {
        const selected = document.getElementById('file-select').value;
        if (!selected) {
            alert('Please select a file');
            return;
        }
        filename = selected;
    }
    
    window.location.href = `/api/download/${filename.split('/').pop()}`;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}