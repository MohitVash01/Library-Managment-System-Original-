from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'
Bootstrap(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Use SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Define the Book model
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    number_units = db.Column(db.Integer, nullable=False)  # Added field for number of units
    available = db.Column(db.Boolean, default=True)

# Hardcoded admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    if role == 'admin' and username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return redirect(url_for('dashboard_admin', name=username))

    if role == 'user':
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            return redirect(url_for('dashboard_user', role='User'))

    flash('Invalid username or password!')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if the username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect('/register')
        else:
            # Add the new user to the database
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()

            flash('User registered successfully!')
            return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/dashboard_admin')
def dashboard_admin():
    name = request.args.get('name')  # Assuming name is passed in the request arguments
    return render_template('dashboard_admin.html', name=name)

@app.route('/dashboard_user')
def dashboard_user():
    role = request.args.get('role')
    return render_template('dashboard_user.html', role=role)

# New route for searching books
@app.route('/search_books', methods=['GET', 'POST'])
def search_books():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        # Search for books by title or author
        books = Book.query.filter((Book.title.ilike(f'%{search_query}%')) | (Book.author.ilike(f'%{search_query}%'))).all()

        if books:
            return render_template('search_books.html', books=books, query=search_query)
        else:
            flash('No books found!')
            return render_template('search_books.html', books=[], query=search_query)

    return render_template('search_books.html', books=None)

# Route for admin to manage books (add, delete)
@app.route('/maintenance', methods=['GET', 'POST'])
def maintenance():
    if request.method == 'POST':
        if 'add_book' in request.form:
            title = request.form.get('title')
            author = request.form.get('author')
            number_units = request.form.get('number_units')  # Retrieve the number of units

            # Validate that number_units is not None or empty
            if not number_units:
                flash('Please provide the number of units.')
                return redirect(url_for('maintenance'))

            try:
                number_units = int(number_units)  # Ensure it's converted to an integer
            except ValueError:
                flash('Number of units must be a valid number.')
                return redirect(url_for('maintenance'))

            new_book = Book(title=title, author=author, number_units=number_units)  # Save number_units to the Book
            db.session.add(new_book)
            db.session.commit()
            flash('Book added successfully!')

        elif 'delete_book' in request.form:
            book_id = request.form.get('book_id')
            book = Book.query.get(book_id)
            if book:
                db.session.delete(book)
                db.session.commit()
                flash('Book deleted successfully!')
            else:
                flash('Book not found!')

    books = Book.query.all()
    return render_template('maintenance.html', books=books)

# Route for Book Issue Page
@app.route('/book_issue', methods=['GET', 'POST'])
def book_issue():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        # Search for books by title or author
        books = Book.query.filter((Book.title.ilike(f'%{search_query}%')) | (Book.author.ilike(f'%{search_query}%'))).all()
        
        return render_template('book_issue.html', books=books, query=search_query)
    return render_template('book_issue.html', books=None)

# Route to handle actual book issue process
@app.route('/issue/<int:book_id>', methods=['POST'])
def issue(book_id):
    book = Book.query.get(book_id)
    
    if book and book.available and book.number_units > 0:
        book.number_units -= 1  # Decrease number of available units
        if book.number_units == 0:
            book.available = False  # Mark as unavailable if no units left
        db.session.commit()
        flash('Book issued successfully!')
    else:
        flash('Book is not available or out of stock.')

    return redirect(url_for('book_issue'))

# Route for Book Return Page
@app.route('/book_return', methods=['GET', 'POST'])
def book_return():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        # Search for books by title or author
        books = Book.query.filter((Book.title.ilike(f'%{search_query}%')) | (Book.author.ilike(f'%{search_query}%'))).all()
        
        return render_template('book_return.html', books=books, query=search_query)
    return render_template('book_return.html', books=None)

# Route to handle actual book return process
@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    book = Book.query.get(book_id)
    
    if book:
        book.number_units += 1  # Increase the number of available units
        book.available = True  # Mark as available again
        db.session.commit()
        flash('Book returned successfully!')
    else:
        flash('Book not found.')

    return redirect(url_for('book_return'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database and tables if they don't exist
    app.run(debug=True)
