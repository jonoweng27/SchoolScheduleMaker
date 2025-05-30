-- Table: Courses
CREATE TABLE Courses (
    course_name VARCHAR PRIMARY KEY,
    num_periods_in_week INT NOT NULL
);

-- Table: Schedules
CREATE TABLE Schedules (
    course_name VARCHAR NOT NULL,
    section VARCHAR NOT NULL, -- e.g., 'A', 'B', etc.
    capacity INT NOT NULL,
    PRIMARY KEY (course_name, section),
    FOREIGN KEY (course_name) REFERENCES Courses(course_name)
);

-- Table: Periods
CREATE TABLE Periods (
    course_name VARCHAR NOT NULL,
    section VARCHAR NOT NULL,
    day_of_week VARCHAR NOT NULL, -- e.g., 'Monday', 'Tuesday', etc.
    period_num INT NOT NULL,
    PRIMARY KEY (course_name, section, day_of_week, period_num),
    FOREIGN KEY (course_name, section) REFERENCES Schedules(course_name, section)
);

-- Table: Students
CREATE TABLE Students (
    student_name VARCHAR NOT NULL,
    course_name VARCHAR NOT NULL,
    PRIMARY KEY (student_name, course_name),
    FOREIGN KEY (course_name) REFERENCES Courses(course_name)
);

-- Table: StudentSchedules (Output)
CREATE TABLE StudentSchedules (
    student_name VARCHAR NOT NULL,
    course_name VARCHAR NOT NULL,
    section VARCHAR NOT NULL,
    PRIMARY KEY (student_name, course_name),
    FOREIGN KEY (course_name, section) REFERENCES Schedules(course_name, section)
);

-- Table: UnassignedCourses (Output)
CREATE TABLE UnassignedCourses (
    student_name VARCHAR NOT NULL,
    course_name VARCHAR NOT NULL,
    PRIMARY KEY (student_name, course_name),
    FOREIGN KEY (course_name) REFERENCES Courses(course_name)
);
