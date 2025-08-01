-- Users table: stores username/password for authentication
CREATE TABLE users (
    "ID" SERIAL PRIMARY KEY,
    "Username" VARCHAR(64) UNIQUE NOT NULL,
    "Password Hash" VARCHAR(255) NOT NULL,
    "Email" VARCHAR(255),
    "Name" VARCHAR(255),
    "Created At" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students table: stores uploaded student data per user
CREATE TABLE students (
    "ID" SERIAL PRIMARY KEY,
    "User ID" INTEGER REFERENCES users("ID") ON DELETE CASCADE,
    "Student Name" VARCHAR(255) NOT NULL,
    "Course Name" VARCHAR(255) NOT NULL
);

-- Schedules table: stores uploaded schedule data per user
CREATE TABLE schedules (
    "ID" SERIAL PRIMARY KEY,
    "User ID" INTEGER REFERENCES users("ID") ON DELETE CASCADE,
    "Course Name" VARCHAR(255) NOT NULL,
    "Section" INTEGER NOT NULL,
    "Capacity" INTEGER NOT NULL
);

-- Periods table: stores uploaded period data per user
CREATE TABLE periods (
    "ID" SERIAL PRIMARY KEY,
    "User ID" INTEGER REFERENCES users("ID") ON DELETE CASCADE,
    "Course Name" VARCHAR(255) NOT NULL,
    "Section" INTEGER NOT NULL,
    "Day of Week" VARCHAR(32) NOT NULL,
    "Period Number" INTEGER NOT NULL
);

-- Student Schedules: assigned courses
CREATE TABLE assigned_courses (
    "ID" SERIAL PRIMARY KEY,
    "User ID" INTEGER REFERENCES users("ID") ON DELETE CASCADE,
    "Student Name" VARCHAR(255) NOT NULL,
    "Course Name" VARCHAR(255) NOT NULL,
    "Section" INTEGER NOT NULL
);

-- Unassigned Courses: courses a student requested but did not get, with reason
CREATE TABLE unassigned_courses (
    "ID" SERIAL PRIMARY KEY,
    "User ID" INTEGER REFERENCES users("ID") ON DELETE CASCADE,
    "Student Name" VARCHAR(255) NOT NULL,
    "Unassigned Course Name" VARCHAR(255) NOT NULL,
    "Reason" TEXT NOT NULL
);

-- Insert two users with fake data and password hash for "school"
-- Password hash generated using bcrypt for "school": $2y$05$OBbYmy9OOJmY.IwtbVRcp.KApaHr8NGYytU7aGNUlXh6P5lPPtsQS
INSERT INTO users ("Username", "Password Hash", "Email", "Name")
VALUES
    ('Basic Data', '$2y$05$OBbYmy9OOJmY.IwtbVRcp.KApaHr8NGYytU7aGNUlXh6P5lPPtsQS', 'basic@example.com', 'Basic Data User'),
    ('Twelfth Grade Data', '$2y$05$OBbYmy9OOJmY.IwtbVRcp.KApaHr8NGYytU7aGNUlXh6P5lPPtsQS', 'twelfth@example.com', 'Twelfth Grade Data User');