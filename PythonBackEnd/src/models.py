from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column('ID', db.Integer, primary_key=True)
    username = db.Column('Username', db.String(64), unique=True, nullable=False)
    password_hash = db.Column('Password Hash', db.String(255), nullable=False)
    email = db.Column('Email', db.String(255))
    name = db.Column('Name', db.String(255))
    created_at = db.Column('Created At', db.DateTime, server_default=db.func.now())

class Students(db.Model):
    __tablename__ = 'students'
    id = db.Column('ID', db.Integer, primary_key=True)
    user_id = db.Column('User ID', db.Integer, db.ForeignKey('users.ID', ondelete='CASCADE'), nullable=False)
    student_name = db.Column('Student Name', db.String(255), nullable=False)
    course_name = db.Column('Course Name', db.String(255), nullable=False)

class Schedules(db.Model):
    __tablename__ = 'schedules'
    id = db.Column('ID', db.Integer, primary_key=True)
    user_id = db.Column('User ID', db.Integer, db.ForeignKey('users.ID', ondelete='CASCADE'), nullable=False)
    course_name = db.Column('Course Name', db.String(255), nullable=False)
    section = db.Column('Section', db.Integer, nullable=False)
    capacity = db.Column('Capacity', db.Integer, nullable=False)

class Periods(db.Model):
    __tablename__ = 'periods'
    id = db.Column('ID', db.Integer, primary_key=True)
    user_id = db.Column('User ID', db.Integer, db.ForeignKey('users.ID', ondelete='CASCADE'), nullable=False)
    course_name = db.Column('Course Name', db.String(255), nullable=False)
    section = db.Column('Section', db.Integer, nullable=False)
    day_of_week = db.Column('Day of Week', db.String(32), nullable=False)
    period_number = db.Column('Period Number', db.Integer, nullable=False)

class ValidationResults(db.Model):
    __tablename__ = 'validation_results'
    id = db.Column('ID', db.Integer, primary_key=True)
    user_id = db.Column('User ID', db.Integer, db.ForeignKey('users.ID', ondelete='CASCADE'), nullable=False)
    valid = db.Column('Valid', db.Boolean, nullable=False)
    errors = db.Column('Errors', db.JSON, nullable=True)
    created_at = db.Column('Created At', db.DateTime, server_default=db.func.now())

class AssignedCourses(db.Model):
    __tablename__ = 'assigned_courses'
    id = db.Column('ID', db.Integer, primary_key=True)
    user_id = db.Column('User ID', db.Integer, db.ForeignKey('users.ID', ondelete='CASCADE'), nullable=False)
    student_name = db.Column('Student Name', db.String(255), nullable=False)
    course_name = db.Column('Course Name', db.String(255), nullable=False)
    section = db.Column('Section', db.Integer, nullable=False)

class UnassignedCourses(db.Model):
    __tablename__ = 'unassigned_courses'
    id = db.Column('ID', db.Integer, primary_key=True)
    user_id = db.Column('User ID', db.Integer, db.ForeignKey('users.ID', ondelete='CASCADE'), nullable=False)
    student_name = db.Column('Student Name', db.String(255), nullable=False)
    unassigned_course_name = db.Column('Unassigned Course Name', db.String(255), nullable=False)
    reason = db.Column('Reason', db.Text, nullable=False)