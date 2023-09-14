from flask import Flask,render_template, request, jsonify
from flask_mysqldb import MySQL
 
app = Flask(__name__)
 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Bhavana@123'
app.config['MYSQL_DB'] = 'mysql'
 
mysql = MySQL(app)

@app.route('/api/signup', methods=['POST'])
def register_user():
    try:
        username = request.json['username']
        password = request.json['password']

        # Check if the user already exists in the database
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            cursor.close()
            return jsonify({'status': 'User already exists', 'status_code': 400}), 400

        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        mysql.connection.commit()
        cursor.close()

        new_cursor = mysql.connection.cursor()
        new_cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user_id = new_cursor.fetchone()[0]
        new_cursor.close()

        response_data = {
            'status': 'Account successfully created',
            'status_code': 200,
            'user_id': user_id
        }

        return jsonify(response_data), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


import uuid  # for generating API keys
admin_api_key = str(uuid.uuid4())

api_keys = {'admin': admin_api_key}

@app.route('/admin/api-key', methods=['GET'])
def get_admin_api_key():
    return jsonify({'api_key': admin_api_key})
@app.route('/api/login', methods=['POST'])
def login_user():
    try:
        username = request.json['username']
        password = request.json['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            return jsonify({'status': 'Incorrect username/password provided. Please retry'}), 401

        token = str(uuid.uuid4())
        user_id = user[0]

        response_data = {
            'status': 'Login successful',
            'status_code': 200,
            'user_id': user_id,
            'access_token': token
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def require_admin_api_key(func):
    def wrapper(*args, **kwargs):
        api_key = request.headers.get('Authorization')

        if api_key == admin_api_key:
            return func(*args, **kwargs)
        else:
            return jsonify({'message': 'Unauthorized'}), 401

    return wrapper

@app.route('/api/books/create', methods=['POST'])
@require_admin_api_key
def add_book():
    try:

        return jsonify({'message': 'Book added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/books/create', methods=['POST'])
@require_admin_api_key
def add_book():
    try:
        title = request.json['title']
        author = request.json['author']

        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO books (title, author) VALUES (%s, %s)", (title, author))
        mysql.connection.commit()

        cursor.execute("SELECT LAST_INSERT_ID()")
        book_id = cursor.fetchone()[0]

        cursor.close()

        response_data = {
            'message': 'Book added successfully',
            'book_id': book_id
        }

        return jsonify(response_data), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/books?title={search_query}', methods=['GET'])
def search_books():
    try:
        query = request.args.get('query')

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM books WHERE title LIKE %s", (f"%{query}%",))
        books = cursor.fetchall()
        cursor.close()

        if not books:
            return jsonify({'message': 'No books found'}), 404

        book_list = [{'id': book[0], 'title': book[1], 'author': book[2]} for book in books]

        return jsonify({'books': book_list}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/books/{book_id}/availability', methods=['GET'])
def get_book_availability(book_id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM bookings WHERE book_id = %s ORDER BY return_time DESC LIMIT 1", (book_id,))
        booking = cursor.fetchone()
        cursor.close()

        if not booking:
            return jsonify({'message': 'Book is available'}), 200
        next_available_time = booking[3]  

        return jsonify({'message': 'Book is not available', 'next_available_time': next_available_time}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/books/borrow', methods=['POST'])
def borrow_book(book_id):
    try:
        # Get the user's authorization token from the request headers
        authorization_token = request.headers.get('Authorization')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM bookings WHERE book_id = %s AND return_time > NOW()", (book_id,))
        booking = cursor.fetchone()

        if booking:
            next_available_time = booking[3] 
            cursor.close()
            return jsonify({'message': 'Book is not available', 'next_available_time': next_available_time}), 400

        # Book the book for the user
        cursor.execute("INSERT INTO bookings (book_id, user_token, issue_time, return_time) VALUES (%s, %s, NOW(), DATE_ADD(NOW(), INTERVAL 7 DAY))", (book_id, authorization_token))
        mysql.connection.commit()
        cursor.close()

        return jsonify({'message': 'Book successfully booked', 'return_time': '7 days from now'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

