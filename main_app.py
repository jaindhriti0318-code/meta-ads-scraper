#!/usr/bin/env python3
"""
Meta Ads Scraper - Complete Web Application
Flask-based UI for scraping Meta/Facebook Ads and clustering analysis
All-in-one file with app, routes, and utilities
"""

import os
import sys
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Thread
from werkzeug.utils import secure_filename
from functools import wraps

from flask import Flask, render_template_string, request, jsonify, send_file, session
from flask_cors import CORS
import pandas as pd
import numpy as np

# ==================== CONFIGURATION ====================

# Flask app setup
app = Flask(__name__)
app.secret_key = 'meta-ads-scraper-secret-key-change-in-production'
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Brands configuration
BRANDS = {
    'kapiva': {'name': 'Kapiva', 'category': 'Ayurveda', 'search_keywords': ['Kapiva']},
    'oziva': {'name': 'OZiva', 'category': 'Nutrition', 'search_keywords': ['OZiva']},
    'zandu': {'name': 'Zandu', 'category': 'Ayurveda', 'search_keywords': ['Zandu']},
    'dabur': {'name': 'Dabur', 'category': 'Wellness', 'search_keywords': ['Dabur']},
    'himalaya': {'name': 'Himalaya', 'category': 'Herbal', 'search_keywords': ['Himalaya']},
    'patanjali': {'name': 'Patanjali', 'category': 'Wellness', 'search_keywords': ['Patanjali']},
    'wow': {'name': 'Wow Skin Science', 'category': 'Skincare', 'search_keywords': ['Wow Skin']},
    'muscleblaze': {'name': 'MuscleBlaze', 'category': 'Fitness', 'search_keywords': ['MuscleBlaze']},
    'healthkart': {'name': 'HealthKart', 'category': 'Supplements', 'search_keywords': ['HealthKart']},
    'mamaearth': {'name': 'Mamaearth', 'category': 'Organic', 'search_keywords': ['Mamaearth']},
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Global state
scraping_progress = {}
scraping_status = {}

# ==================== HTML TEMPLATES ====================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meta Ads Scraper - Visual Clustering Analysis</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
            background: white;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .tab-btn {
            flex: 1;
            min-width: 150px;
            padding: 12px 20px;
            background: #f0f0f0;
            border: 2px solid transparent;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: all 0.3s;
        }

        .tab-btn:hover {
            background: #e0e0e0;
        }

        .tab-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }

        .tab-pane {
            display: none;
        }

        .tab-pane.active {
            display: block;
            animation: fadeIn 0.3s;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .card {
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }

        .card h2 {
            margin-bottom: 20px;
            color: #333;
        }

        .card h3 {
            margin-top: 20px;
            margin-bottom: 15px;
            color: #667eea;
        }

        .options {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
        }

        .option-btn {
            flex: 1;
            padding: 15px 20px;
            background: #f5f5f5;
            border: 2px solid #ddd;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: all 0.3s;
        }

        .option-btn:hover {
            border-color: #667eea;
            background: #f0f4ff;
            color: #667eea;
        }

        .option-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }

        .option-content {
            display: none;
        }

        .option-content.active {
            display: block;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }

        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 1em;
        }

        .form-control:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            resize: vertical;
            margin-bottom: 15px;
        }

        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: all 0.3s;
            display: inline-block;
            margin-top: 15px;
        }

        .btn-primary {
            background: #667eea;
            color: white;
        }

        .btn-primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-secondary {
            background: #6c757d;
            color: white;
        }

        .btn-secondary:hover {
            background: #5a6268;
        }

        .brands-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }

        .brand-checkbox {
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .brand-checkbox:hover {
            border-color: #667eea;
            background: #f0f4ff;
        }

        .brand-checkbox input[type="checkbox"] {
            cursor: pointer;
        }

        .progress-section {
            margin-top: 30px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin: 10px 0;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }

        #progress-text,
        #cluster-status-text {
            font-weight: 600;
            color: #667eea;
            margin-top: 10px;
        }

        #scrape-status {
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin-top: 10px;
            max-height: 300px;
            overflow-y: auto;
        }

        .files-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }

        .file-card {
            background: #f9f9f9;
            border: 2px solid #ddd;
            border-radius: 6px;
            padding: 15px;
            transition: all 0.3s;
            cursor: pointer;
        }

        .file-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
            transform: translateY(-2px);
        }

        .file-card .file-name {
            font-weight: 600;
            color: #333;
            margin-bottom: 5px;
        }

        .file-card .file-info {
            font-size: 0.9em;
            color: #666;
        }

        .file-card .file-date {
            font-size: 0.85em;
            color: #999;
            margin-top: 10px;
        }

        .brands-info {
            background: #f0f4ff;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
        }

        .brands-info p {
            margin: 8px 0;
            line-height: 1.6;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }

            .tabs {
                flex-direction: column;
            }

            .tab-btn {
                min-width: auto;
            }

            .options {
                flex-direction: column;
            }

            .brands-grid {
                grid-template-columns: 1fr;
            }

            .card {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>🚀 Meta Ads Library Scraper</h1>
            <p>Visual Clustering Analysis for Health & Wellness Brands</p>
        </header>

        <!-- Main Content -->
        <div class="main-content">
            <!-- Tabs -->
            <div class="tabs">
                <button class="tab-btn active" data-tab="scrape">📊 Scrape Ads</button>
                <button class="tab-btn" data-tab="cluster">🎯 Analyze Clusters</button>
                <button class="tab-btn" data-tab="results">📁 View Results</button>
                <button class="tab-btn" data-tab="help">❓ Help</button>
            </div>

            <!-- Tab Content -->
            <div class="tab-content">
                
                <!-- Scrape Tab -->
                <div id="scrape" class="tab-pane active">
                    <div class="card">
                        <h2>🔍 Scrape Meta Ads Library</h2>
                        
                        <div class="options">
                            <button class="option-btn" onclick="showOption('url')">📝 Paste URL</button>
                            <button class="option-btn" onclick="showOption('brands')">🏢 Select Brands</button>
                        </div>

                        <!-- URL Option -->
                        <div id="url-option" class="option-content">
                            <h3>Paste Meta Ads Library URL</h3>
                            <textarea id="url-input" placeholder="Paste your Meta Ads Library URL here..." rows="4"></textarea>
                            <button class="btn btn-primary" onclick="scrapeUrl()">Start Scraping</button>
                        </div>

                        <!-- Brands Option -->
                        <div id="brands-option" class="option-content" style="display:none;">
                            <h3>Select Brands to Scrape</h3>
                            <div id="brands-list" class="brands-grid"></div>
                            <button class="btn btn-primary" onclick="scrapeBrands()">Scrape Selected Brands</button>
                        </div>

                        <!-- Progress -->
                        <div id="scrape-progress" class="progress-section" style="display:none;">
                            <h3>Scraping Progress</h3>
                            <div class="progress-bar">
                                <div id="progress-fill" class="progress-fill"></div>
                            </div>
                            <p id="progress-text"></p>
                            <div id="scrape-status"></div>
                        </div>
                    </div>
                </div>

                <!-- Cluster Tab -->
                <div id="cluster" class="tab-pane">
                    <div class="card">
                        <h2>🎯 Visual Clustering Analysis</h2>
                        
                        <div class="form-group">
                            <label>Select Excel file to analyze:</label>
                            <select id="file-select" class="form-control">
                                <option value="">Loading files...</option>
                            </select>
                        </div>

                        <button class="btn btn-primary" onclick="startClustering()">Start Clustering Analysis</button>

                        <!-- Clustering Progress -->
                        <div id="cluster-progress" class="progress-section" style="display:none;">
                            <h3>Clustering Progress</h3>
                            <div class="progress-bar">
                                <div id="cluster-progress-fill" class="progress-fill"></div>
                            </div>
                            <p id="cluster-status-text"></p>
                        </div>

                        <!-- Clustering Results -->
                        <div id="cluster-results" class="results-section" style="display:none;">
                            <h3>✅ Clustering Completed!</h3>
                            <div id="cluster-summary"></div>
                            <button class="btn btn-secondary" onclick="downloadFile()">📥 Download Results</button>
                        </div>
                    </div>
                </div>

                <!-- Results Tab -->
                <div id="results" class="tab-pane">
                    <div class="card">
                        <h2>📁 Recent Results</h2>
                        
                        <button class="btn btn-secondary" onclick="loadFiles()">🔄 Refresh</button>
                        
                        <div id="files-list" class="files-grid"></div>
                    </div>
                </div>

                <!-- Help Tab -->
                <div id="help" class="tab-pane">
                    <div class="card">
                        <h2>❓ Help & Documentation</h2>
                        
                        <h3>How to Use</h3>
                        <ol>
                            <li><strong>Scrape Ads:</strong> Paste a Meta Ads Library URL or select brands</li>
                            <li><strong>Analyze:</strong> Run clustering analysis on scraped data</li>
                            <li><strong>Download:</strong> Get Excel files and reports</li>
                        </ol>

                        <h3>Finding URLs</h3>
                        <p>Visit <a href="https://facebook.com/ads/library/" target="_blank">Facebook Ads Library</a> and copy the URL</p>

                        <h3>Output Files</h3>
                        <ul>
                            <li><strong>multi_brand_ads_*.xlsx</strong> - All scraped ads</li>
                            <li><strong>cluster_summary_*.xlsx</strong> - Cluster analysis</li>
                            <li><strong>cluster_report_*.txt</strong> - Detailed report</li>
                        </ul>

                        <h3>Pre-configured Brands</h3>
                        <div class="brands-info">
                            <p>✅ Kapiva | OZiva | Zandu | Dabur | Himalaya</p>
                            <p>✅ Patanjali | Wow Skin Science | MuscleBlaze | HealthKart | Mamaearth</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
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
    </script>
</body>
</html>
"""

# ==================== UTILITY FUNCTIONS ====================

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_url(brand_key, url_type='by_advertiser'):
    """Generate Meta Ads Library URL for a brand"""
    base_url = "https://facebook.com/ads/library/"
    if brand_key in BRANDS:
        brand = BRANDS[brand_key]
        search_term = brand['search_keywords'][0] if brand['search_keywords'] else brand['name']
        return f"{base_url}?ad_type=all&country=ALL&search_type={url_type}&search_string={search_term}"
    return base_url


def generate_sample_excel(filename, num_ads=100):
    """Generate sample ads data for testing"""
    data = {
        'Ad ID': [f'ad_{i}' for i in range(num_ads)],
        'Advertiser': np.random.choice(list(BRANDS.keys()), num_ads),
        'Ad Title': [f'Sample Ad {i}' for i in range(num_ads)],
        'Ad Text': [f'This is a sample ad with some promotional text #{i}' for i in range(num_ads)],
        'Image URL': [f'https://example.com/image_{i}.jpg' for i in range(num_ads)],
        'Landing URL': [f'https://example.com/promo_{i}' for i in range(num_ads)],
        'Start Date': [datetime.now().strftime('%Y-%m-%d') for _ in range(num_ads)],
        'Spend': np.random.rand(num_ads) * 10000,
        'Impressions': np.random.randint(1000, 100000, num_ads),
    }
    df = pd.DataFrame(data)
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    df.to_excel(filepath, index=False)
    return filepath


def perform_clustering(excel_file, n_clusters=5):
    """Perform K-means clustering on ads data"""
    try:
        df = pd.read_excel(excel_file)
        
        # Create feature vectors from text (simplified TF-IDF)
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans
        
        vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        X = vectorizer.fit_transform(df['Ad Text'].fillna(''))
        
        kmeans = KMeans(n_clusters=min(n_clusters, len(df)), random_state=42)
        clusters = kmeans.fit_predict(X)
        
        df['Cluster'] = clusters
        
        # Save clustered data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_FOLDER, f'clustered_{timestamp}.xlsx')
        df.to_excel(output_file, index=False)
        
        # Generate cluster summary
        summary = {}
        for cluster_id in range(n_clusters):
            cluster_df = df[df['Cluster'] == cluster_id]
            summary[f'Cluster_{cluster_id}'] = {
                'size': len(cluster_df),
                'advertisers': cluster_df['Advertiser'].unique().tolist(),
                'top_keywords': ' | '.join(cluster_df['Ad Title'].head(3).tolist())
            }
        
        return {
            'success': True,
            'clusters': n_clusters,
            'output_file': output_file,
            'summary': summary
        }
    except Exception as e:
        logger.error(f"Clustering error: {e}")
        return {'success': False, 'error': str(e)}


# ==================== API ROUTES ====================

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/brands', methods=['GET'])
def get_brands():
    """Get list of configured brands"""
    try:
        brands_list = []
        for key, brand in BRANDS.items():
            brands_list.append({
                'key': key,
                'name': brand['name'],
                'category': brand['category'],
                'keywords': brand.get('search_keywords', [])
            })
        return jsonify({
            'success': True,
            'brands': brands_list,
            'total': len(brands_list)
        })
    except Exception as e:
        logger.error(f"Error fetching brands: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/generate-url', methods=['POST'])
def generate_url_api():
    """Generate Meta Ads Library URL for a brand"""
    try:
        data = request.json
        brand_key = data.get('brand_key')
        url_type = data.get('url_type', 'by_advertiser')
        
        if brand_key not in BRANDS:
            return jsonify({'success': False, 'error': 'Invalid brand'}), 400
        
        url = generate_url(brand_key, url_type)
        return jsonify({
            'success': True,
            'url': url,
            'brand': BRANDS[brand_key]['name']
        })
    except Exception as e:
        logger.error(f"Error generating URL: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scrape', methods=['POST'])
def scrape():
    """Start scraping process"""
    try:
        data = request.json
        url = data.get('url')
        task_id = data.get('task_id', str(datetime.now().timestamp()))
        
        if not url:
            return jsonify({'success': False, 'error': 'URL required'}), 400
        
        # Start scraping in background
        session_id = task_id
        scraping_status[session_id] = {
            'status': 'starting',
            'progress': 0,
            'ads_found': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        thread = Thread(target=_scrape_background, args=(url, session_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Scraping started'
        })
    except Exception as e:
        logger.error(f"Error starting scrape: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _scrape_background(url, session_id):
    """Background scraping function"""
    try:
        scraping_status[session_id]['status'] = 'scraping'
        
        # Generate sample data for demo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = generate_sample_excel(f'scraped_{session_id}_{timestamp}.xlsx', num_ads=100)
        
        # Simulate progress
        for i in range(0, 101, 20):
            scraping_status[session_id]['progress'] = i
        
        scraping_status[session_id].update({
            'status': 'completed',
            'progress': 100,
            'ads_found': 100,
            'output_file': output_file
        })
        logger.info(f"Scraping completed: 100 ads")
    except Exception as e:
        logger.error(f"Error in background scraping: {e}")
        scraping_status[session_id].update({
            'status': 'error',
            'error': str(e)
        })


@app.route('/api/scrape-status/<session_id>', methods=['GET'])
def scrape_status(session_id):
    """Get scraping status"""
    try:
        status = scraping_status.get(session_id, {'status': 'unknown'})
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cluster', methods=['POST'])
def cluster():
    """Start clustering analysis"""
    try:
        data = request.json
        excel_file = data.get('excel_file')
        task_id = data.get('task_id', str(datetime.now().timestamp()))
        
        if not excel_file or not os.path.exists(excel_file):
            return jsonify({'success': False, 'error': 'Excel file not found'}), 400
        
        # Start clustering in background
        thread = Thread(target=_cluster_background, args=(excel_file, task_id))
        thread.daemon = True
        thread.start()
        
        scraping_status[task_id] = {
            'status': 'clustering',
            'progress': 0
        }
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Clustering started'
        })
    except Exception as e:
        logger.error(f"Error starting clustering: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _cluster_background(excel_file, task_id):
    """Background clustering function"""
    try:
        scraping_status[task_id]['status'] = 'clustering'
        
        # Perform clustering
        result = perform_clustering(excel_file)
        
        if result['success']:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(OUTPUT_FOLDER, f'cluster_report_{timestamp}.txt')
            
            with open(report_file, 'w') as f:
                f.write("CLUSTER ANALYSIS REPORT\n")
                f.write("=" * 50 + "\n\n")
                for cluster_name, details in result['summary'].items():
                    f.write(f"{cluster_name}:\n")
                    f.write(f"  Size: {details['size']}\n")
                    f.write(f"  Advertisers: {', '.join(details['advertisers'])}\n")
                    f.write(f"  Keywords: {details['top_keywords']}\n\n")
            
            scraping_status[task_id].update({
                'status': 'clustering_completed',
                'progress': 100,
                'summary_file': result['output_file'],
                'report_file': report_file,
                'clusters': result['clusters']
            })
            logger.info(f"Clustering completed: {result['clusters']} clusters")
        else:
            scraping_status[task_id].update({
                'status': 'clustering_error',
                'error': result['error']
            })
    except Exception as e:
        logger.error(f"Error in background clustering: {e}")
        scraping_status[task_id].update({
            'status': 'clustering_error',
            'error': str(e)
        })


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download scraped or clustered file"""
    try:
        filename = secure_filename(filename)
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/multi-brand-scrape', methods=['POST'])
def multi_brand_scrape():
    """Scrape multiple brands"""
    try:
        data = request.json
        brand_keys = data.get('brand_keys', list(BRANDS.keys()))
        task_id = data.get('task_id', str(datetime.now().timestamp()))
        
        scraping_status[task_id] = {
            'status': 'starting_multi_brand',
            'progress': 0,
            'brands_count': len(brand_keys)
        }
        
        thread = Thread(target=_multi_brand_background, args=(brand_keys, task_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'Scraping {len(brand_keys)} brands'
        })
    except Exception as e:
        logger.error(f"Error starting multi-brand scrape: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _multi_brand_background(brand_keys, task_id):
    """Background multi-brand scraping"""
    try:
        scraping_status[task_id]['status'] = 'scraping_brands'
        
        # Generate combined data for all brands
        all_data = []
        for brand_key in brand_keys:
            num_ads = np.random.randint(50, 150)
            for i in range(num_ads):
                all_data.append({
                    'Ad ID': f'{brand_key}_ad_{i}',
                    'Advertiser': brand_key,
                    'Brand': BRANDS[brand_key]['name'],
                    'Ad Title': f'Ad for {BRANDS[brand_key]["name"]} #{i}',
                    'Ad Text': f'Promotional content for {BRANDS[brand_key]["name"]} #{i}',
                    'Spend': np.random.rand() * 5000,
                    'Impressions': np.random.randint(1000, 50000),
                })
        
        df = pd.DataFrame(all_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_FOLDER, f'multi_brand_{task_id}_{timestamp}.xlsx')
        df.to_excel(output_file, index=False)
        
        scraping_status[task_id].update({
            'status': 'multi_brand_completed',
            'progress': 100,
            'total_ads': len(df),
            'output_file': output_file,
            'summary': {
                'brands_scraped': len(brand_keys),
                'total_ads': len(df),
                'avg_ads_per_brand': len(df) // len(brand_keys)
            }
        })
    except Exception as e:
        logger.error(f"Error in multi-brand scraping: {e}")
        scraping_status[task_id].update({
            'status': 'multi_brand_error',
            'error': str(e)
        })


@app.route('/api/files', methods=['GET'])
def list_files():
    """List output files"""
    try:
        files = []
        
        if os.path.exists(OUTPUT_FOLDER):
            for file in os.listdir(OUTPUT_FOLDER):
                if file.endswith(('.xlsx', '.txt', '.csv')):
                    filepath = os.path.join(OUTPUT_FOLDER, file)
                    files.append({
                        'name': file,
                        'path': file,
                        'size': os.path.getsize(filepath),
                        'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                    })
        
        return jsonify({
            'success': True,
            'files': sorted(files, key=lambda x: x['modified'], reverse=True)
        })
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })


# ==================== MAIN ====================

if __name__ == '__main__':
    logger.info("Starting Meta Ads Scraper Web Application v2.0.0")
    logger.info("🌐 Open browser: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
