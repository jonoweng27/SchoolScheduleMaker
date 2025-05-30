-- Given Data

-- Admin login
CREATE TABLE Admins (
    admin_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    school_id INT REFERENCES Schools(school_id) ON DELETE CASCADE
);
-- Create Students table
CREATE TABLE Students (
    student_id SERIAL PRIMARY KEY,  -- Auto-incrementing ID for each student
    first_name VARCHAR(255) NOT NULL,  -- Student's first name
    last_name VARCHAR(255) NOT NULL  -- Student's last name
    school_id INT REFERENCES Schools(school_id) ON DELETE CASCADE; -- Foreign key reference to Schools
);

-- Create Courses table
CREATE TABLE Courses (
    course_id SERIAL PRIMARY KEY,  -- Auto-incrementing ID for each course
    course_name VARCHAR(255) NOT NULL  -- Name of the course
    num_periods_in_week INTEGER NOT NULL -- Number of periods in a week for the course
    school_id INT REFERENCES Schools(school_id) ON DELETE CASCADE; -- Foreign key reference to Schools
);

-- Create Teachers table
CREATE TABLE Teachers (
    teacher_id SERIAL PRIMARY KEY,  -- Auto-incrementing ID for each teacher
    first_name VARCHAR(255) NOT NULL,  -- Teacher's first name
    last_name VARCHAR(255) NOT NULL  -- Teacher's last name
    school_id INT REFERENCES Schools(school_id) ON DELETE CASCADE;
);

-- Create Period table with start and end times for each day (M-F)
CREATE TABLE Period (
    period_id INT PRIMARY KEY,  -- Manually defined ID for each period
    start_time_monday TIME,  -- Start time for Monday
    end_time_monday TIME,  -- End time for Monday
    start_time_tuesday TIME,  -- Start time for Tuesday
    end_time_tuesday TIME,  -- End time for Tuesday
    start_time_wednesday TIME,  -- Start time for Wednesday
    end_time_wednesday TIME,  -- End time for Wednesday
    start_time_thursday TIME,  -- Start time for Thursday
    end_time_thursday TIME,  -- End time for Thursday
    start_time_friday TIME,  -- Start time for Friday
    end_time_friday TIME  -- End time for Friday
    ADD COLUMN school_id INT REFERENCES Schools(school_id) ON DELETE CASCADE;
);

-- Create Class Schedule table without room
CREATE TABLE ClassSchedule (
    schedule_id SERIAL PRIMARY KEY,  -- Auto-incrementing ID for each class schedule
    section_number INT NOT NULL,  -- Section number for the class
    course_id INT REFERENCES Courses(course_id),  -- Foreign key reference to Courses
    teacher_id INT REFERENCES Teachers(teacher_id),  -- Foreign key reference to Teachers
    class_capacity INT NOT NULL  -- Maximum number of students (class cap)
    school_id INT REFERENCES Schools(school_id) ON DELETE CASCADE;
);

-- Create join table for Students and Courses (many-to-many relationship)
CREATE TABLE StudentCourses (
    student_id INT REFERENCES Students(student_id) ON DELETE CASCADE,  -- Foreign key to Students
    course_id INT REFERENCES Courses(course_id) ON DELETE CASCADE,  -- Foreign key to Courses
    PRIMARY KEY (student_id, course_id)  -- Composite primary key to ensure uniqueness
);

-- Create a join table to link ClassSchedule and Periods for each day of the week with room number
CREATE TABLE ClassSchedulePeriods (
    schedule_id INT REFERENCES ClassSchedule(schedule_id) ON DELETE CASCADE,  -- Foreign key to ClassSchedule
    period_id INT REFERENCES Period(period_id) ON DELETE CASCADE,  -- Foreign key to Period
    day_of_week INT NOT NULL,  -- Represents the day of the week (1 = Monday, 2 = Tuesday, ..., 5 = Friday)
    room INT NOT NULL,  -- Room number for the class during this period
    PRIMARY KEY (schedule_id, period_id, day_of_week)  -- Composite primary key to ensure uniqueness
);

-- Data to be retrieved

-- Create Student_Schedules table
CREATE TABLE Student_Schedules (
    student_schedule_id SERIAL PRIMARY KEY,  -- Auto-incrementing ID for each student schedule
    student_id INT REFERENCES Students(student_id) ON DELETE CASCADE,  -- Foreign key reference to Students
    schedule_id INT REFERENCES ClassSchedule(schedule_id) ON DELETE CASCADE  -- Foreign key reference to ClassSchedule
);
