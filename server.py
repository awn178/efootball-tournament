import os
import json
import psycopg2
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import base64

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Database connection
def get_db():
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    return psycopg2.connect(DATABASE_URL)

# Initialize database tables
def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    # Read and execute schema
    with open('database.sql', 'r') as f:
        cur.execute(f.read())
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized!")

# Serve HTML files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')

# Test route
@app.route('/api/test')
def test():
    return jsonify({'status': 'Server is running!'})
import os
import json
import psycopg2
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import base64

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Database connection
def get_db():
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    return psycopg2.connect(DATABASE_URL)

# Initialize database tables
def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    # Read and execute schema
    with open('database.sql', 'r') as f:
        cur.execute(f.read())
    
    conn.commit()
    cur.close()
    conn.close()
    print("Database initialized!")

# Serve HTML files
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory('.', 'admin.html')

# Test route
@app.route('/api/test')
def test():
    return jsonify({'status': 'Server is running!'})
