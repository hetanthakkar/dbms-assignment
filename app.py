from datetime import datetime

from flask import Flask
from flaskext.mysql import MySQL
from flask import request
from flask_bcrypt import Bcrypt
from flask import jsonify
from flask_socketio import SocketIO
from flask import render_template
from flask_socketio import emit

app = Flask(__name__)
mysql = MySQL()
bcrypt = Bcrypt(app)
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Zlh19980901.'
app.config['MYSQL_DATABASE_DB'] = 'skillshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
conn = mysql.connect()
cursor =conn.cursor()
socketio = SocketIO()


@app.route('/')
def index():
	data=cursor.fetchall()
	print(data)
	return 'Hello, Flask!'


def generate_password_hash(password):
    pw_hash = bcrypt.generate_password_hash(password)
    return pw_hash

def check_if_email_exists(email,role):
    if role:
        cursor.execute('SELECT COUNT(*) FROM student WHERE email = %s', (email))
        count = cursor.fetchone()[0]
    else:
        cursor.execute('SELECT COUNT(*) FROM teacher WHERE email = %s', (email))
        count = cursor.fetchone()[0]
    return count > 0

def insert_user(name, email, password_hash,role):
    if role:
        cursor.execute('INSERT INTO student (name, email, password) VALUES (%s, %s, %s)',
                   (name, email, password_hash))
        conn.commit()
    else:
                cursor.execute('INSERT INTO teacher (name, email, password) VALUES (%s, %s, %s)',
                   (name, email, password_hash))
                conn.commit()

def get_user_by_email(email,role):
    if role:
        cursor.execute('SELECT * FROM student WHERE email = %s', (email))
        user = cursor.fetchone()
    else:
        cursor.execute('SELECT * FROM teacher WHERE email = %s', (email))
        user = cursor.fetchone()
    # print("fetched student",student)
    return user

def check_password_hash(password, password_hash):
    return bcrypt.check_password_hash(password_hash,password)


def create_account(name, email, password,role):
    hashed_password = generate_password_hash(password)

    email_exists = check_if_email_exists(email,role)
    if email_exists:
        raise ValueError('Email already exists')

    insert_user(name, email, hashed_password,role )

def validate_login(email, password,role):
    user = get_user_by_email(email,role)
    if not user:
        return None

    if not check_password_hash(password, user[2]):
        return None

    if role:
        return {
            'student_id': user[0],
            'name': user[1],
            'email': user[3],
        }
    else:
         return {
            'teacher_id': user[0],
            'name': user[1],
            'email': user[3],
        }

@app.route('/user/signup', methods=['POST'])
def signup_student():
    signup_data = request.get_json()
    name = signup_data['name']
    email = signup_data['email']
    password = signup_data['password']
    role = signup_data['role']

    create_account(name, email, password,role)

    return jsonify({'message': 'Signup successful'})



def get_categories():
    # Connect to the database

    # Execute query to retrieve all categories
    cursor.execute('SELECT * FROM category')
    categories = cursor.fetchall()

    # Close the database connection

    # Convert database records to Python objects
    category_list = []
    if categories:
        for category in categories:
            print('this is cat',category)
            category_obj = {
                'cat_id': category[0],
                'name': category[1],
                'description': category[2]
            }
            category_list.append(category_obj)

    return category_list

def get_subcategories_by_category_id(category_id):
    # Connect to the database

    # Execute query to retrieve subcategories for the specified category
    cursor.execute('SELECT * FROM subcategory WHERE cat_id = %s', (category_id,))
    subcategories = cursor.fetchall()

    # Close the database connection

    # Convert database records to Python objects
    subcategory_list = []
    for subcategory in subcategories:
        subcategory_obj = {
            'subcat_id': subcategory[1],
            'name': subcategory[2]
        }
        subcategory_list.append(subcategory_obj)

    return subcategory_list

def insert_category_record(name, description):


    # Check if category name already exists
    cursor.execute('SELECT COUNT(*) FROM category WHERE name = %s', (name,))
    category_exists = cursor.fetchone()[0] > 0

    # Validate category data
    if category_exists:
        raise ValueError('Category name already exists')

    # Insert new category record into database
    cursor.execute('INSERT INTO category (name, description) VALUES (%s, %s)', (name, description))
    conn.commit()

    # Close the database connection

def insert_subcategory_record(cat_id, name):
    # Connect to the database

    # Check if subcategory name already exists for the specified category
    cursor.execute('SELECT COUNT(*) FROM subcategory WHERE cat_id = %s AND name = %s', (cat_id, name))
    subcategory_exists = cursor.fetchone()[0] > 0

    # Validate subcategory data
    if subcategory_exists:
        raise ValueError('Subcategory name already exists in this category')

    # Insert new subcategory record into database
    cursor.execute('INSERT INTO subcategory (cat_id, name) VALUES (%s, %s)', (cat_id, name))
    conn.commit()

    # Close the database connection

def insert_course_record(subcat_id, price, description, content, ratings, number_of_lessons, teacher_id):
    # Connect to the database

    # Validate course data
    if price < 0:
        raise ValueError('Course price cannot be negative')
    if ratings < 0 or ratings > 5:
        raise ValueError('Course ratings must be between 0 and 5')
    if number_of_lessons < 1:
        raise ValueError('Course must have at least one lesson')

    # Insert new course record into database
    cursor.execute('INSERT INTO course (subcat_id, price, description, content, ratings, number_of_lessons, teacher_id) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                   (subcat_id, price, description, content, ratings, number_of_lessons, teacher_id))
    conn.commit()

    # Close the database connection

def get_course_by_id(course_id):
    # Connect to the database

    cursor.execute('SELECT * FROM course WHERE cid = %s', (course_id,))
    course = cursor.fetchone()

    return course

def is_valid_course_id(course_id):
    # Connect to the database

    # Check if course ID exists in the database
    cursor.execute('SELECT COUNT(*) FROM course WHERE cid = %s', (course_id,))
    course_exists = cursor.fetchone()[0] > 0

    # Close the database connection

    return course_exists

def is_student_enrolled(student_id, course_id):
    # Connect to the database

    # Check if student is enrolled in the course
    cursor.execute('SELECT COUNT(*) FROM enrollment WHERE student_id = %s AND course_id = %s', (student_id, course_id))
    enrolled = cursor.fetchone()[0] > 0


    return enrolled

def enroll_student_in_course(student_id, course_id):
    # Connect to the database

    # Insert a new enrollment record
    cursor.execute('INSERT INTO enrollment (student_id, course_id, date_of_enrollment) VALUES (%s, %s, CURRENT_DATE)', (student_id, course_id))
    conn.commit()

    # Close the database connection

def is_in_wishlist(student_id, course_id):
    # Connect to the database

    # Check if item exists in wishlist
    cursor.execute('SELECT COUNT(*) FROM wishlist WHERE sid = %s AND cid = %s', (student_id, course_id))
    in_wishlist = cursor.fetchone()[0] > 0

    # Close the database connection

    return in_wishlist

def remove_from_wishlist_item(student_id, course_id):
    # Connect to the database

    # Remove item from wishlist
    cursor.execute('DELETE FROM wishlist WHERE sid = %s AND cid = %s', (student_id, course_id))

    # Close the database connection

def is_in_cart(student_id, course_id):
    # Connect to the database



    # Check if item exists in cart
    cursor.execute('SELECT COUNT(*) FROM cart WHERE sid = %s AND cid = %s', (student_id, course_id))
    in_cart = cursor.fetchone()[0] > 0

    # Close the database connection


    return in_cart

def add_to_cart_item(student_id, course_id):
    # Connect to the database


    # Add item to cart
    cursor.execute('INSERT INTO cart (sid, cid) VALUES (%s, %s)', (student_id, course_id))


    # Close the database connection



@app.route('/user/login', methods=['POST'])
def login_student():
    login_data = request.get_json()
    email = login_data['email']
    password = login_data['password']
    role = login_data['role']
    user_info = validate_login(email, password,role)

    if user_info:
        return jsonify({'message': 'Login successful', 'user': user_info})
    else:
        return jsonify({'error': 'Invalid login credentials'})

@app.route('/categories', methods=['GET'])
def get_all_categories():
    # Fetch all categories from the database
    categories = get_categories()

    return jsonify({'categories': categories})

@app.route('/categories/<category_id>/subcategories', methods=['GET'])
def get_subcategories_by_category(category_id):
    subcategories = get_subcategories_by_category_id(category_id)

    return jsonify({'subcategories': subcategories})

@app.route('/category', methods=['POST'])
def insert_category():
    category_data = request.get_json()
    name = category_data['name']
    description = category_data['description']

    # Validate category data and insert into database
    insert_category_record(name, description)

    return jsonify({'message': 'Category inserted successfully'})

@app.route('/subcategory', methods=['POST'])
def insert_subcategory():
    subcategory_data = request.get_json()
    print('sub',subcategory_data)
    cat_id = subcategory_data['cat_id']
    name = subcategory_data['name']

    # Validate subcategory data and insert into database
    insert_subcategory_record(cat_id, name)

    return jsonify({'message': 'Subcategory inserted successfully'})


@app.route('/course', methods=['POST'])
def insert_course():
    course_data = request.get_json()
    subcat_id = course_data['subcat_id']
    price = course_data['price']
    description = course_data['description']
    content = course_data['content']
    ratings = course_data['ratings']
    number_of_lessons = course_data['number_of_lessons']
    teacher_id = course_data['teacher_id']

    # Validate course data and insert into database
    insert_course_record(subcat_id, price, description, content, ratings, number_of_lessons, teacher_id)

    return jsonify({'message': 'Course inserted successfully'})

@app.route('/courses/<course_id>', methods=['GET'])
def get_course(course_id):
    course = get_course_by_id(course_id)

    if course is None:
        return jsonify({'message': 'Course not found'})

    # Convert course record to dictionary
    course_obj = {
            'cid': course[0],
            'subcat_id': course[1],
            'price': course[2],
            'description': course[3],
            'content': course[4],
            'ratings': course[5],
            'number_of_lessons': course[6],
            'student_id': course[7]
    }

    return jsonify(course_obj)

@app.route('/courses', methods=['GET'])
def get_all_courses():
    # Connect to the database

    # Retrieve all course records from database
    cursor.execute('SELECT * FROM course')
    courses = cursor.fetchall()

    # Close the database connection

    # Convert course records to dictionaries
    course_list = []
    for course in courses:
        course_obj = {
            'cid': course[0],
            'subcat_id': course[1],
            'price': course[2],
            'description': course[3],
            'content': course[4],
            'ratings': course[5],
            'number_of_lessons': course[6],
            'student_id': course[7]
        }
        course_list.append(course_obj)

    return jsonify({'courses': course_list})

@app.route('/enrollment', methods=['POST'])

def enroll_student():
    enrollment_data = request.get_json()
    student_id = enrollment_data['student_id']
    course_id = enrollment_data['course_id']

    # Validate enrollment data
    if not is_valid_course_id(course_id):
        return jsonify({'message': 'Invalid course ID'})

    # Check if student is already enrolled in the course
    if is_student_enrolled(student_id, course_id):
        return jsonify({'message': 'Student is already enrolled in this course'})

    # Enroll student in the course
    enroll_student_in_course(student_id, course_id)

    return jsonify({'message': 'Successfully enrolled in the course'})


@app.route('/wishlist/<student_id>', methods=['GET'])
def get_wishlist(student_id):
    # Connect to the database

    # Retrieve wishlist items for the specified student
    cursor.execute('SELECT * FROM wishlist WHERE sid = %s', (student_id,))
    wishlist_items = cursor.fetchall()

    # Convert wishlist records to dictionaries
    wishlist_list = []
    for wishlist_item in wishlist_items:
        wishlist_obj = {
            'sid': wishlist_item['sid'],
            'cid': wishlist_item['cid']
        }
        wishlist_list.append(wishlist_obj)

    # Close the database connection

    return jsonify({'wishlist': wishlist_list})

@app.route('/wishlist', methods=['POST'])
def add_to_wishlist():
    wishlist_data = request.get_json()
    student_id = wishlist_data['student_id']
    course_id = wishlist_data['course_id']

    # Check if course ID exists
    if not is_valid_course_id(course_id):
        return jsonify({'message': 'Invalid course ID'})

    # Check if item is already in wishlist
    if is_in_wishlist(student_id, course_id):
        return jsonify({'message': 'Item is already in wishlist'})

    # Add item to wishlist
    cursor.execute('INSERT INTO cart (sid, cid) VALUES (%s, %s)', (student_id, course_id))


    return jsonify({'message': 'Item added to wishlist'})


@app.route('/wishlist/<student_id>/<course_id>', methods=['DELETE'])
def remove_from_wishlist(student_id, course_id):
    # Check if course ID exists
    if not is_valid_course_id(course_id):
        return jsonify({'message': 'Invalid course ID'})

    # Check if item is in wishlist
    if not is_in_wishlist(student_id, course_id):
        return jsonify({'message': 'Item is not in wishlist'})

    # Remove item from wishlist
    remove_from_wishlist_item(student_id, course_id)

    return jsonify({'message': 'Item removed from wishlist'})



@app.route('/cart/<student_id>', methods=['GET'])
def get_cart(student_id):
    # Connect to the database

    # Retrieve cart items for the specified student
    cursor.execute('SELECT * FROM cart WHERE sid = %s', (student_id,))
    cart_items = cursor.fetchall()

    # Convert cart records to dictionaries
    cart_list = []
    for cart_item in cart_items:
        cart_obj = {
            'sid': cart_item['sid'],
            'cid': cart_item['cid']
        }
        cart_list.append(cart_obj)

    # Close the database connection

    return jsonify({'cart': cart_list})

@app.route('/cart', methods=['POST'])
def add_to_cart():
    cart_data = request.get_json()
    student_id = current_user.id
    course_id = cart_data['course_id']

    # Check if course ID exists
    if not is_valid_course_id(course_id):
        return jsonify({'message': 'Invalid course ID'})

    # Check if item is already in cart
    if is_in_cart(student_id, course_id):
        return jsonify({'message': 'Item is already in cart'})

    # Add item to cart
    add_to_cart_item(student_id, course_id)

    return jsonify({'message': 'Item added to cart'})

@app.route('/past_enrollments/<student_id>', methods=['GET'])
def get_past_enrollments(student_id):
    # Connect to the database

    # Retrieve past enrollments for the specified student
    cursor.execute('SELECT * FROM past_enrollments WHERE sid = %s AND validity < CURRENT_DATE', (student_id,))
    past_enrollments = cursor.fetchall()

    # Convert past enrollment records to dictionaries
    past_enrollment_list = []
    for past_enrollment in past_enrollments:
        past_enrollment_obj = {
            'sid': past_enrollment['sid'],
            'cid': past_enrollment['cid'],
            'date_of_enrollment': past_enrollment['date_of_enrollment'],
            'validity': past_enrollment['validity']
        }
        past_enrollment_list.append(past_enrollment_obj)

    return jsonify({'past_enrollments': past_enrollment_list})


@app.route("/chat")
def chat():
    return render_template("chat.html")


users = {}
receiver_global = ""


@socketio.on("connect")
def handle_connect():
    print("Client connected!")


@socketio.on("user_join")
def handle_user_join(username):
    print(f"User {username} joined!")
    users[username] = request.sid

    cursor.execute('SELECT distinct receiver FROM chat WHERE sender = %s', username)
    person_list = cursor.fetchall()

    print("Here is the list of person that you chatted before")
    print(person_list)

    global receiver_global
    receiver = input("Enter a person to start chatting: ")
    receiver_global = receiver

    cursor.execute('SELECT * FROM student WHERE email = %s', username)
    result = cursor.fetchone()
    if result:
        student_id = result[0]
    else:
        cursor.execute('SELECT * FROM teacher WHERE email = %s', username)
        teacher_id = cursor.fetchone()[0]

    cursor.execute('SELECT * FROM teacher WHERE email = %s', receiver_global)
    result = cursor.fetchone()
    if result:
        teacher_id = result[0]
    else:
        cursor.execute('SELECT * FROM student WHERE email = %s', receiver_global)
        student_id = cursor.fetchone()[0]

    query = "SELECT * FROM chat WHERE student_id = %s AND teacher_id = %s"
    cursor.execute(query, (student_id, teacher_id))
    user_chatted_before = cursor.fetchall()

    if user_chatted_before:
        chat_history = get_chat_history(student_id, teacher_id)
        for message in chat_history:
            emit("chat", {"message": message['content'], "username": message['sender']}, room=request.sid)


def get_chat_history(student_id, teacher_id):
    # Retrieve chat history for the connected user from the database
    query = "SELECT * FROM chat WHERE student_id = %s AND teacher_id = %s"
    cursor.execute(query, (student_id, teacher_id))
    chat_history = cursor.fetchall()

    # Convert chat history to a list of dictionaries
    history_list = []
    for entry in chat_history:
        history_list.append({
            'sender': entry[5],
            'content': entry[4]
        })

    return history_list


@socketio.on("new_message")
def handle_new_message(message):
    global receiver_global
    print(f"New message: {message}")
    username = None
    for user in users:
        if users[user] == request.sid:
            username = user

    cursor.execute('SELECT * FROM student WHERE email = %s', username)
    result = cursor.fetchone()
    if result:
        student_id = result[0]
    else:
        cursor.execute('SELECT * FROM teacher WHERE email = %s', username)
        teacher_id = cursor.fetchone()[0]

    cursor.execute('SELECT * FROM teacher WHERE email = %s', receiver_global)
    result = cursor.fetchone()
    if result:
        teacher_id = result[0]
    else:
        cursor.execute('SELECT * FROM student WHERE email = %s', receiver_global)
        student_id = cursor.fetchone()[0]

    insert_query = "INSERT INTO chat (student_id, teacher_id, time_stamp, content, sender, receiver) VALUES (%s, %s, %s, %s, %s, %s)"
    values = (student_id, teacher_id, datetime.now().time(), message, username, receiver_global)
    cursor.execute(insert_query, values)
    conn.commit()

    emit("chat", {"message": message, "username": username}, room=request.sid)
    emit("chat", {"message": message, "username": username}, room=users[receiver_global])


if __name__ == '__main__':
    socketio.init_app(app)
    socketio.run(app)
