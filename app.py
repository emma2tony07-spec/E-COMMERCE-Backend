import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import bcrypt
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

# Get database URL from Render environment
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Create database connection"""
    conn = psycopg2.connect(DATABASE_URL, 
                           cursor_factory=RealDictCursor)
    return conn

def init_db():
    """Initialize database tables"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Create users table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

def hash_password(password):
    """Hash password"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(hashed, password):
    """Verify password"""
    return bcrypt.checkpw(password.encode(), hashed.encode())

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')

        # Validation
        if not all([email, phone, password]):
            return jsonify({'success': False, 'message': 'All fields required'}), 400
        
        if len(password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Check existing user
        cur.execute(
            "SELECT id FROM users WHERE email = %s OR phone = %s",
            (email, phone)
        )
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Email or phone already exists'}), 409

        # Create user
        password_hash = hash_password(password)
        cur.execute(
            "INSERT INTO users (email, phone, password_hash) VALUES (%s, %s, %s) RETURNING id, email, phone, created_at",
            (email, phone, password_hash)
        )
        
        user = cur.fetchone()
        conn.commit()
        
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': dict(user)
        }), 201

    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'service': 'postgresql'
        }), 200
    except Exception as e:
        print(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

# Initialize database on startup
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
