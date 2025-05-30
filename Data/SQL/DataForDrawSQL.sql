CREATE TABLE Schools (
    school_id INT PRIMARY KEY,
    school_name VARCHAR(255) NOT NULL
);

CREATE TABLE Admins (
    admin_id INT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    school_id INT,
    FOREIGN KEY (school_id) REFERENCES Schools(school_id) ON DELETE CASCADE
);

CREATE TABLE Students (
    student_id INT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    school_id INT,
    FOREIGN KEY (school_id) REFERENCES Schools(school_id) ON DELETE CASCADE
);

CREATE TABLE Courses (
    course_id INT PRIMARY KEY,
    course_name VARCHAR(255) NOT NULL,
    num_periods_in_week INT NOT NULL,
    school_id INT,
    FOREIGN KEY (school_id) REFERENCES Schools(school_id) ON DELETE CASCADE
);

CREATE TABLE Teachers (
    teacher_id INT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    school_id INT,
    FOREIGN KEY (school_id) REFERENCES Schools(school_id) ON DELETE CASCADE
);

CREATE TABLE Periods (
    period_id INT PRIMARY KEY,
    start_time_monday TIME,
    end_time_monday TIME,
    start_time_tuesday TIME,
    end_time_tuesday TIME,
    start_time_wednesday TIME,
    end_time_wednesday TIME,
    start_time_thursday TIME,
    end_time_thursday TIME,
    start_time_friday TIME,
    end_time_friday TIME,
    school_id INT,
    FOREIGN KEY (school_id) REFERENCES Schools(school_id) ON DELETE CASCADE
);

CREATE TABLE ClassSchedule (
    schedule_id INT PRIMARY KEY,
    section_number INT NOT NULL,
    course_id INT,
    teacher_id INT,
    class_capacity INT NOT NULL,
    school_id INT,
    FOREIGN KEY (course_id) REFERENCES Courses(course_id),
    FOREIGN KEY (teacher_id) REFERENCES Teachers(teacher_id),
    FOREIGN KEY (school_id) REFERENCES Schools(school_id) ON DELETE CASCADE
);

CREATE TABLE StudentCourses (
    student_id INT,
    course_id INT,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES Students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES Courses(course_id) ON DELETE CASCADE
);

CREATE TABLE ClassSchedulePeriods (
    schedule_id INT,
    period_id INT,
    day_of_week INT NOT NULL,
    room INT NOT NULL,
    PRIMARY KEY (schedule_id, period_id, day_of_week),
    FOREIGN KEY (schedule_id) REFERENCES ClassSchedule(schedule_id) ON DELETE CASCADE,
    FOREIGN KEY (period_id) REFERENCES Periods(period_id) ON DELETE CASCADE
);

CREATE TABLE Student_Schedules (
    student_schedule_id INT PRIMARY KEY,
    student_id INT,
    schedule_id INT,
    FOREIGN KEY (student_id) REFERENCES Students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (schedule_id) REFERENCES ClassSchedule(schedule_id) ON DELETE CASCADE
);