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


# Test cases for the REST API endpoints in the Flask application
def test_straight_path(client):
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

    response = client.get('/validate')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['valid'] is True
    assert isinstance(json_data['errors'], list)
    assert len(json_data['errors']) == 0

    response = client.post('/optimize')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'Success'
    assert json_data['message'] == 'Optimization complete'

    # Test /class_roster endpoint for "High Math", section 1
    response = client.get('/class_roster?course=High Math&section=1')
    assert response.status_code == 200
    json_data = response.get_json()
    if json_data is None:
        json_data = json.loads(response.data.decode('utf-8'))
    assert isinstance(json_data, list)
    assert len(json_data) > 0
    high_math_section_1_roster = json_data

    # Test /class_roster endpoint for "hIgH MAtH", section 1 (case-insensitive)
    response = client.get('/class_roster?course=hIgH MAtH&section=1')
    assert response.status_code == 200
    json_data_case = response.get_json()
    if json_data_case is None:
        json_data_case = json.loads(response.data.decode('utf-8'))
    assert isinstance(json_data_case, list)
    assert json_data_case == high_math_section_1_roster

def test_mixed_case(client):
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

    
def test_bad_data(client):
    # Attempt to upload malformed or incomplete data files
    base_dir = os.path.join(os.path.dirname(__file__), "data", "BadData")
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

    # Validate should fail due to bad data
    response = client.get('/validate')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['valid'] is False
    assert isinstance(json_data['errors'], list)
    assert len(json_data['errors']) > 0

    # Optimize should not succeed if validation failed
    response = client.post('/optimize')
    assert response.status_code == 400 or response.get_json()['status'] == 'Error'
