#!/usr/bin/env python3
"""
Simplified Flask app with better error handling
"""

import os
import sys
from flask import Flask, render_template, jsonify
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/')
def index():
    """Serve the main web interface"""
    try:
        logger.info("Serving index.html")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return f"<h1>Error</h1><p>{str(e)}</p><p>Template path: {app.template_folder}</p>", 500

@app.route('/api/test')
def test_api():
    """Test API endpoint"""
    return jsonify({"status": "ok", "message": "API is working"})

@app.errorhandler(404)
def not_found(e):
    return f"<h1>404 Not Found</h1><p>The requested URL was not found on the server.</p><p>Working directory: {os.getcwd()}</p>", 404

@app.errorhandler(500)
def server_error(e):
    return f"<h1>500 Internal Server Error</h1><p>{str(e)}</p>", 500

if __name__ == '__main__':
    print(f"Starting server...")
    print(f"Working directory: {os.getcwd()}")
    print(f"Template folder: {app.template_folder}")
    print(f"Static folder: {app.static_folder}")
    print(f"")
    print(f"Open your browser to: http://localhost:5000")
    print(f"")
    app.run(debug=True, port=5000, host='0.0.0.0')