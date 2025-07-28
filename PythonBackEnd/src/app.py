from flask import Flask, request, jsonify, session
import pandas as pd
from models import db, Students, Schedules, Periods, ValidationResults, OptimizationResults
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

    # Remove old validation results for this user
    ValidationResults.query.filter_by(user_id=user_id).delete()
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
    
    # Serialize only the assignments
    assignments = optimizer.get_assignments()

    # Delete any old optimization results for this user
    OptimizationResults.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    # Store the assignments in the optimization_results table (as JSON)
    db.session.add(OptimizationResults(user_id=user_id, assignments_json=assignments))
    db.session.commit()

    return jsonify({"status": "Success", "message": "Optimization complete, assignments stored"})


def get_optimizer_for_user():
    user_id = session.get('user_id')
    if not user_id:
        return None, jsonify({"status": "Error", "message": "Not authenticated"}), 401
    opt_result = OptimizationResults.query.filter_by(user_id=user_id).order_by(OptimizationResults.created_at.desc()).first()
    if not opt_result or not opt_result.assignments_json:
        return None, jsonify({"status": "Error", "message": "Optimization not run"}), 400
    try:
        assignments = opt_result.assignments_json
        students, schedules, periods = get_user_uploaded_data(user_id)
        optimizer = ScheduleOptimizer()
        optimizer.run_solver(students, schedules, periods)
        optimizer.set_assignments(assignments)
        return optimizer, None, None
    except Exception:
        return None, jsonify({"status": "Error", "message": "Failed to load optimizer"}), 500

@app.route('/assigned_courses', methods=['GET'])
@require_login
def get_assigned_courses():
    optimizer, error_response, status = get_optimizer_for_user()
    if error_response:
        return error_response, status
    df = optimizer.get_assigned_courses()
    return df.to_json(orient='records')

@app.route('/unassigned_courses', methods=['GET'])
@require_login
def get_unassigned_courses():
    optimizer, error_response, status = get_optimizer_for_user()
    if error_response:
        return error_response, status
    df = optimizer.get_unassigned_courses()
    return df.to_json(orient='records')

@app.route('/class_roster', methods=['GET'])
@require_login
def get_class_roster():
    optimizer, error_response, status = get_optimizer_for_user()
    if error_response:
        return error_response, status
    course = request.args.get('course')
    section = request.args.get('section')
    if not course or not section:
        return jsonify({"status": "Error", "message": "Missing course or section parameter"}), 400
    try:
        schedules_df = pd.read_sql(Schedules.query.filter_by(user_id=session.get('user_id')).statement, db.engine)
        match = (schedules_df['Course Name'].str.lower() == course.strip().lower()) & (schedules_df['Section'].astype(str) == str(section))
        if not match.any():
            return jsonify({"status": "Error", "message": "The given course/section does not exist"}), 404
        course_name = schedules_df.loc[match, 'Course Name'].iloc[0]
        section_num = schedules_df.loc[match, 'Section'].iloc[0]
        df = optimizer.get_class_roster(course_name, section_num)
        if isinstance(df, str):
            return jsonify({"status": "Error", "message": df}), 404
        # Return empty list if no students are registered
        return df.to_json(orient='records')
    except Exception:
        return jsonify({"status": "Error", "message": "The given course/section does not exist"}), 404

@app.route('/student_schedule', methods=['GET'])
@require_login
def get_student_schedule():
    optimizer, error_response, status = get_optimizer_for_user()
    if error_response:
        return error_response, status
    student = request.args.get('student')
    if not student:
        return jsonify({"status": "Error", "message": "Missing student parameter"}), 400
    try:
        students_df = pd.read_sql(Students.query.filter_by(user_id=session.get('user_id')).statement, db.engine)
        match = students_df['Student Name'].str.lower() == student.strip().lower()
        if not match.any():
            return jsonify({"status": "Error", "message": "Student does not exist"}), 404
        student = students_df.loc[match, 'Student Name'].iloc[0]
        df = optimizer.get_student_schedule(student)
        if df is None or (hasattr(df, 'empty') and df.empty):
            return jsonify({"status": "Error", "message": "Student does not exist"}), 404
        return df.to_json()
    except Exception:
        return jsonify({"status": "Error", "message": "Student does not exist"}), 404

@app.route('/all_class_rosters', methods=['GET'])
@require_login
def get_all_class_rosters():
    optimizer, error_response, status = get_optimizer_for_user()
    if error_response:
        return error_response, status
    rosters = optimizer.get_all_class_rosters()
    result = {str(k): v.to_dict(orient='records') for k, v in rosters.items()}
    return jsonify(result)

@app.route('/all_student_schedules', methods=['GET'])
@require_login
def get_all_student_schedules():
    optimizer, error_response, status = get_optimizer_for_user()
    if error_response:
        return error_response, status
    schedules = optimizer.get_all_student_schedules()
    result = {k: v.to_dict() for k, v in schedules.items()}
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
