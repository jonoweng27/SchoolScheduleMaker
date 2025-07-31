from flask import Flask, request, jsonify, g
from models import db, Users, Students, Schedules, Periods, ValidationResults, AssignedCourses, UnassignedCourses
from data_validation.schedule_data_validator import ScheduleDataValidator
from optimization.schedule_optimizer import ScheduleOptimizer
from utils import normalize_dataframe
from functools import wraps
from passlib.hash import bcrypt
import pandas as pd


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/ScheduleBackEnd'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return jsonify({"status": "Error", "message": "Authentication required"}), 401
        user = Users.query.filter_by(username=auth.username).first()
        if not user or not bcrypt.verify(auth.password, user.password_hash):
            return jsonify({"status": "Error", "message": "Invalid credentials"}), 401
        g.user = user  # Store user in Flask global context
        return f(*args, **kwargs)
    return decorated

# Example registration endpoint (for creating users)
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    name = data.get('name')
    if not username or not password:
        return jsonify({"status": "Error", "message": "Username and password required"}), 400
    if Users.query.filter_by(username=username).first():
        return jsonify({"status": "Error", "message": "Username already exists"}), 400
    password_hash = bcrypt.hash(password)
    user = Users(username=username, password_hash=password_hash, email=email, name=name)
    db.session.add(user)
    db.session.commit()
    return jsonify({"status": "Success", "message": "User registered"})


@app.route('/upload', methods=['POST'])
@require_auth
def upload_data():
    user_id = g.user.id
    
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

        # Normalize dataframes
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
        AssignedCourses.query.filter_by(user_id=user_id).delete()
        UnassignedCourses.query.filter_by(user_id=user_id).delete()
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
@require_auth
def validate_data():
    user_id = g.user.id  # Set after SSO

    students, schedules, periods = get_user_uploaded_data(user_id)
    if not all([students is not None, schedules is not None, periods is not None]):
        return jsonify({"status": "Error", "message": "Data not uploaded"}), 400

    validator = ScheduleDataValidator()
    valid, errors = validator.validate(students, schedules, periods)

    # Remove old validation results for this user
    ValidationResults.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    db.session.add(ValidationResults(user_id=user_id, valid=valid, errors=errors))
    db.session.commit()

    return jsonify({"valid": valid, "errors": errors})

@app.route('/optimize', methods=['POST'])
@require_auth
def optimize_schedule():
    user_id = g.user.id  # Set after SSO

    # Check if data is uploaded
    students, schedules, periods = get_user_uploaded_data(user_id)
    if students is None or schedules is None or periods is None:
        return jsonify({"status": "Error", "message": "Data not uploaded"}), 400
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
    
    # Run the optimizer
    optimizer = ScheduleOptimizer()
    optimizer.run_solver(students, schedules, periods)
    
    # Get assignments and unassigned courses
    assigned = optimizer.get_assigned_courses()  # DataFrame: Student Name, Course Name, Section
    unassigned = optimizer.get_unassigned_courses()  # DataFrame: Student Name, Course Name

    # Remove old results for this user
    AssignedCourses.query.filter_by(user_id=user_id).delete()
    UnassignedCourses.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    # Insert assigned courses
    for _, row in assigned.iterrows():
        db.session.add(AssignedCourses(
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
@require_auth
def get_assigned_courses():
    user_id = g.user.id
    if not is_data_optimized(user_id):
        return jsonify({"status": "Error", "message": "Data not optimized"}), 400
    results = AssignedCourses.query.filter_by(user_id=user_id).all()
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
@require_auth
def get_unassigned_courses():
    user_id = g.user.id
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
@require_auth
def get_class_roster():
    user_id = g.user.id
    if not is_data_optimized(user_id):
        return jsonify({"status": "Error", "message": "Data not optimized"}), 400
    course = request.args.get('course')
    section = request.args.get('section')
    if not course or not section:
        return jsonify({"status": "Error", "message": "Missing course or section parameter"}), 400

    try:
        section = int(section)
    except ValueError:
        return jsonify({"status": "Error", "message": "Section must be an integer"}), 400

    try:
        # Get schedules DataFrame for this user
        schedules_df = pd.read_sql(
            Schedules.query.filter_by(user_id=user_id).statement, db.engine
        )
        match = schedules_df['Course Name'].str.lower() == course.strip().lower()
        if not match.any():
            return jsonify({"status": "Error", "message": "The given course/section does not exist"}), 404
        course_name = schedules_df.loc[match, 'Course Name'].iloc[0]

        # Get assigned courses DataFrame for this user
        assigned_df = pd.read_sql(
            AssignedCourses.query.filter_by(user_id=user_id).statement, db.engine
        )
        roster = assigned_df[
            (assigned_df['Course Name'] == course_name) & (assigned_df['Section'] == section)
        ]
        if roster.empty:
            return jsonify({"status": "Error", "message": "The given course/section does not exist"}), 404
        return roster['Student Name'].to_json(orient='values')
    except Exception:
        return jsonify({"status": "Error", "message": "The given course/section does not exist"}), 404

@app.route('/student_schedule', methods=['GET'])
@require_auth
def get_student_schedule():
    user_id = g.user.id
    if not is_data_optimized(user_id):
        return jsonify({"status": "Error", "message": "Data not optimized"}), 400
    student = request.args.get('student')
    if not student:
        return jsonify({"status": "Error", "message": "Missing student parameter"}), 400

    try:
        # Get students DataFrame for this user
        students_df = pd.read_sql(
            Students.query.filter_by(user_id=user_id).statement, db.engine
        )
        match = students_df['Student Name'].str.lower() == student.strip().lower()
        if not match.any():
            return jsonify({"status": "Error", "message": f"Student '{student}' not found for this user"}), 404
        student_name = students_df.loc[match, 'Student Name'].iloc[0]

        # Get assigned courses DataFrame for this user
        assigned_df = pd.read_sql(
            AssignedCourses.query.filter_by(user_id=user_id).statement, db.engine
        )
        schedule = assigned_df[assigned_df['Student Name'] == student_name]
        data = schedule[['Course Name', 'Section']].to_dict(orient='records')
        return jsonify(data)
    except Exception:
        return jsonify({"status": "Error", "message": f"Student '{student}' not found for this user"}), 404

@app.route('/all_class_rosters', methods=['GET'])
@require_auth
def get_all_class_rosters():
    user_id = g.user.id
    if not is_data_optimized(user_id):
        return jsonify({"status": "Error", "message": "Data not optimized"}), 400

    # Get all classes/sections for this user
    classes = Schedules.query.filter_by(user_id=user_id).all()
    rosters = {}
    for c in classes:
        key = f"{c.course_name}.{c.section}"
        rosters[key] = []

    # Get all student assignments
    results = AssignedCourses.query.filter_by(user_id=user_id).all()
    for r in results:
        key = f"{r.course_name}.{r.section}"
        if key in rosters:
            rosters[key].append(r.student_name)
        else:
            rosters[key] = [r.student_name]

    return jsonify(rosters)

@app.route('/all_student_schedules', methods=['GET'])
@require_auth
def get_all_student_schedules():
    user_id = g.user.id
    if not is_data_optimized(user_id):
        return jsonify({"status": "Error", "message": "Data not optimized"}), 400
    results = AssignedCourses.query.filter_by(user_id=user_id).all()
    schedules = {}
    for r in results:
        schedules.setdefault(r.student_name, []).append({
            "Course Name": r.course_name,
            "Section": r.section
        })
    return jsonify(schedules)

# Get the uploaded data for a user
def get_user_uploaded_data(user_id):
    students = pd.read_sql(Students.query.filter_by(user_id=user_id).statement, db.engine)
    schedules = pd.read_sql(Schedules.query.filter_by(user_id=user_id).statement, db.engine)
    periods = pd.read_sql(Periods.query.filter_by(user_id=user_id).statement, db.engine)
    if students.empty or schedules.empty or periods.empty:
        return None, None, None
    return students, schedules, periods

# Checks if the data for a user has been optimized
def is_data_optimized(user_id):
    assigned_exists = db.session.query(AssignedCourses.query.filter_by(user_id=user_id).exists()).scalar()
    unassigned_exists = db.session.query(UnassignedCourses.query.filter_by(user_id=user_id).exists()).scalar()
    return assigned_exists or unassigned_exists

if __name__ == '__main__':
    app.run(debug=True)
