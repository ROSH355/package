from datetime import datetime
from flask import Flask, jsonify, render_template, request, redirect,flash, send_from_directory,url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import bcrypt
import pymysql
import os
from reportlab.pdfgen import canvas
from sqlalchemy import text
import pytz

india = pytz.timezone('Asia/Kolkata')
pymysql.install_as_MySQLdb()


app = Flask(__name__)
app.secret_key = 'supersecretkey123'
# Configure MySQL database (adjust according to your setup)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Jo36%40220705@localhost/e_learning'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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
    quizzes = db.relationship('Quiz', backref='course', lazy=True)
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

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    quiz_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    questions = db.relationship('QuizQuestion', backref='quizzes', lazy=True)

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    question_id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.quiz_id'), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)

class QuizResponse(db.Model):
    __tablename__ = 'quiz_responses'
    response_id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.quiz_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    score = db.Column(db.Integer)
    submitted_at = db.Column(db.DateTime, default=lambda: datetime.now(india))
    quiz = db.relationship('Quiz', backref=db.backref('responses', lazy=True))
    user = db.relationship('User', backref=db.backref('quiz_responses', lazy=True))

class Certificate(db.Model):
    __tablename__ = 'certificates'
    certificate_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    issued_at = db.Column(db.TIMESTAMP, server_default=func.now())
    certificate_url = db.Column(db.String(255), nullable=False)

    user = db.relationship('User', backref='certificates')
    course = db.relationship('Course', backref='certificates')


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
        instructor_email = request.form['email']  
        
        instructor = User.query.filter_by(email=instructor_email, role='Instructor').first()
        
        if instructor:
            existing_course = Course.query.filter_by(title=title, instructor_id=instructor.user_id).first()
            if existing_course:
                return "This course already exists for this instructor.", 400
            
            new_course = Course(title=title, description=description, instructor_id=instructor.user_id)
            db.session.add(new_course)
            db.session.commit()
            
            return redirect(url_for('addlessons', course_id=new_course.course_id))
        else:
            return "Instructor not found", 404
    
    return render_template('create_course.html')

# 
@app.route('/courses')
def show_courses():
    courses = Course.query.all()
    enrolled_course_ids = []

    if 'user_id' in session and session.get('role') == 'student':
        user_id = session['user_id']
        enrolled_course_ids = [e.course_id for e in Enrollment.query.filter_by(user_id=user_id).all()]

    return render_template('courses.html', courses=courses, enrolled_course_ids=enrolled_course_ids)


from flask import session

@app.route('/enroll/<int:course_id>')
def enroll(course_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    
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
        return redirect(url_for('login')) 

    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        flash("User not found.", "error")
        return redirect(url_for('login'))

    if user.role == 'student':
        enrollments = Enrollment.query.filter_by(user_id=user_id).all()
        courses = [Course.query.get(enrollment.course_id) for enrollment in enrollments]

        for course in courses:
            course.lessons = Lesson.query.filter_by(course_id=course.course_id).all()
            course.quizzes = Quiz.query.filter_by(course_id=course.course_id).all()

        return render_template('my_courses.html', courses=courses)
    else:
        flash("You are not authorized to view this page.", "error")
        return redirect(url_for('courses'))


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
        return redirect(url_for('show_courses')) 

    return render_template('addlessons.html', course=course)

@app.route('/course/<int:course_id>')
def course_page(course_id):
    course = Course.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(course_id=course_id).all()
    quizzes = Quiz.query.filter_by(course_id=course_id).all()
    return render_template('course_lessons.html', course=course, lessons=lessons, quizzes=quizzes)

@app.route('/lesson/<int:lesson_id>')
def lesson_page(lesson_id):
    lesson = Lesson.query.get(lesson_id) 
    if not lesson:
        return "Lesson not found", 404
    
    return render_template('lesson_page.html', lesson=lesson)

@app.route('/create_quiz/<int:course_id>', methods=['GET', 'POST'])
def create_quiz(course_id):
    if request.method == 'POST':
        title = request.form['title']
        total_marks = request.form['total_marks']

        new_quiz = Quiz(course_id=course_id, title=title, total_marks=total_marks)
        db.session.add(new_quiz)
        db.session.commit()

        return redirect(url_for('add_quiz_questions', quiz_id=new_quiz.quiz_id))

    return render_template('create_quiz.html', course_id=course_id)

@app.route('/add_quiz_questions/<int:quiz_id>', methods=['GET', 'POST'])
def add_quiz_questions(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)

    if request.method == 'POST':
        action = request.form.get('action')
        question_text = request.form['question_text']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_option = request.form['correct_option']

        question = QuizQuestion(
            quiz_id=quiz_id,
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_option=correct_option.upper()
        )
        db.session.add(question)
        db.session.commit()

        if action == 'add':
            return redirect(url_for('add_quiz_questions', quiz_id=quiz_id))
        elif action == 'finish':
            # Redirect back to create_quiz.html for the same course
            quiz = Quiz.query.get(quiz_id)
            return redirect(url_for('create_quiz', course_id=quiz.course_id))

    return render_template('add_quiz_questions.html', quiz_id=quiz_id)


@app.route('/attend_quiz/<int:quiz_id>', methods=['GET', 'POST'])
def attend_quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = QuizQuestion.query.filter_by(quiz_id=quiz_id).all()

    if request.method == 'POST':
        score = 0
        for question in questions:
            selected = request.form.get(f'question_{question.question_id}')
            if selected and selected.upper() == question.correct_option.upper():
                score += 1
        
        response = QuizResponse(
            quiz_id=quiz_id,
            user_id=session['user_id'],
            score=score
        )
        db.session.add(response)
        db.session.commit()

        return render_template('quiz_result.html', score=score, total=len(questions))

    return render_template('attend_quiz.html', quiz=quiz, questions=questions)

@app.route('/view_quiz_results/<int:quiz_id>')
def view_quiz_results(quiz_id):
    if 'role' not in session or session['role'] != 'instructor':
        flash("Access denied.")
        return redirect(url_for('login'))

    quiz = Quiz.query.get_or_404(quiz_id)
    results = QuizResponse.query.filter_by(quiz_id=quiz_id).all()

    return render_template('quiz_results_instructor.html', quiz=quiz, results=results)

def get_student_by_id(student_id):
    return User.query.get(student_id)

from sqlalchemy import text

def get_certificate_for_student(student_id, course_id):
    result = db.session.execute(
        text("CALL get_certificate_for_student(:student_id, :course_id)"),
        {"student_id": student_id, "course_id": course_id}
    ).fetchone()

    return result

def ensure_certificate_pdf(student_id, course_id):
    filename = f"{student_id}_{course_id}.pdf"
    cert_dir = os.path.join(app.root_path, 'static', 'certificates')
    os.makedirs(cert_dir, exist_ok=True)
    path = os.path.join(cert_dir, filename)

    if not os.path.exists(path):
        # Generate a simple PDF
        c = canvas.Canvas(path)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, 750, "Certificate of Completion")
        c.setFont("Helvetica", 14)
        c.drawString(100, 700, f"Congratulations, Student {student_id}!")
        c.drawString(100, 675, f"You've completed Course {course_id}.")
        c.save()

@app.route('/course_completion/<student_id>/<course_id>')
def course_completion(student_id, course_id):
    student = get_student_by_id(student_id)
    certificate = get_certificate_for_student(student_id, course_id)

    if certificate:
        ensure_certificate_pdf(student_id, course_id)

    return render_template('course_completion.html', student=student, certificate=certificate)

@app.route('/download_certificate/<certificate_url>')
def download_certificate(certificate_url):
    certificate_directory = os.path.join(app.root_path, 'static', 'certificates')
    return send_from_directory(certificate_directory, certificate_url, as_attachment=True)

def get_user_progress(user_id, course_id):
    result = db.session.execute(
        text("CALL get_user_progress(:user_id, :course_id)"),
        {"user_id": user_id, "course_id": course_id}
    ).fetchone()
    
    print(f"Stored Procedure result: {result}") 
    return result[0] if result else None

@app.route('/progress/<int:course_id>')
def show_progress(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))  
    user_id = session['user_id']

    progress_percent = get_user_progress(user_id, course_id)
    
    if progress_percent is None:
        flash('Unable to fetch progress. Please try again later.', 'error')
        return redirect(url_for('my_courses'))

    return render_template('show_progress.html', progress=progress_percent, course_id=course_id)

def get_course_completion_status(user_id, course_id):
    result = db.session.execute(
        text("CALL get_course_completion_status(:user_id, :course_id)"),
        {"user_id": user_id, "course_id": course_id}
    ).fetchone()

    if result:
        try:
            return result[0] or result['progress_percent']
        except (IndexError, KeyError):
            return None
    return None

@app.route('/course_completion/<int:course_id>')
def show_course_completion(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    progress = get_course_completion_status(user_id, course_id)

    if progress is None:
        flash('Unable to fetch course completion status. Please try again later.', 'error')
        return redirect(url_for('my_courses'))

    return render_template('show_course_completion.html', progress=progress, course_id=course_id)

from datetime import datetime, timedelta
from sqlalchemy import text
india = pytz.timezone('Asia/Kolkata')

@app.route('/cleanup_old_responses')
def cleanup_old_responses():
    if 'role' not in session or session['role'] != 'instructor':
        flash("Only instructors can perform cleanup.", "error")
        return redirect(url_for('login'))

    cutoff = datetime.now(india) - timedelta(days=1)
    try:
        db.session.execute(text("CALL DeleteOldResponses(:cutoff)"), {"cutoff": cutoff})
        db.session.commit()
        flash("Old quiz responses cleaned up successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to clean old responses: {str(e)}", "error")

    return redirect(url_for('show_courses')) 

if __name__ == '__main__':
    app.run(debug=True)