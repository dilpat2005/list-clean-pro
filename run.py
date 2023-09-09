from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from config import config
import os
from psycopg2.extensions import parse_dsn


template_dir = os.path.abspath('templates')
app = Flask(__name__, template_folder=template_dir)
app.secret_key = '1234'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, role=None):
        self.id = id
        self.username = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, role, username FROM users WHERE user_id = %s', (user_id,))
    user_data = cursor.fetchone()
    conn.close()

    if user_data and len(user_data) == 3:
        return User(id=user_data[0], role=user_data[1], username=user_data[2])
    return None

@app.route('/add_notes/<int:id>', methods=['POST'])
@login_required
def add_notes(id):
    note_content = request.form['notes_content']
    conn = connect()
    cursor = conn.cursor()
    cursor.execute('UPDATE items SET notes = %s WHERE id = %s', (note_content, id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = connect()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, password_hash FROM users WHERE username = %s', (username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and check_password_hash(user_data[1], password):
            user = User(id=user_data[0], username=username)
            login_user(user)
            return redirect(url_for('view_other_lists'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = 'admin' if request.form.get('role') == 'admin' else 'user'
        if role == 'admin':
                print ('setting admin role')
        conn = connect()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password_hash, email, role) VALUES (%s, %s, %s, %s)', (username, password, email, role))
            conn.commit()
        except psycopg2.IntegrityError:
            flash('Username already exists.')
        except Exception as e:
            print(f"Error while registering: {e}")
            flash('Error occurred. Please try again.')
        finally:
            conn.close()
            return redirect(url_for('login'))
    return render_template('register.html')


def get_column_headers(column):
    connection = None
    try:
        params = config()
        print('Connecting to SQL database...')
        connection = psycopg2.connect(**params)
        cursor = connection.cursor()

        query = f"SELECT {column} FROM your_table LIMIT 0;"
        cursor.execute(query)

        colnames = [desc[0] for desc in cursor.description]
        return colnames

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()
            print('Database connection ended')

def connect():
    connection = None
    try:
        params = config()
        print('Connecting to sql database...')
        connection = psycopg2.connect(**params)
        return connection
    except(Exception, psycopg2.DatabaseError) as error:
        print(error)


@app.route('/assign_rooms', methods=['POST','GET'])
@login_required
def assign_rooms():
    conn = connect()
    cursor = conn.cursor()

    if current_user.role != 'admin':
        flash('You do not have permission to assign rooms.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        selected_rooms = request.form.getlist('room')
        user_id = request.form['user_id']

        for room in selected_rooms:
            # Check if room is already assigned
            cursor.execute('SELECT * FROM items WHERE content = %s', (room,))
            existing_assignment = cursor.fetchone()
            if existing_assignment:
                flash(f'Room {room} is already assigned. Choose another room.')
                return redirect(url_for('assign_rooms'))

        # Get the room status (Stay Over or Checkout)
            status = request.form.get('status' + room)
            
        # Assign each room to the user and include status in content.
            room_with_status = f"Room {room} ({status})"
        
            cursor.execute('INSERT INTO items (content, user_id,task_type) VALUES (%s, %s, %s)', (room_with_status, user_id, status))

        conn.commit()
        conn.close()

        flash(f'Rooms {", ".join(selected_rooms)} have been assigned.')
        return redirect(url_for('index'))

    # If request.method is 'GET', we fetch already assigned rooms to display them as disabled in the form
    cursor.execute('SELECT content FROM items')
    assigned_rooms = [room[0] for room in cursor.fetchall()]
    cursor.execute('SELECT user_id, username FROM users')
    users = cursor.fetchall()
    conn.close()

    return render_template('assign_rooms.html',assigned_rooms=assigned_rooms, users=users)


@app.route('/assign_task', methods=['POST'])
@login_required
def assign_task():

    if current_user.role == 'admin':
        content = request.form['content']
        user_id = int(request.form.get('user_id', current_user.id))

        conn = connect()
        cursor = conn.cursor()

        cursor.execute('INSERT INTO items (content, user_id) VALUES (%s, %s)', (content, user_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


@app.route('/')
@login_required
def index():
    conn = connect()
    cursor = conn.cursor()
    
    # Fetch tasks assigned to the logged-in user
    cursor.execute('SELECT items.id, items.content, items.is_completed, items.notes,items.task_type, users.username FROM items JOIN users ON items.user_id = users.user_id WHERE items.user_id = %s', (current_user.id,))
    
    items = cursor.fetchall()
    cursor.execute('SELECT user_id, username FROM users')
    users = cursor.fetchall()
    conn.close()

    return render_template('index.html', items=items, users = users)


@app.route('/view_other_lists')
@login_required
def view_other_lists():
    if current_user.role != 'admin':
        flash('You do not have permission to view other lists.')
        return redirect(url_for('index'))

    user_id = request.args.get('user_id', default=None, type=int)
    conn = connect()
    cursor = conn.cursor()

    # If no specific user is selected, fetch all tasks
    if user_id is None:
        cursor.execute('SELECT items.id, items.content, items.is_completed, users.username,items.task_type,items.notes FROM items JOIN users ON items.user_id = users.user_id')
    # If a user is selected, fetch tasks for that user
    else:
        cursor.execute('SELECT items.id, items.content, items.is_completed, users.username,items.task_type, items.notes FROM items JOIN users ON items.user_id = users.user_id WHERE items.user_id = %s', (user_id,))
    
    

    items = cursor.fetchall()

    # Fetch the list of all users for the dropdown menu
    cursor.execute('SELECT user_id, username FROM users')
    users = cursor.fetchall()
    
    conn.close()

    return render_template('view_other_lists.html',items=items, users=users, selected_user_id=user_id)


@app.route('/clear_all', methods=['POST'])
@login_required
def clear_all():
    if current_user.role != 'admin':
        flash('You do not have permission to clear all tasks.')
        return redirect(url_for('view_other_lists'))

    conn = connect()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM items')
    conn.commit()
    conn.close()

    flash('All tasks have been cleared.')
    return redirect(url_for('view_other_lists'))


@app.route('/complete/<int:id>')
@login_required
def complete(id):
    conn = connect()
    cursor = conn.cursor()
    
    if current_user.role == 'admin':
        cursor.execute('UPDATE items SET is_completed = TRUE WHERE id = %s', (id,))
    else:
        cursor.execute('SELECT * FROM items WHERE id = %s AND user_id = %s', (id, current_user.id))
        item = cursor.fetchone()
    
        if not item:
            flash('Item not found or you do not have permission to complete this item.')
            return redirect(url_for('view_other_lists'))

        cursor.execute('UPDATE items SET is_completed = TRUE WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))



@app.route('/delete/<int:id>')
@login_required
def delete(id):
    conn = connect()
    cursor = conn.cursor()

    if current_user.role == 'admin':
        cursor.execute('DELETE FROM items WHERE id = %s', (id,))
    else:
        flash('Item not found or you do not have permission to delete this item.')
        return redirect(url_for('view_other_lists'))

    conn.commit()
    conn.close()
    return redirect(url_for('view_other_lists'))
