-- Users table: stores username/password for authentication
CREATE TABLE users (
    "ID" SERIAL PRIMARY KEY,
    "Google ID" VARCHAR(255) UNIQUE NOT NULL,  -- Google's unique user ID
    "Email" VARCHAR(255) UNIQUE NOT NULL,
    "Name" VARCHAR(255),
    "Profile Picture" TEXT,  -- Optional: Google profile image URL
    "Created At" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "Last Login" TIMESTAMP,
    "Email Verified" BOOLEAN DEFAULT FALSE
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