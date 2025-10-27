from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column('ID', db.Integer, primary_key=True)
    google_id = db.Column('Google ID', db.String(255), unique=True, nullable=False)
    email = db.Column('Email', db.String(255), unique=True, nullable=False) 
    name = db.Column('Name', db.String(255))
    profile_picture = db.Column('Profile Picture', db.Text)
    created_at = db.Column('Created At', db.DateTime, server_default=db.func.now())
    last_login = db.Column('Last Login', db.DateTime)
    email_verified = db.Column('Email Verified', db.Boolean, default=False)

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