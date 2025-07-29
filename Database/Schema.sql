-- Users table: stores Google SSO users
CREATE TABLE users (
    "ID" VARCHAR(128) PRIMARY KEY,         -- Google user ID
    "Email" VARCHAR(255) UNIQUE NOT NULL,
    "Name" VARCHAR(255),
    "Created At" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students table: stores uploaded student data per user
CREATE TABLE students (
    "ID" SERIAL PRIMARY KEY,
    "User ID" VARCHAR(128) REFERENCES users("ID") ON DELETE CASCADE,
    "Student Name" VARCHAR(255) NOT NULL,
    "Course Name" VARCHAR(255) NOT NULL
);

-- Schedules table: stores uploaded schedule data per user
CREATE TABLE schedules (
    "ID" SERIAL PRIMARY KEY,
    "User ID" VARCHAR(128) REFERENCES users("ID") ON DELETE CASCADE,
    "Course Name" VARCHAR(255) NOT NULL,
    "Section" INTEGER NOT NULL,
    "Capacity" INTEGER NOT NULL
);

-- Periods table: stores uploaded period data per user
CREATE TABLE periods (
    "ID" SERIAL PRIMARY KEY,
    "User ID" VARCHAR(128) REFERENCES users("ID") ON DELETE CASCADE,
    "Course Name" VARCHAR(255) NOT NULL,
    "Section" INTEGER NOT NULL,
    "Day of Week" VARCHAR(32) NOT NULL,
    "Period Number" INTEGER NOT NULL
);

-- Validation results table: stores validation status and errors per user
CREATE TABLE validation_results (
    "ID" SERIAL PRIMARY KEY,
    "User ID" VARCHAR(128) REFERENCES users("ID") ON DELETE CASCADE,
    "Valid" BOOLEAN NOT NULL,
    "Errors" JSONB,
    "Created At" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Student Schedules: assigned courses
CREATE TABLE assigned_courses (
    "ID" SERIAL PRIMARY KEY,
    "User ID" VARCHAR(128) REFERENCES users("ID") ON DELETE CASCADE,
    "Student Name" VARCHAR(255) NOT NULL,
    "Course Name" VARCHAR(255) NOT NULL,
    "Section" INTEGER NOT NULL
);

-- Unassigned Courses: courses a student requested but did not get, with reason
CREATE TABLE unassigned_courses (
    "ID" SERIAL PRIMARY KEY,
    "User ID" VARCHAR(128) REFERENCES users("ID") ON DELETE CASCADE,
    "Student Name" VARCHAR(255) NOT NULL,
    "Unassigned Course Name" VARCHAR(255) NOT NULL,
    "Reason" TEXT NOT NULL
);