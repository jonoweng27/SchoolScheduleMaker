from flask import Flask, request, jsonify, session, send_file
import pandas as pd
from data_validation.schedule_data_validator import ScheduleDataValidator
from optimization.schedule_optimizer import ScheduleOptimizer

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session

# In-memory storage for uploaded data and optimizer instance
DATA = {
    "students": None,
    "schedules": None,
    "periods": None,
    "optimizer": None,
    "validation": {}
}

@app.route('/upload', methods=['POST'])
def upload_data():
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

        if empty_csvs:
            return jsonify({
                "status": "Error",
                "message": f"The following CSVs are empty: {', '.join(empty_csvs)}"
            }), 400

        print('printed periods')
        DATA['students'] = students
        DATA['schedules'] = schedules
        DATA['periods'] = periods
        DATA['optimizer'] = None  # Reset optimizer
        DATA['validation'] = {}  # Reset validation
        return jsonify({"status": "Success", "message": "Files uploaded"})
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 400

@app.route('/validate', methods=['GET'])
def validate_data():
    if not all([DATA['students'] is not None, DATA['schedules'] is not None, DATA['periods'] is not None]):
        return jsonify({"status": "Error", "message": "Data not uploaded"}), 400
    validator = ScheduleDataValidator()
    valid, errors = validator.validate(DATA['students'], DATA['schedules'], DATA['periods'])
    DATA['validation'] = {"valid": valid, "errors": errors}
    return jsonify({"valid": valid, "errors": errors})

@app.route('/optimize', methods=['POST'])
def optimize_schedule():
    if not all([DATA['students'] is not None, DATA['schedules'] is not None, DATA['periods'] is not None]):
        return jsonify({"status": "Error", "message": "Data not uploaded"}), 400
    validation = DATA.get('validation', {})
    if 'valid' not in validation:
        return jsonify({"status": "Error", "message": "Data not validated"}), 400
    if not validation.get('valid', False):
        return jsonify({
            "status": "Error",
            "message": "Validation failed",
            "errors": validation.get('errors', [])
        }), 400
    optimizer = ScheduleOptimizer()
    optimizer.run_solver(DATA['students'], DATA['schedules'], DATA['periods'])
    DATA['optimizer'] = optimizer
    return jsonify({"status": "Success", "message": "Optimization complete"})

@app.route('/assigned_courses', methods=['GET'])
def get_assigned_courses():
    optimizer = DATA.get('optimizer')
    if optimizer is None:
        return jsonify({"status": "Error", "message": "Optimization not run"}), 400
    df = optimizer.get_assigned_courses()
    return df.to_json(orient='records')

@app.route('/unassigned_courses', methods=['GET'])
def get_unassigned_courses():
    optimizer = DATA.get('optimizer')
    if optimizer is None:
        return jsonify({"status": "Error", "message": "Optimization not run"}), 400
    df = optimizer.get_unassigned_courses()
    return df.to_json(orient='records')

@app.route('/class_roster', methods=['GET'])
def get_class_roster():
    optimizer = DATA.get('optimizer')
    if optimizer is None:
        return jsonify({"status": "Error", "message": "Optimization not run"}), 400
    course = request.args.get('course')
    section = request.args.get('section')
    if not course or not section:
        return jsonify({"status": "Error", "message": "Missing course or section parameter"}), 400
    try:
        df = optimizer.get_class_roster(course, int(section))
        if df is None or df.empty:
            return jsonify({"status": "Error", "message": "The given course/section does not exist"}), 404
        return df.to_json(orient='records')
    except Exception:
        return jsonify({"status": "Error", "message": "The given course/section does not exist"}), 404

@app.route('/student_schedule', methods=['GET'])
def get_student_schedule():
    optimizer = DATA.get('optimizer')
    if optimizer is None:
        return jsonify({"status": "Error", "message": "Optimization not run"}), 400
    student = request.args.get('student')
    if not student:
        return jsonify({"status": "Error", "message": "Missing student parameter"}), 400
    try:
        df = optimizer.get_student_schedule(student)
        if df is None or (hasattr(df, 'empty') and df.empty):
            return jsonify({"status": "Error", "message": "Student does not exist"}), 404
        return df.to_json()
    except Exception:
        return jsonify({"status": "Error", "message": "Student does not exist"}), 404

@app.route('/all_class_rosters', methods=['GET'])
def get_all_class_rosters():
    optimizer = DATA.get('optimizer')
    if optimizer is None:
        return jsonify({"status": "Error", "message": "Optimization not run"}), 400
    rosters = optimizer.get_all_class_rosters()
    # Convert each DataFrame to JSON
    result = {str(k): v.to_dict(orient='records') for k, v in rosters.items()}
    return jsonify(result)

@app.route('/all_student_schedules', methods=['GET'])
def get_all_student_schedules():
    optimizer = DATA.get('optimizer')
    if optimizer is None:
        return jsonify({"status": "Error", "message": "Optimization not run"}), 400
    schedules = optimizer.get_all_student_schedules()
    # Convert each DataFrame to JSON
    result = {k: v.to_dict() for k, v in schedules.items()}
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)