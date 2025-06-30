#!/usr/bin/env python3
"""
Simple test to check if Flask is working
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <html>
        <head><title>Flask Test</title></head>
        <body>
            <h1>Flask is working!</h1>
            <p>If you see this, Flask is running correctly.</p>
            <p><a href="/test">Test API endpoint</a></p>
        </body>
    </html>
    '''

@app.route('/test')
def test():
    return {'status': 'ok', 'message': 'API is working'}

if __name__ == '__main__':
    print("Starting test server on http://localhost:5001")
    app.run(debug=True, port=5001)