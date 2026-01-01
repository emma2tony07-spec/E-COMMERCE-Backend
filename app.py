from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
import re
import bcrypt
import os

app = Flask(__name__)
CORS(app)

# MySQL Configuration
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'modern_store')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

def init_db():
    """Initialize database tables"""
    try:
        cur = mysql.connection.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        mysql.connection.commit()
        cur.close()
    except Exception as e:
        print(f"DB init error: {e}")

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

        # Check existing user
        cur = mysql.connection.cursor()
        cur.execute("SELECT id FROM users WHERE email = %s OR phone = %s", (email, phone))
        if cur.fetchone():
            cur.close()
            return jsonify({'success': False, 'message': 'Email or phone already exists'}), 409

        # Create user
        password_hash = hash_password(password)
        cur.execute(
            "INSERT INTO users (email, phone, password_hash) VALUES (%s, %s, %s)",
            (email, phone, password_hash)
        )
        mysql.connection.commit()
        user_id = cur.lastrowid
        
        # Get user data
        cur.execute("SELECT id, email, phone, created_at FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        cur.close()

        return jsonify({
            'success': True,
            'message': 'Account created',
            'user': dict(user)
        }), 201

    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if not user:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        if not check_password(user['password_hash'], password):
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        user_dict = dict(user)
        user_dict.pop('password_hash', None)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user_dict
        })

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected'}), 500

# Initialize DB on startup
with app.app_context():
    init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)