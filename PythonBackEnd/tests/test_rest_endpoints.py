import pytest
from flask import Flask
from app import app as flask_app
import json
import os

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

def pytest_runtest_makereport(item, call):
    """Hook to stop further tests in this module if one fails."""
    if call.when == 'call' and call.excinfo is not None:
        pytest.exit("Test failed, stopping further tests in this module.")


# Now you can write your test cases using the 'client' fixture.
@pytest.mark.run(order=1)
def test_upload_files(client):
    base_dir = os.path.join(os.path.dirname(__file__), "data", "BasicData")
    with open(os.path.join(base_dir, 'Students.csv'), 'rb') as students_file, \
         open(os.path.join(base_dir, 'Schedules.csv'), 'rb') as schedules_file, \
         open(os.path.join(base_dir, 'Periods.csv'), 'rb') as periods_file:
        data = {
            'students': (students_file, 'Students.csv'),
            'schedules': (schedules_file, 'Schedules.csv'),
            'periods': (periods_file, 'Periods.csv')
        }
        response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'Success'
    assert json_data['message'] == 'Files uploaded'

@pytest.mark.run(order=2)
def test_validate(client):
    response = client.get('/validate')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['valid'] is True
    assert isinstance(json_data['errors'], list)
    assert len(json_data['errors']) == 0


@pytest.mark.run(order=3)
def test_optimize(client):
    response = client.post('/optimize')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'Success'
    assert json_data['message'] == 'Optimization complete'

@pytest.mark.run(order=4)
def test_class_roster_high_math_section_1(client):
    # Call class_roster for "High Math", section 1 using query parameters
    response = client.get('/class_roster?course=High Math&section=1')
    assert response.status_code == 200
    json_data = response.get_json()
    if json_data is None:
        json_data = json.loads(response.data.decode('utf-8'))
    assert isinstance(json_data, list)
    assert len(json_data) > 0
    # Save for comparison in next test
    global high_math_section_1_roster
    high_math_section_1_roster = json_data

@pytest.mark.run(order=5)
def test_class_roster_high_math_section_1_case_insensitive(client):
    # Call class_roster for "hIgH MAtH", section 1 (case-insensitive) using query parameters
    response = client.get('/class_roster?course=hIgH MAtH&section=1')
    assert response.status_code == 200
    json_data = response.get_json()
    if json_data is None:
        json_data = json.loads(response.data.decode('utf-8'))
    assert isinstance(json_data, list)
    # Compare with previous result
    global high_math_section_1_roster
    assert json_data == high_math_section_1_roster



@pytest.mark.run(order=6)
def test_get_unassigned_courses(client):
    # Ensure test data is uploaded before calling the endpoint
    base_dir = os.path.join(os.path.dirname(__file__), "data", "MixedCaseData")
    with open(os.path.join(base_dir, 'Students.csv'), 'rb') as students_file, \
         open(os.path.join(base_dir, 'Schedules.csv'), 'rb') as schedules_file, \
         open(os.path.join(base_dir, 'Periods.csv'), 'rb') as periods_file:
        data = {
            'students': (students_file, 'Students.csv'),
            'schedules': (schedules_file, 'Schedules.csv'),
            'periods': (periods_file, 'Periods.csv')
        }
        upload_response = client.post('/upload', data=data, content_type='multipart/form-data')
        assert upload_response.status_code == 200

    # Optionally, validate and optimize if required by your backend logic
    validate_response = client.get('/validate')
    assert validate_response.status_code == 200

    optimize_response = client.post('/optimize')
    assert optimize_response.status_code == 200

    response = client.get('/unassigned_courses')
    assert response.status_code == 200
    # Try to get JSON, if None, parse manually
    json_data = response.get_json()
    if json_data is None:
        json_data = json.loads(response.data.decode('utf-8'))
    assert json_data is not None, f"Response JSON is None. Response data: {response.data}"
    assert len(json_data) == 4
    student_names = {course['Student Name'] for course in json_data}
    assert student_names == {'G', 'H', 'I', 'J'}
    reasons = {course['Reason'] for course in json_data}
    assert reasons == {'Time Conflict'}
    course_names = {course['Unassigned Course'] for course in json_data}
    assert course_names == {'High History', 'Low English', 'Medium English', 'High English'}