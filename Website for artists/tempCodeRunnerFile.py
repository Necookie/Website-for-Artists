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