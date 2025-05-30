import pandas as pd
from pyomo.environ import *

import os

# --- Load CSV data ---
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Data', 'TwelfthGrade'))
courses_df = pd.read_csv(os.path.join(base_dir, "Courses.csv"))              # Course Name, Num Periods in Week
schedules_df = pd.read_csv(os.path.join(base_dir, "Schedules.csv"))          # Course Name, Section, Capacity
periods_df = pd.read_csv(os.path.join(base_dir, "Periods.csv"))              # Course Name, Section, Day of Week, Period Number
students_df = pd.read_csv(os.path.join(base_dir, "Students.csv"))            # Student Name, Course Name

# --- Initialize model ---
model = ConcreteModel()

# --- Sets ---
model.Students = Set(initialize=students_df["Student Name"].unique())
model.Courses = Set(initialize=courses_df["Course Name"].unique())
model.Sections = Set(initialize=[(row["Course Name"], row["Section"]) for _, row in schedules_df.iterrows()])

# Map each (Course Name, Section) to its course (redundant, but for compatibility)
section_to_course = {(row["Course Name"], row["Section"]): row["Course Name"] for _, row in schedules_df.iterrows()}
model.SectionToCourse = Param(model.Sections, initialize=section_to_course)

# Map each (Course Name, Section) to its capacity
section_to_capacity = {(row["Course Name"], row["Section"]): row["Capacity"] for _, row in schedules_df.iterrows()}
model.SectionCapacity = Param(model.Sections, initialize=section_to_capacity)

# --- Helper sets ---
# All (Course Name, Section) that correspond to a course
course_to_sections = schedules_df.groupby("Course Name")["Section"].apply(set).to_dict()
course_to_sections = {c: {(c, s) for s in sections} for c, sections in course_to_sections.items()}

# Map (Course Name, Section, Day of Week, Period Number) for each scheduled class
section_periods = {(row['Course Name'], row['Section'], row['Day of Week'], row['Period Number']) for _, row in periods_df.iterrows()}
model.SectionPeriods = Set(dimen=4, initialize=section_periods)

# Requested courses by student
student_requests = students_df.groupby("Student Name")["Course Name"].apply(set).to_dict()
model.StudentCourseRequests = Param(model.Students, within=Any, initialize=lambda model, s: student_requests.get(s, set()))

# --- Variables ---
# x[s, (c, sec)] = 1 if student s is assigned to (Course Name, Section)
model.x = Var(model.Students, model.Sections, domain=Binary)

# --- Constraints ---

# Each student can be assigned to at most one section of each requested course
def course_assignment_rule(model, s, c):
    sections = course_to_sections.get(c, set())
    valid_sections = [sec for sec in sections if sec in model.Sections]
    if not valid_sections:
        return Constraint.Skip
    return sum(model.x[s, sec] for sec in valid_sections) <= 1
model.AssignOneSectionPerCourse = Constraint(model.Students, model.Courses, rule=course_assignment_rule)

# A student can only be assigned to requested courses
def only_requested_courses(model, s, c, sec_num):
    course = model.SectionToCourse[(c, sec_num)]
    if course not in student_requests.get(s, set()):
        return model.x[s, (c, sec_num)] == 0
    return Constraint.Skip
model.OnlyRequestedCourses = Constraint(model.Students, model.Sections, rule=only_requested_courses)

# Capacity constraint: number of students in a class cannot exceed capacity
def capacity_rule(model, c, sec_num):
    return sum(model.x[s, (c, sec_num)] for s in model.Students) <= model.SectionCapacity[(c, sec_num)]
model.CapacityConstraint = Constraint(model.Sections, rule=capacity_rule)

# No time conflicts for any student (can't take two classes at same time)
def no_time_conflicts(model, s, d, p):
    overlapping_sections = [sec for sec in model.Sections if (sec[0], sec[1], d, p) in model.SectionPeriods]
    if not overlapping_sections:
        return Constraint.Skip
    return sum(model.x[s, sec] for sec in overlapping_sections) <= 1
model.NoTimeConflicts = Constraint(model.Students, periods_df["Day of Week"].unique(), periods_df["Period Number"].unique(), rule=no_time_conflicts)

# --- Objective ---
# Maximize number of assigned student-course pairs
model.obj = Objective(expr=sum(model.x[s, sec] for s in model.Students for sec in model.Sections), sense=maximize)

# --- Solver ---
solver = SolverFactory('cbc')  # or 'glpk' or another MIP solver
result = solver.solve(model, tee=True)

# --- Output assigned students ---
assigned = [(s, sec[0], sec[1]) for s in model.Students for sec in model.Sections if value(model.x[s, sec]) == 1]
assigned_df = pd.DataFrame(assigned, columns=["Student Name", "Course Name", "Section"])
assigned_df.to_csv("drs_student_schedule_output.csv", index=False)

# --- Output unassigned requested courses per student ---
unassigned = []
for s in model.Students:
    requested_courses = student_requests.get(s, set())
    for c in requested_courses:
        assigned_sections = [sec for sec in course_to_sections.get(c, set()) if value(model.x[s, sec]) == 1]
        if not assigned_sections:
            unassigned.append((s, c))
unassigned_df = pd.DataFrame(unassigned, columns=["Student Name", "Unassigned Course"])
unassigned_df.to_csv("drs_student_unassigned_courses.csv", index=False)