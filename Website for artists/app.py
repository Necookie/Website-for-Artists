from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import mysql.connector
from werkzeug.utils import secure_filename
import secrets

# Generate a random secret key
secret_key = secrets.token_hex(16)

app = Flask(__name__)
app.secret_key = secret_key

# MySQL connection setup
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Replace with your DB password
        database="ecommerce_db"  # Your database name
    )

# Set upload folder and allowed extensions
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', items=items)

@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']

        if 'image' not in request.files:
            return 'No file part'

        file = request.files['image']

        if file.filename == '':
            return 'No selected file'

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO items (name, description, price, image_url) VALUES (%s, %s, %s, %s)", 
                           (name, description, price, filename))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect('/')

    return render_template('add_item.html')

@app.route('/submit_form', methods=['POST'])
def submit_form():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO information (name, email, password) VALUES (%s, %s, %s)"
    values = (name, email, password)

    cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('success', name=name))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM information WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['email'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('art_gallery'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/success')
def success():
    name = request.args.get('name')
    return render_template('success.html', name=name)

@app.route('/art')
def art_gallery():
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    # Render profile page (you may want to create profile.html)
    return render_template('profile.html')

@app.route('/settings')
def settings():
    # Render settings page (you may want to create settings.html)
    return render_template('settings.html')

@app.route('/logout')
def logout():
    session.pop('email', None)  # Remove the email from the session
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
