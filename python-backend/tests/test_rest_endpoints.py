import pytest
from flask import Flask
from app import app as flask_app, generate_access_token
from models import db, Users
import json
import os
import base64
from datetime import datetime, timezone, timedelta
import jwt
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        with flask_app.app_context():
            # Clean up test users
            Users.query.filter(Users.email.like('test-user-%')).delete()
            db.session.commit()
        yield client
        with flask_app.app_context():
            Users.query.filter(Users.email.like('test-user-%')).delete()
            db.session.commit()

@pytest.fixture
def auth_headers(client):
    with flask_app.app_context():
        # Create or get test user
        email = 'test-user-rest@test.com'
        user = Users.query.filter_by(email=email).first()
        if not user:
            user = Users(
                google_id='test-google-id-rest',
                email=email,
                name='Test User REST',
                profile_picture='test-pic.jpg',
                last_login=db.func.now(),
                email_verified=True
            )
            db.session.add(user)
            db.session.commit()
        
        token, _ = generate_access_token(user.id)
        return {'Authorization': f'Bearer {token}'}

def test_straight_path(client, auth_headers):
    base_dir = os.path.join(os.path.dirname(__file__), "data", "BasicData")
    with open(os.path.join(base_dir, 'Students.csv'), 'rb') as students_file, \
         open(os.path.join(base_dir, 'Schedules.csv'), 'rb') as schedules_file, \
         open(os.path.join(base_dir, 'Periods.csv'), 'rb') as periods_file:
        data = {
            'students': (students_file, 'Students.csv'),
            'schedules': (schedules_file, 'Schedules.csv'),
            'periods': (periods_file, 'Periods.csv')
        }
        upload_response = client.post(
            '/upload',
            data=data,
            content_type='multipart/form-data',
            headers=auth_headers
        )
        assert upload_response.status_code == 200
        json_data = upload_response.get_json()
        assert json_data['status'] == 'Success'
        assert json_data['message'] == 'Files uploaded and validated'

    optimize_response = client.post(
        '/optimize',
        headers=auth_headers
    )
    assert optimize_response.status_code == 200

    response = client.get(
        '/unassigned_courses',
        headers=auth_headers
    )
    assert response.status_code == 200
    json_data = response.get_json()
    if json_data is None:
        json_data = json.loads(response.data.decode('utf-8'))
    assert json_data is not None, f"Response JSON is None. Response data: {response.data}"
    assert len(json_data) == 4
    student_names = {course['Student Name'] for course in json_data}
    assert student_names == {'G', 'H', 'I', 'J'}
    reasons = {course['Reason'] for course in json_data}
    assert reasons == {'Time Conflict'}

def test_mixed_case(client, auth_headers):
    base_dir = os.path.join(os.path.dirname(__file__), "data", "MixedCaseData")
    with open(os.path.join(base_dir, 'Students.csv'), 'rb') as students_file, \
         open(os.path.join(base_dir, 'Schedules.csv'), 'rb') as schedules_file, \
         open(os.path.join(base_dir, 'Periods.csv'), 'rb') as periods_file:
        data = {
            'students': (students_file, 'Students.csv'),
            'schedules': (schedules_file, 'Schedules.csv'),
            'periods': (periods_file, 'Periods.csv')
        }
        response = client.post(
            '/upload',
            data=data,
            content_type='multipart/form-data',
            headers=auth_headers
        )
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'Success'
    assert json_data['message'] == 'Files uploaded and validated'

    response = client.post(
        '/optimize',
        headers=auth_headers
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'Success'
    assert json_data['message'] == 'Optimization complete, assignments stored'

    response = client.get(
        '/class_roster?course=High Math&section=1',
        headers=auth_headers
    )
    assert response.status_code == 200
    json_data = response.get_json()
    if json_data is None:
        json_data = json.loads(response.data.decode('utf-8'))
    assert isinstance(json_data, list)
    assert len(json_data) > 0
    high_math_section_1_roster = json_data

    response = client.get(
        '/class_roster?course=hIgH MAtH&section=1',
        headers=auth_headers
    )
    assert response.status_code == 200
    json_data_case = response.get_json()
    if json_data_case is None:
        json_data_case = json.loads(response.data.decode('utf-8'))
    assert isinstance(json_data_case, list)
    assert json_data_case == high_math_section_1_roster

def test_bad_data(client, auth_headers):
    base_dir = os.path.join(os.path.dirname(__file__), "data", "BadData")
    with open(os.path.join(base_dir, 'Students.csv'), 'rb') as students_file, \
            open(os.path.join(base_dir, 'Schedules.csv'), 'rb') as schedules_file, \
            open(os.path.join(base_dir, 'Periods.csv'), 'rb') as periods_file:
        data = {
            'students': (students_file, 'Students.csv'),
            'schedules': (schedules_file, 'Schedules.csv'),
            'periods': (periods_file, 'Periods.csv')
        }
        response = client.post(
            '/upload',
            data=data,
            content_type='multipart/form-data',
            headers=auth_headers
        )
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['status'] == 'Error'
    assert isinstance(json_data['errors'], list)
    assert len(json_data['errors']) == 8