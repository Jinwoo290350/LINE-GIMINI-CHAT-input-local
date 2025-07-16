let currentTab = 'upload-tab';

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing application...');
    initializeApp();
    updateCurrentTime();
    checkSystemStatus();
    loadFilesList();
    
    // Update time every second
    setInterval(updateCurrentTime, 1000);
    
    // Debug: Check if tabs are working
    console.log('✅ Application initialized successfully');
});

// Initialize application
function initializeApp() {
    setupEventListeners();
    updateWebhookUrl();
    
    // Make sure the first tab is active
    const firstTab = document.querySelector('.tab-button');
    const firstContent = document.querySelector('.tab-content');
    if (firstTab && firstContent) {
        firstTab.classList.add('active');
        firstContent.classList.add('active');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Single file upload form
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleSingleUpload);
    }
    
    // Multiple files upload form
    const multipleForm = document.getElementById('multipleUploadForm');
    if (multipleForm) {
        multipleForm.addEventListener('submit', handleMultipleUpload);
    }
    
    // File input changes
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    const filesInput = document.getElementById('files');
    if (filesInput) {
        filesInput.addEventListener('change', handleMultipleFileSelect);
    }
}

// Tab functionality - FIXED VERSION
function openTab(evt, tabName) {
    console.log('🔄 Opening tab:', tabName);
    
    // Hide all tab contents
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].classList.remove('active');
    }

    // Remove active class from all tab buttons
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }

    // Show selected tab content and mark button as active
    const targetTab = document.getElementById(tabName);
    if (targetTab) {
        targetTab.classList.add('active');
        console.log('✅ Tab content activated:', tabName);
    } else {
        console.error('❌ Tab not found:', tabName);
    }
    
    if (evt && evt.currentTarget) {
        evt.currentTarget.classList.add('active');
        console.log('✅ Tab button activated');
    }
    
    currentTab = tabName;
    
    // Load data for specific tabs
    if (tabName === 'files-tab') {
        console.log('📁 Loading files list...');
        loadFilesList();
    } else if (tabName === 'status-tab') {
        console.log('📊 Checking system status...');
        checkSystemStatus();
    }
}

// Handle single file upload
async function handleSingleUpload(e) {
    e.preventDefault();
    console.log('📤 Starting single file upload...');
    
    const formData = new FormData();
    const fileInput = document.getElementById('file');
    const promptInput = document.getElementById('prompt');
    const resultDiv = document.getElementById('result');
    
    if (!fileInput.files[0]) {
        showResult(resultDiv, 'error', 'กรุณาเลือกไฟล์');
        return;
    }
    
    console.log('📁 File selected:', fileInput.files[0].name);
    
    formData.append('file', fileInput.files[0]);
    formData.append('prompt', promptInput.value || 'อธิบายเนื้อหาของไฟล์นี้');
    
    showResult(resultDiv, 'loading', 'กำลังอัพโหลดและประมวลผล...');
    
    try {
        console.log('🚀 Sending request to server...');
        const response = await fetch('/api/upload/single', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        console.log('📨 Server response:', result);
        
        if (result.success) {
            const fileInfo = result.fileInfo;
            const content = `
                <h3><i class="fas fa-check-circle"></i> ประมวลผลเสร็จสิ้น</h3>
                <div class="file-details">
                    <p><strong>ไฟล์:</strong> ${fileInfo.name}</p>
                    <p><strong>ขนาด:</strong> ${fileInfo.size}</p>
                    <p><strong>ประเภท:</strong> ${fileInfo.type}</p>
                </div>
                <h4>ผลการวิเคราะห์:</h4>
                <p>${result.response}</p>
            `;
            showResult(resultDiv, 'success', content);
        } else {
            showResult(resultDiv, 'error', result.error);
        }
    } catch (error) {
        console.error('❌ Upload error:', error);
        showResult(resultDiv, 'error', 'เกิดข้อผิดพลาด: ' + error.message);
    }
}

// Handle multiple files upload
async function handleMultipleUpload(e) {
    e.preventDefault();
    console.log('📤 Starting multiple files upload...');
    
    const formData = new FormData();
    const filesInput = document.getElementById('files');
    const promptInput = document.getElementById('multiplePrompt');
    const resultDiv = document.getElementById('multipleResult');
    
    if (!filesInput.files.length) {
        showResult(resultDiv, 'error', 'กรุณาเลือกไฟล์');
        return;
    }
    
    console.log('📁 Files selected:', filesInput.files.length);
    
    // Append all files
    for (let i = 0; i < filesInput.files.length; i++) {
        formData.append('files', filesInput.files[i]);
        console.log(`📄 File ${i + 1}:`, filesInput.files[i].name);
    }
    formData.append('prompt', promptInput.value || 'อธิบายเนื้อหาของไฟล์เหล่านี้');
    
    showResult(resultDiv, 'loading', 'กำลังอัพโหลดและประมวลผลไฟล์ทั้งหมด...');
    
    try {
        const response = await fetch('/api/upload/multiple', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        console.log('📨 Server response:', result);
        
        if (result.success) {
            let filesInfoHtml = '';
            result.filesInfo.forEach((file, index) => {
                filesInfoHtml += `
                    <div class="file-item">
                        <p><strong>ไฟล์ ${index + 1}:</strong> ${file.name} (${file.size})</p>
                    </div>
                `;
            });
            
            const content = `
                <h3><i class="fas fa-check-circle"></i> ประมวลผลไฟล์ทั้งหมดเสร็จสิ้น</h3>
                <div class="files-summary">
                    <h4>ไฟล์ที่ประมวลผล (${result.filesInfo.length} ไฟล์):</h4>
                    ${filesInfoHtml}
                </div>
                <h4>ผลการวิเคราะห์:</h4>
                <p>${result.response}</p>
            `;
            showResult(resultDiv, 'success', content);
        } else {
            showResult(resultDiv, 'error', result.error);
        }
    } catch (error) {
        console.error('❌ Multiple upload error:', error);
        showResult(resultDiv, 'error', 'เกิดข้อผิดพลาด: ' + error.message);
    }
}

// Handle file selection display
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        console.log('📁 Selected file:', file.name, 'Size:', formatFileSize(file.size));
    }
}

// Handle multiple files selection display
function handleMultipleFileSelect(e) {
    const files = e.target.files;
    if (files.length) {
        console.log(`📁 Selected ${files.length} files:`);
        for (let i = 0; i < files.length; i++) {
            console.log(`- ${files[i].name} (${formatFileSize(files[i].size)})`);
        }
    }
}

// Show result in specified div
function showResult(div, type, content) {
    if (!div) {
        console.error('❌ Result div not found');
        return;
    }
    
    div.style.display = 'block';
    div.className = `result ${type}`;
    
    if (type === 'loading') {
        div.innerHTML = `<div class="loading">${content}</div>`;
    } else if (type === 'error') {
        div.innerHTML = `<h3><i class="fas fa-exclamation-triangle"></i> เกิดข้อผิดพลาด</h3><p>${content}</p>`;
    } else if (type === 'success') {
        div.innerHTML = content;
    } else {
        div.innerHTML = content;
    }
    
    // Scroll to result
    div.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Load files list
async function loadFilesList() {
    const listDiv = document.getElementById('filesList');
    if (!listDiv) {
        console.error('❌ Files list div not found');
        return;
    }
    
    listDiv.innerHTML = '<div class="loading">กำลังโหลดรายการไฟล์...</div>';
    
    try {
        console.log('📂 Loading files list...');
        const response = await fetch('/api/upload/files');
        const result = await response.json();
        console.log('📋 Files list response:', result);
        
        if (result.success) {
            if (result.files.length === 0) {
                listDiv.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">ยังไม่มีไฟล์ที่อัพโหลด</p>';
            } else {
                let filesHtml = `<h4>ไฟล์ทั้งหมด (${result.total} ไฟล์)</h4>`;
                result.files.forEach(file => {
                    filesHtml += `
                        <div class="file-item">
                            <div class="file-details">
                                <h4><i class="fas fa-file"></i> ${file.name}</h4>
                                <p><strong>ขนาด:</strong> ${file.size}</p>
                                <p><strong>อัพโหลด:</strong> ${new Date(file.created).toLocaleString('th-TH')}</p>
                                <p><strong>แก้ไขล่าสุด:</strong> ${new Date(file.modified).toLocaleString('th-TH')}</p>
                            </div>
                        </div>
                    `;
                });
                listDiv.innerHTML = filesHtml;
            }
        } else {
            listDiv.innerHTML = '<p style="color: #e74c3c;">เกิดข้อผิดพลาดในการโหลดรายการไฟล์</p>';
        }
    } catch (error) {
        console.error('❌ Files list error:', error);
        listDiv.innerHTML = '<p style="color: #e74c3c;">เกิดข้อผิดพลาด: ' + error.message + '</p>';
    }
}

// Cleanup old files
async function cleanupFiles() {
    if (!confirm('คุณต้องการลบไฟล์เก่าหรือไม่?')) {
        return;
    }
    
    try {
        console.log('🗑️ Cleaning up old files...');
        const response = await fetch('/api/upload/cleanup?apiKey=your_webhook_secret_here', {
            method: 'DELETE'
        });
        
        const result = await response.json();
        console.log('🧹 Cleanup response:', result);
        
        if (result.success) {
            alert(result.message);
            loadFilesList(); // Reload files list
        } else {
            alert('เกิดข้อผิดพลาด: ' + result.error);
        }
    } catch (error) {
        console.error('❌ Cleanup error:', error);
        alert('เกิดข้อผิดพลาด: ' + error.message);
    }
}

// Check system status
async function checkSystemStatus() {
    try {
        console.log('🔍 Checking system status...');
        const response = await fetch('/health');
        const result = await response.json();
        console.log('💚 Health check response:', result);
        
        const serverStatusEl = document.getElementById('serverStatus');
        if (serverStatusEl) {
            serverStatusEl.textContent = result.status === 'OK' ? 'ออนไลน์' : 'ออฟไลน์';
            serverStatusEl.style.color = result.status === 'OK' ? '#27ae60' : '#e74c3c';
        }
        
    } catch (error) {
        console.error('❌ Health check error:', error);
        const serverStatusEl = document.getElementById('serverStatus');
        if (serverStatusEl) {
            serverStatusEl.textContent = 'ออฟไลน์';
            serverStatusEl.style.color = '#e74c3c';
        }
    }
}

// Update current time
function updateCurrentTime() {
    const now = new Date();
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        timeElement.textContent = now.toLocaleString('th-TH');
    }
}

// Update webhook URL
function updateWebhookUrl() {
    const webhookElement = document.getElementById('webhookUrl');
    if (webhookElement) {
        const baseUrl = window.location.origin;
        webhookElement.textContent = `${baseUrl}/webhook`;
    }
}

// Format file size
function formatFileSize(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Byte';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

// Utility function for copying text
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        console.log('📋 Copied to clipboard:', text);
        alert('คัดลอกแล้ว: ' + text);
    }).catch(err => {
        console.error('❌ Copy failed:', err);
    });
}

// Make openTab function globally available
window.openTab = openTab;
window.loadFilesList = loadFilesList;
window.cleanupFiles = cleanupFiles;
window.copyToClipboard = copyToClipboard;

console.log('✅ All functions loaded successfully');
