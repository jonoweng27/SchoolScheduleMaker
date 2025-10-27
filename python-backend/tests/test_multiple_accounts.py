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

@pytest.fixture
def auth_headers_basic(client):
    with flask_app.app_context():
        # Create or get test user for basic data
        email = 'test-user-basic@test.com'
        user = Users.query.filter_by(email=email).first()
        if not user:
            user = Users(
                google_id='test-google-id-basic',
                email=email,
                name='Test User Basic',
                profile_picture='test-pic-basic.jpg',
                last_login=db.func.now(),
                email_verified=True
            )
            db.session.add(user)
            db.session.commit()
        
        token, _ = generate_access_token(user.id)
        return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def auth_headers_twelfth(client):
    with flask_app.app_context():
        # Create or get test user for twelfth grade data
        email = 'test-user-twelfth@test.com'
        user = Users.query.filter_by(email=email).first()
        if not user:
            user = Users(
                google_id='test-google-id-twelfth',
                email=email,
                name='Test User Twelfth',
                profile_picture='test-pic-twelfth.jpg',
                last_login=db.func.now(),
                email_verified=True
            )
            db.session.add(user)
            db.session.commit()
        
        token, _ = generate_access_token(user.id)
        return {'Authorization': f'Bearer {token}'}

def test_multiple_accounts_alternating_calls(client, auth_headers_basic, auth_headers_twelfth):
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
            headers=auth_headers_basic
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
            headers=auth_headers_twelfth
        )
        assert upload_response_twelfth.status_code == 200
        json_data = upload_response_twelfth.get_json()
        assert json_data['status'] == 'Success'

    # Optimize BasicData
    optimize_response_basic = client.post(
        '/optimize',
        headers=auth_headers_basic
    )
    assert optimize_response_basic.status_code == 200

    # Optimize TwelfthGradeData
    optimize_response_twelfth = client.post(
        '/optimize',
        headers=auth_headers_twelfth
    )
    assert optimize_response_twelfth.status_code == 200

    # Get unassigned courses for BasicData
    response_basic = client.get(
        '/unassigned_courses',
        headers=auth_headers_basic
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
        headers=auth_headers_twelfth
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
