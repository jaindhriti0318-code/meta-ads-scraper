#!/usr/bin/env python3
"""
Web Application for Meta Ads Scraper
Flask-based UI for scraping and clustering ads
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from threading import Thread
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
import pandas as pd

# Import scraper modules
from scraper import MetaAdsScraper
from cluster_analysis import AdClusterer
import brands_config
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.secret_key = 'meta-ads-scraper-secret-key'
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)

# Global state for scraping progress
scraping_progress = {}
scraping_status = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/brands', methods=['GET'])
def get_brands():
    """Get list of configured brands"""
    try:
        brands_list = []
        for key, brand in brands_config.BRANDS.items():
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
def generate_url():
    """Generate Meta Ads Library URL for a brand"""
    try:
        data = request.json
        brand_key = data.get('brand_key')
        url_type = data.get('url_type', 'by_advertiser')
        
        if brand_key not in brands_config.BRANDS:
            return jsonify({'success': False, 'error': 'Invalid brand'}), 400
        
        url = brands_config.generate_url(brand_key, url_type)
        return jsonify({
            'success': True,
            'url': url,
            'brand': brands_config.BRANDS[brand_key]['name']
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
        
        scraper = MetaAdsScraper()
        ads_data = scraper.scrape(url)
        
        if ads_data:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = scraper.export_to_excel(f"scraped_{session_id}_{timestamp}.xlsx")
            
            scraping_status[session_id].update({
                'status': 'completed',
                'progress': 100,
                'ads_found': len(ads_data),
                'output_file': output_file
            })
            logger.info(f"Scraping completed: {len(ads_data)} ads")
        else:
            scraping_status[session_id].update({
                'status': 'no_ads',
                'progress': 100,
                'ads_found': 0
            })
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
        
        clusterer = AdClusterer(excel_file)
        clusterer.load_data()
        clusterer.perform_clustering()
        clusterer.analyze_clusters()
        
        summary_file = clusterer.export_analysis()
        report_file = clusterer.generate_report()
        
        scraping_status[task_id].update({
            'status': 'clustering_completed',
            'progress': 100,
            'summary_file': summary_file,
            'report_file': report_file,
            'clusters': len(clusterer.cluster_analysis)
        })
        logger.info(f"Clustering completed: {len(clusterer.cluster_analysis)} clusters")
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
        file_path = os.path.join(config.OUTPUT_FOLDER, filename)
        
        if not os.path.exists(file_path):
            # Try clusters folder
            file_path = os.path.join(config.CLUSTER_OUTPUT_FOLDER, filename)
        
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
        brand_keys = data.get('brand_keys', list(brands_config.BRANDS.keys()))
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
        from multi_brand_scraper import MultiBrandScraper
        
        scraping_status[task_id]['status'] = 'scraping_brands'
        scraper = MultiBrandScraper()
        scraper.scrape_multiple_brands(brand_keys)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = scraper.export_to_excel(f"multi_brand_{task_id}_{timestamp}.xlsx")
        
        scraping_status[task_id].update({
            'status': 'multi_brand_completed',
            'progress': 100,
            'total_ads': scraper.scrape_summary.get('total_ads', 0),
            'output_file': output_file,
            'summary': scraper.scrape_summary
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
        
        # List Excel files
        for folder in [config.OUTPUT_FOLDER, config.CLUSTER_OUTPUT_FOLDER]:
            if os.path.exists(folder):
                for file in os.listdir(folder):
                    if file.endswith('.xlsx') or file.endswith('.txt'):
                        filepath = os.path.join(folder, file)
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


if __name__ == '__main__':
    logger.info("Starting Meta Ads Scraper Web Application")
    app.run(debug=True, host='0.0.0.0', port=5000)
