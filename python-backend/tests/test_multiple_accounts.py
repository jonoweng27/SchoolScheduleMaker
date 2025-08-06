import pytest
from flask import Flask
from app import app as flask_app
import json
import os
import base64

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

# Credentials for two accounts
CREDENTIALS_BASIC = base64.b64encode(b"Basic Data:school").decode("utf-8")
CREDENTIALS_TWELFTH = base64.b64encode(b"Twelfth Grade Data:school").decode("utf-8")

AUTH_HEADERS_BASIC = {'Authorization': f'Basic {CREDENTIALS_BASIC}'}
AUTH_HEADERS_TWELFTH = {'Authorization': f'Basic {CREDENTIALS_TWELFTH}'}

def test_multiple_accounts_alternating_calls(client):
    # Paths for both datasets
    basic_dir = os.path.join(os.path.dirname(__file__), "data", "BasicData")
    twelfth_dir = os.path.join(os.path.dirname(__file__), "data", "TwelfthGrade")

    # Upload BasicData
    with open(os.path.join(basic_dir, 'Students.csv'), 'rb') as students_file, \
         open(os.path.join(basic_dir, 'Schedules.csv'), 'rb') as schedules_file, \
         open(os.path.join(basic_dir, 'Periods.csv'), 'rb') as periods_file:
        data_basic = {
            'students': (students_file, 'Students.csv'),
            'schedules': (schedules_file, 'Schedules.csv'),
            'periods': (periods_file, 'Periods.csv')
        }
        upload_response_basic = client.post(
            '/upload',
            data=data_basic,
            content_type='multipart/form-data',
            headers=AUTH_HEADERS_BASIC
        )
        assert upload_response_basic.status_code == 200
        json_data = upload_response_basic.get_json()
        assert json_data['status'] == 'Success'

    # Upload TwelfthGradeData
    with open(os.path.join(twelfth_dir, 'Students.csv'), 'rb') as students_file, \
         open(os.path.join(twelfth_dir, 'Schedules.csv'), 'rb') as schedules_file, \
         open(os.path.join(twelfth_dir, 'Periods.csv'), 'rb') as periods_file:
        data_twelfth = {
            'students': (students_file, 'Students.csv'),
            'schedules': (schedules_file, 'Schedules.csv'),
            'periods': (periods_file, 'Periods.csv')
        }
        upload_response_twelfth = client.post(
            '/upload',
            data=data_twelfth,
            content_type='multipart/form-data',
            headers=AUTH_HEADERS_TWELFTH
        )
        assert upload_response_twelfth.status_code == 200
        json_data = upload_response_twelfth.get_json()
        assert json_data['status'] == 'Success'

    # Optimize BasicData
    optimize_response_basic = client.post(
        '/optimize',
        headers=AUTH_HEADERS_BASIC
    )
    assert optimize_response_basic.status_code == 200

    # Optimize TwelfthGradeData
    optimize_response_twelfth = client.post(
        '/optimize',
        headers=AUTH_HEADERS_TWELFTH
    )
    assert optimize_response_twelfth.status_code == 200

    # Get unassigned courses for BasicData
    response_basic = client.get(
        '/unassigned_courses',
        headers=AUTH_HEADERS_BASIC
    )
    assert response_basic.status_code == 200
    json_basic = response_basic.get_json()
    if json_basic is None:
        json_basic = json.loads(response_basic.data.decode('utf-8'))
    assert json_basic is not None
    student_names_basic = {course['Student Name'] for course in json_basic}
    assert 'Jonathan Wenger' not in student_names_basic
    assert 'I' in student_names_basic
    assert student_names_basic == {'G', 'H', 'I', 'J'}

    # Get unassigned courses for TwelfthGradeData
    response_twelfth = client.get(
        '/unassigned_courses',
        headers=AUTH_HEADERS_TWELFTH
    )
    assert response_twelfth.status_code == 200
    json_twelfth = response_twelfth.get_json()
    if json_twelfth is None:
        json_twelfth = json.loads(response_twelfth.data.decode('utf-8'))
    assert json_twelfth is not None
    student_names_twelfth = {course['Student Name'] for course in json_twelfth}
    assert 'Jonathan Wenger' in student_names_twelfth
    assert 'D' not in student_names_twelfth
    reasons_twelfth = {course['Reason'] for course in json_twelfth}
    assert 'Time Conflict' in reasons_twelfth
