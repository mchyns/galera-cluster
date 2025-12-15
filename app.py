from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Database Configuration - Connect to HAProxy
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3300,
    'user': 'root',
    'password': '030105',
    'database': 'beauty'
}

def get_db_connection():
    """Create database connection through HAProxy"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to database: {e}")
        return None

def get_current_node():
    """Get the hostname of the current database node handling the request"""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("SELECT @@hostname")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            return result[0] if result else "Unknown"
    except Error as e:
        print(f"Error getting hostname: {e}")
        return "Error"
    return "Unknown"

def init_database():
    """Initialize database and create products table if not exists"""
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    stock INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.commit()
            cursor.close()
            connection.close()
            print("Database initialized successfully")
    except Error as e:
        print(f"Error initializing database: {e}")

@app.route('/')
def index():
    """Display product list with system info badge"""
    products = []
    node_info = get_current_node()
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
            products = cursor.fetchall()
            cursor.close()
            connection.close()
    except Error as e:
        flash(f'Error fetching products: {str(e)}', 'danger')
    
    return render_template('index.html', products=products, node_info=node_info)

@app.route('/store', methods=['POST'])
def store():
    """Insert new product into database"""
    name = request.form.get('name')
    price = request.form.get('price')
    stock = request.form.get('stock')
    
    if not name or not price or not stock:
        flash('All fields are required!', 'warning')
        return redirect(url_for('index'))
    
    try:
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
                (name, float(price), int(stock))
            )
            connection.commit()
            cursor.close()
            connection.close()
            flash(f'Product "{name}" added successfully!', 'success')
        else:
            flash('Database connection failed!', 'danger')
    except Error as e:
        flash(f'Error adding product: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Initialize database on startup
    init_database()
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
