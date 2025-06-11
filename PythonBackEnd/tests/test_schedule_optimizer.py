import os
import pandas as pd
from optimization.schedule_optimizer import ScheduleOptimizer

#TODO: Add/Test Data Validation

def get_data(DataType):
    # Path to your test data
    data_dir = os.path.join(os.path.dirname(__file__), "data", DataType)
    students_csv = os.path.join(data_dir, "Students.csv")
    schedules_csv = os.path.join(data_dir, "Schedules.csv")
    periods_csv = os.path.join(data_dir, "Periods.csv")

    # Load data
    students_df = pd.read_csv(students_csv)
    schedules_df = pd.read_csv(schedules_csv)
    periods_df = pd.read_csv(periods_csv)

    return students_df, schedules_df, periods_df

def generate_basic_data_model():
    students_df, schedules_df, periods_df = get_data("BasicData")
    # Run optimizer
    optimizer = ScheduleOptimizer()
    optimizer.run_solver(students_df, schedules_df, periods_df)
    return optimizer

def test_assigned_courses():
    optimizer = generate_basic_data_model()
    assigned_df = optimizer.get_assigned_courses()
    assert len(assigned_df) == 44

def test_unassigned_courses():
    optimizer = generate_basic_data_model()
    unassigned_df = optimizer.get_unassigned_courses()
    assert len(unassigned_df) == 4
    assert set(['G', 'H', 'I', 'J']).issubset(set(unassigned_df['Student Name'].values))

def test_class_roster():
    optimizer = generate_basic_data_model()
    class_roster_low_history = optimizer.get_class_roster('Low History', 1)
    assert len(class_roster_low_history) == 4
    assert set(['A', 'L', 'I', 'J']).issubset(set(class_roster_low_history['Student Name'].values))


def test_all_class_rosters():
    optimizer = generate_basic_data_model()
    class_rosters = optimizer.get_all_class_rosters()
    assert len(class_rosters) == 16
    low_history_section_1 = class_rosters[('Low History', 1)]
    assert len(low_history_section_1) == 4
    assert set(['A', 'L', 'I', 'J']).issubset(set(low_history_section_1['Student Name'].values))

def test_student_schedule():
    optimizer = generate_basic_data_model()
    student_schedule = optimizer.get_student_schedule('L')
    assert len(student_schedule) == 4

    # Assert that 'L' has 'Low English' in period 1 on Monday
    # Check that 'Low English' is scheduled for 'L' in period 1 on Monday
    assert any(
        row['Monday'] == 'Low English.1'
        for _, row in student_schedule.iterrows()
    ), "'Low English.1' not found in 'L' schedule for Monday period 1"

def test_all_student_schedules():
    optimizer = generate_basic_data_model()
    all_schedules = optimizer.get_all_student_schedules()
    # There should be 12 students in the basic data
    assert len(all_schedules) == 12

    # Check that student 'L' has 'Low English' in period 1 on Monday
    l_schedule = all_schedules['L']
    assert any(
        row['Monday'] == 'Low English.1'
        for _, row in l_schedule.iterrows()
    ), "'Low English.1' not found in 'L' schedule for Monday period 1"

def test_basic_data():
    students_df, schedules_df, periods_df = get_data("BasicData")
    # Run optimizer
    optimizer = ScheduleOptimizer()
    optimizer.run_solver(students_df, schedules_df, periods_df)
    
    # For all students not G, H, I, or J, check their assigned courses
    assigned_df = optimizer.get_assigned_courses()
    other_students = students_df[~students_df['Student Name'].isin(['G', 'H', 'I', 'J'])]

    for student_name in other_students['Student Name']:
        required_courses = set(students_df[students_df['Student Name'] == student_name]['Course Name'].values)
        assigned_courses = set(assigned_df[assigned_df['Student Name'] == student_name]['Course Name'].values)
        assert required_courses == assigned_courses, f"Mismatch for {student_name}: required {required_courses}, assigned {assigned_courses}"


def test_twelfth_grade():
    students_df, schedules_df, periods_df = get_data("TwelfthGrade")
    # Run optimizer
    optimizer = ScheduleOptimizer()
    optimizer.run_solver(students_df, schedules_df, periods_df)

    # Get unassigned courses DataFrame
    unassigned_df = optimizer.get_unassigned_courses()

    # Assert the number of unassigned courses is 6
    assert len(unassigned_df) == 6

    assert "Jonathan Wenger" in unassigned_df['Student Name'].values

    required_courses = set(students_df[students_df['Student Name'] == 'Joshua Trauring']['Course Name'].values)
    assigned_courses = set(optimizer.get_assigned_courses()[optimizer.get_assigned_courses()['Student Name'] == 'Joshua Trauring']['Course Name'].values)
    assert required_courses == assigned_courses, f"Mismatch for Joshua Trauring: required {required_courses}, assigned {assigned_courses}"
