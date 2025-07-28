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
    "Section" VARCHAR(64) NOT NULL,
    "Capacity" INTEGER NOT NULL
);

-- Periods table: stores uploaded period data per user
CREATE TABLE periods (
    "ID" SERIAL PRIMARY KEY,
    "User ID" VARCHAR(128) REFERENCES users("ID") ON DELETE CASCADE,
    "Course Name" VARCHAR(255) NOT NULL,
    "Section" VARCHAR(64) NOT NULL,
    "Day of Week" VARCHAR(32) NOT NULL,
    "Period Number" INTEGER NOT NULL
);

-- Optimization results table: stores results per user (optional)
CREATE TABLE optimization_results (
    "ID" SERIAL PRIMARY KEY,
    "User ID" VARCHAR(128) REFERENCES users("ID") ON DELETE CASCADE,
    "Assignments" JSONB NOT NULL,
    "Created At" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Validation results table: stores validation status and errors per user
CREATE TABLE validation_results (
    "ID" SERIAL PRIMARY KEY,
    "User ID" VARCHAR(128) REFERENCES users("ID") ON DELETE CASCADE,
    "Valid" BOOLEAN NOT NULL,
    "Errors" JSONB,
    "Created At" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);