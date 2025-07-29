from flask import Flask, request, jsonify, session
import pandas as pd
from models import db, Students, Schedules, Periods, ValidationResults, StudentSchedules, UnassignedCourses
from data_validation.schedule_data_validator import ScheduleDataValidator
from optimization.schedule_optimizer import ScheduleOptimizer
from utils import normalize_dataframe
from functools import wraps
import json


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/ScheduleBackEnd'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"status": "Error", "message": "Not authenticated"}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_user_uploaded_data(user_id):
    students = pd.read_sql(Students.query.filter_by(user_id=user_id).statement, db.engine)
    schedules = pd.read_sql(Schedules.query.filter_by(user_id=user_id).statement, db.engine)
    periods = pd.read_sql(Periods.query.filter_by(user_id=user_id).statement, db.engine)
    if students.empty or schedules.empty or periods.empty:
        return None, None, None
    return students, schedules, periods

def is_data_optimized(user_id):
    assigned_exists = db.session.query(StudentSchedules.query.filter_by(user_id=user_id).exists()).scalar()
    unassigned_exists = db.session.query(UnassignedCourses.query.filter_by(user_id=user_id).exists()).scalar()
    return assigned_exists or unassigned_exists

@app.route('/mock_login')
def mock_login():
    session['user_id'] = 'test-user-123'  # Use the ID from your test user
    return jsonify({"status": "Success", "message": "Mock user logged in", "user_id": session['user_id']})

@app.route('/upload', methods=['POST'])
@require_login
def upload_data():
    user_id = session.get('user_id')
    
    required_files = {'students', 'schedules', 'periods'}
    uploaded_files = set(request.files.keys())

    missing_files = required_files - uploaded_files

    if missing_files:
        return jsonify({
            "status": "Error",
            "message": f"Missing required CSV file(s): {', '.join(sorted(missing_files))}"
        }), 400

    try:
        empty_csvs = []
        def read_csv_file(file_key):
            try:
                return pd.read_csv(request.files[file_key])
            except pd.errors.EmptyDataError:
                empty_csvs.append(file_key)
                return None

        students = read_csv_file('students')
        schedules = read_csv_file('schedules')
        periods = read_csv_file('periods')

        students = normalize_dataframe(students, value_columns=['Student Name', 'Course Name'])
        schedules = normalize_dataframe(schedules, value_columns=['Course Name'])
        periods = normalize_dataframe(periods, value_columns=['Course Name', 'Day of Week'])

        if empty_csvs:
            return jsonify({
                "status": "Error",
                "message": f"The following CSVs are empty: {', '.join(empty_csvs)}"
            }), 400

        # Remove old data for this user
        Students.query.filter_by(user_id=user_id).delete()
        Schedules.query.filter_by(user_id=user_id).delete()
        Periods.query.filter_by(user_id=user_id).delete()
        ValidationResults.query.filter_by(user_id=user_id).delete()
        StudentSchedules.query.filter_by(user_id=user_id).delete()
        UnassignedCourses.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        db.session.commit()


        # Insert new data
        for _, row in students.iterrows():
            db.session.add(Students(
            user_id=user_id,
            student_name=row['Student Name'],
            course_name=row['Course Name']
            ))
        for _, row in schedules.iterrows():
            db.session.add(Schedules(
            user_id=user_id,
            course_name=row['Course Name'],
            section=row['Section'],
            capacity=row['Capacity']
            ))
        for _, row in periods.iterrows():
            db.session.add(Periods(
            user_id=user_id,
            course_name=row['Course Name'],
            section=row['Section'],
            day_of_week=row['Day of Week'],
            period_number=row['Period Number']
            ))

        db.session.commit()

        return jsonify({"status": "Success", "message": "Files uploaded"})
    
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400

@app.route('/validate', methods=['GET'])
@require_login
def validate_data():
    user_id = session.get('user_id')  # Set after SSO

    students, schedules, periods = get_user_uploaded_data(user_id)
    if not all([students is not None, schedules is not None, periods is not None]):
        return jsonify({"status": "Error", "message": "Data not uploaded"}), 400

    validator = ScheduleDataValidator()
    valid, errors = validator.validate(students, schedules, periods)

    # Remove old validation result for this user
    ValidationResults.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    db.session.add(ValidationResults(user_id=user_id, valid=valid, errors=errors))
    db.session.commit()

    return jsonify({"valid": valid, "errors": errors})

@app.route('/optimize', methods=['POST'])
@require_login
def optimize_schedule():
    user_id = session.get('user_id')  # Set after SSO

    # Check if data is uploaded
    students, schedules, periods = get_user_uploaded_data(user_id)
    if students.empty or schedules.empty or periods.empty:
        return jsonify({"status": "Error", "message": "Data not uploaded"}), 400

    # Check validation result
    validation = ValidationResults.query.filter_by(user_id=user_id).order_by(ValidationResults.created_at.desc()).first()
    if not validation:
        return jsonify({"status": "Error", "message": "Data not validated"}), 400
    if not validation.valid:
        return jsonify({
            "status": "Error",
            "message": "Validation failed",
            "errors": validation.errors if validation.errors else []
        }), 400
    optimizer = ScheduleOptimizer()
    optimizer.run_solver(students, schedules, periods)
    
    # Get assignments and unassigned courses
    assigned = optimizer.get_assigned_courses()  # DataFrame: Student Name, Course Name, Section
    unassigned = optimizer.get_unassigned_courses()  # DataFrame: Student Name, Course Name

    # Remove old results for this user
    StudentSchedules.query.filter_by(user_id=user_id).delete()
    UnassignedCourses.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    # Insert assigned courses
    for _, row in assigned.iterrows():
        db.session.add(StudentSchedules(
            user_id=user_id,
            student_name=row['Student Name'],
            course_name=row['Course Name'],
            section=int(row['Section'])
        ))

    # Insert unassigned courses
    for _, row in unassigned.iterrows():
        db.session.add(UnassignedCourses(
            user_id=user_id,
            student_name=row['Student Name'],
            unassigned_course_name=row['Unassigned Course Name'],
            reason=row['Reason'] if 'Reason' in row else 'No reason provided'
        ))

    db.session.commit()

    return jsonify({"status": "Success", "message": "Optimization complete, assignments stored"})

@app.route('/assigned_courses', methods=['GET'])
@require_login
def get_assigned_courses():
    user_id = session.get('user_id')
    if not is_data_optimized(user_id):
        return jsonify({"status": "Error", "message": "Data not optimized"}), 400
    results = StudentSchedules.query.filter_by(user_id=user_id).all()
    data = [
        {
            "Student Name": r.student_name,
            "Course Name": r.course_name,
            "Section": r.section
        }
        for r in results
    ]
    return jsonify(data)

@app.route('/unassigned_courses', methods=['GET'])
@require_login
def get_unassigned_courses():
    user_id = session.get('user_id')
    if not is_data_optimized(user_id):
        return jsonify({"status": "Error", "message": "Data not optimized"}), 400
    results = UnassignedCourses.query.filter_by(user_id=user_id).all()
    data = [
        {
            "Student Name": r.student_name,
            "Unassigned Course Name": r.unassigned_course_name,
            "Reason": r.reason
        }
        for r in results
    ]
    return jsonify(data)

@app.route('/class_roster', methods=['GET'])
@require_login
def get_class_roster():
    user_id = session.get('user_id')
    if not is_data_optimized(user_id):
        return jsonify({"status": "Error", "message": "Data not optimized"}), 400
    course = request.args.get('course')
    section = request.args.get('section')
    if not course or not section:
        return jsonify({"status": "Error", "message": "Missing course or section parameter"}), 400

    # Check if the course/section exists in the Schedules table
    exists = Schedules.query.filter_by(
        user_id=user_id,
        course_name=course,
        section=int(section)
    ).first()
    if not exists:
        return jsonify({"status": "Error", "message": "The given course/section does not exist"}), 404

    # Get students registered for this course/section
    results = StudentSchedules.query.filter_by(
        user_id=user_id,
        course_name=course,
        section=int(section)
    ).all()
    student_names = [r.student_name for r in results]
    return jsonify(student_names)

@app.route('/student_schedule', methods=['GET'])
@require_login
def get_student_schedule():
    user_id = session.get('user_id')
    if not is_data_optimized(user_id):
        return jsonify({"status": "Error", "message": "Data not optimized"}), 400
    student = request.args.get('student')
    if not student:
        return jsonify({"status": "Error", "message": "Missing student parameter"}), 400
    results = StudentSchedules.query.filter_by(
        user_id=user_id,
        student_name=student
    ).all()
    data = [
        {
            "Course Name": r.course_name,
            "Section": r.section
        }
        for r in results
    ]
    return jsonify(data)

@app.route('/all_class_rosters', methods=['GET'])
@require_login
def get_all_class_rosters():
    user_id = session.get('user_id')
    if not is_data_optimized(user_id):
        return jsonify({"status": "Error", "message": "Data not optimized"}), 400

    # Get all classes/sections for this user
    classes = Schedules.query.filter_by(user_id=user_id).all()
    rosters = {}
    for c in classes:
        key = f"{c.course_name}.{c.section}"
        rosters[key] = []

    # Get all student assignments
    results = StudentSchedules.query.filter_by(user_id=user_id).all()
    for r in results:
        key = f"{r.course_name}.{r.section}"
        if key in rosters:
            rosters[key].append(r.student_name)
        else:
            rosters[key] = [r.student_name]

    return jsonify(rosters)

@app.route('/all_student_schedules', methods=['GET'])
@require_login
def get_all_student_schedules():
    user_id = session.get('user_id')
    if not is_data_optimized(user_id):
        return jsonify({"status": "Error", "message": "Data not optimized"}), 400
    results = StudentSchedules.query.filter_by(user_id=user_id).all()
    schedules = {}
    for r in results:
        schedules.setdefault(r.student_name, []).append({
            "Course Name": r.course_name,
            "Section": r.section
        })
    return jsonify(schedules)

if __name__ == '__main__':
    app.run(debug=True)
