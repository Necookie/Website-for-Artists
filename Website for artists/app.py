from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
import mysql.connector
from werkzeug.utils import secure_filename
import secrets
from functools import wraps
from sqlalchemy.orm import Session

# Generate a random secret key
secret_key = os.getenv('SECRET_KEY')
app = Flask(__name__)
app.secret_key = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ecommerce_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['USE_TSL'] = True
app.config['USE_SSL'] = False
db = SQLAlchemy(app)

class Information(db.Model):
    __tablename__ = 'information'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))  # Password stored in plain text
    bio = db.Column(db.String(255))
    profile_picture = db.Column(db.String(255))
    role = db.Column(db.String(50))
    followers = db.Column(db.Integer)
    rating = db.Column(db.Float)

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
    password = request.form['password']  # Storing password in plain text

    # Default role for new users
    role = 'guest'  # Set the default role to guest

    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "INSERT INTO information (name, email, password, role) VALUES (%s, %s, %s, %s)"
    values = (name, email, password, role)  # Directly use the password

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

        print(f"Attempting to log in with email: {email} and password: {password}")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM information WHERE email = %s", (email,))
        user = cursor.fetchone()    
        cursor.close()
        conn.close()

        if user:
            print(f"User found: {user}")  # Debug message
            # Assuming the password is at index 3 (check the correct index)
            print(user)
            if user[4] == password:  # Check password directly
                
                print(password)
                session['email'] = email
                session['role'] = user[7]  # Assuming role is the fifth column in your table
                flash('Login successful!', 'success')
                return redirect(url_for('art_gallery'))
            else:
                print("Password does not match.")  # Debug message
        else:
            print("User not found.")  # Debug message
        
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
    user_id = session.get('email')
    if not user_id:
        return redirect(url_for('login'))

    # Fetch the user with db.session instead of creating a new session
    user = db.session.query(Information).filter_by(email=user_id).first()
    if user is None:
        return "User not found", 404

    return render_template('profile.html', user=user)


@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'email' not in session:
        flash('Please log in to update your profile.', 'danger')
        return redirect(url_for('login'))

    # Retrieve form data
    name = request.form['name']
    bio = request.form['bio']
    user_id = session.get('user_id')  # Assume you've stored `user_id` in session during login

    # Handle profile image upload
    file = request.files['profile_image']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        profile_image = filename
    else:
        profile_image = None

    # Update profile in database
    conn = get_db_connection()
    cursor = conn.cursor()
    if profile_image:
        cursor.execute("UPDATE profiles SET name = %s, bio = %s, profile_image = %s WHERE user_id = %s",
                       (name, bio, profile_image, user_id))
    else:
        cursor.execute("UPDATE profiles SET name = %s, bio = %s WHERE user_id = %s", (name, bio, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/settings')
def settings():
    # Render settings page (you may want to create settings.html)
    return render_template('settings.html')

@app.route('/logout')
def logout():
    session.pop('email', None)  # Remove the email from the session
    session.pop('role', None)  # Remove the role from the session
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
