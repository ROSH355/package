from flask import Flask, render_template, request, redirect,flash,url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import bcrypt
import pymysql

pymysql.install_as_MySQLdb()


app = Flask(__name__)
app.secret_key = 'supersecretkey123'
# Configure MySQL database (adjust according to your setup)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Radharam12345@localhost/e_learning'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    __tablename__='users'
    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    date_joined=db.Column(db.TIMESTAMP,server_default=func.now())

class Course(db.Model):
    __tablename__ = 'courses'
    course_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=func.now())
    instructor = db.relationship('User', backref='courses')

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    enrollment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    enrolled_at = db.Column(db.TIMESTAMP, server_default=func.now())
    user = db.relationship('User', backref='enrollments')
    course = db.relationship('Course', backref='enrollments')

class Lesson(db.Model):
    __tablename__ = 'lessons'
    lesson_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    video_url = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in minutes
    order_number = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    course = db.relationship('Course', backref='lessons', lazy=True)

'''class Lesson(db.Model):
    __tablename__ = 'lessons'
    lesson_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    video_url = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    order_number = db.Column(db.Integer, nullable=False)
'''
from flask import session

@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "User already exists. Please log in.", 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(full_name=full_name, email=email, password_hash=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.user_id
        # in both register() and login()
        session['role'] = new_user.role.lower()


        return redirect('/courses')

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            session['user_id'] = user.user_id
            # in both register() and login()
            session['role'] = user.role.lower()
            print("Session role after login:", session['role'])

            return redirect('/courses')
        else:
            return "Invalid credentials", 401

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/create_course', methods=['GET', 'POST'])
def create_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        instructor_email = request.form['email']  # or get from session
        
        instructor = User.query.filter_by(email=instructor_email, role='Instructor').first()
        
        if instructor:
            # Prevent creating the same course with the same title by the same instructor
            existing_course = Course.query.filter_by(title=title, instructor_id=instructor.user_id).first()
            if existing_course:
                return "This course already exists for this instructor.", 400
            
            new_course = Course(title=title, description=description, instructor_id=instructor.user_id)
            db.session.add(new_course)
            db.session.commit()
            
            # Redirect to the add lessons page for the newly created course
            return redirect(url_for('addlessons', course_id=new_course.course_id))
        else:
            return "Instructor not found", 404
    
    return render_template('create_course.html')


'''@app.route('/create_course', methods=['GET', 'POST'])
def create_course():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        instructor_email = request.form['email']  # or get from session
        
        instructor = User.query.filter_by(email=instructor_email, role='Instructor').first()
        
        if instructor:
            # Prevent creating the same course with the same title by the same instructor
            existing_course = Course.query.filter_by(title=title, instructor_id=instructor.user_id).first()
            if existing_course:
                return "This course already exists for this instructor.", 400
            
            new_course = Course(title=title, description=description, instructor_id=instructor.user_id)
            db.session.add(new_course)
            db.session.commit()
            return redirect('/success')
        else:
            return "Instructor not found", 404
    
    return render_template('create_course.html')

'''
@app.route('/courses')
def show_courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

from flask import session

@app.route('/enroll/<int:course_id>')
def enroll(course_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    
    # Avoid duplicate enrollments
    already_enrolled = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    if already_enrolled:
        return "You are already enrolled in this course."

    enrollment = Enrollment(user_id=user_id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    return redirect('/my_courses')


@app.route('/my_courses')
def my_courses():
    if 'user_id' not in session:
        return redirect('/login')
        
    user = User.query.get(session['user_id'])
    enrolled_courses = [en.course for en in user.enrollments]
    return render_template('my_courses.html', courses=enrolled_courses)

'''@app.route('/addlesson', methods=['GET', 'POST'])
def add_lesson():
    if 'user_id' not in session or session.get('role') != 'instructor':
        flash("Access denied. Only instructors can add lessons.")
        return redirect('/login')

    instructor_id = session['user_id']
    instructor_courses = Course.query.filter_by(instructor_id=instructor_id).all()

    if not instructor_courses:
        flash("You must create a course before adding lessons.")
        return redirect('/create_course')

    selected_course_id = request.args.get('course_id', '')

    if request.method == 'POST':
        title = request.form.get('title')
        video_url = request.form.get('video_url')
        duration = request.form.get('duration')
        order_number = request.form.get('order_number')
        course_id = request.form.get('course_id')

        if not all([title, video_url, duration, order_number, course_id]):
            flash("Please fill in all fields.")
            return render_template('addlessons.html', courses=instructor_courses, selected_course_id=selected_course_id)

        new_lesson = Lesson(
            title=title,
            video_url=video_url,
            duration=int(duration),
            order_number=int(order_number),
            course_id=int(course_id)
        )

        try:
            db.session.add(new_lesson)
            db.session.commit()
            flash("Lesson added successfully!")
            return redirect('/addlesson')
        except Exception as e:
            db.session.rollback()
            flash("Error adding lesson: " + str(e))
            return render_template('addlessons.html', courses=instructor_courses, selected_course_id=selected_course_id)

    return render_template('addlessons.html', courses=instructor_courses, selected_course_id=selected_course_id)
'''
@app.route('/addlessons/<int:course_id>', methods=['GET', 'POST'])
def addlessons(course_id):
    if 'role' not in session or session['role'] != 'instructor':
        flash('You need to be an instructor to add lessons.')
        return redirect(url_for('login'))

    course = Course.query.get(course_id)

    if course is None or course.instructor_id != session['user_id']:
        flash('You are not authorized to add lessons to this course.')
        return redirect(url_for('courses'))

    if request.method == 'POST':
        title = request.form['title']
        video_url = request.form['video_url']
        duration = request.form['duration']
        order_number = request.form['order_number']

        new_lesson = Lesson(
            title=title,
            video_url=video_url,
            duration=duration,
            order_number=order_number,
            course_id=course_id
        )
        db.session.add(new_lesson)
        db.session.commit()

        flash('Lesson added successfully!')
        return redirect(url_for('show_courses'))  # Redirect to courses page after adding lesson

    return render_template('addlessons.html', course=course)

@app.route('/course_lessons/<int:course_id>')
def course_lessons(course_id):
    course = Course.query.get(course_id)
    if course is None:
        return "Course not found", 404

    # Get the lessons associated with this course
    lessons = Lesson.query.filter_by(course_id=course_id).all()

    return render_template('course_lessons.html', course=course, lessons=lessons)
@app.route('/lesson/<int:lesson_id>')
def lesson_page(lesson_id):
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return "Lesson not found", 404
    
    return render_template('lesson_page.html', lesson=lesson)

if __name__ == '__main__':
    app.run(debug=True)