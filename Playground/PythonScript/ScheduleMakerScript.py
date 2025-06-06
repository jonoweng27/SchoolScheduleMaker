import pandas as pd
from pyomo.environ import *

import os
import re

# --- Load CSV data ---
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Data', 'TwelfthGrade'))
students_df = pd.read_csv(os.path.join(base_dir, "Students.csv"))            # Student Name, Course Name
schedules_df = pd.read_csv(os.path.join(base_dir, "Schedules.csv"))          # Course Name, Section, Capacity
periods_df = pd.read_csv(os.path.join(base_dir, "Periods.csv"))              # Course Name, Section, Day of Week, Period Number


# --- Initialize model ---
model = ConcreteModel()

# --- Sets ---
model.Students = Set(initialize=students_df["Student Name"].unique())
model.Courses = Set(initialize=schedules_df["Course Name"].unique())
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

# Section size variable
model.SectionSize = Var(model.Sections, domain=NonNegativeIntegers)

# --- Variables ---
# x[s, (c, sec)] = 1 if student s is assigned to (Course Name, Section)
model.x = Var(model.Students, model.Sections, domain=Binary)


# --- Encourage even section sizes ---
model.SectionDeviation = Var(model.Sections, domain=NonNegativeReals)
model.DeviationConstraints = ConstraintList()
for c in model.Courses:
    sections = list(course_to_sections.get(c, set()))
    if not sections:
        continue
    avg = sum(model.SectionSize[sec] for sec in sections) / len(sections)
    for sec in sections:
        model.DeviationConstraints.add(model.SectionDeviation[sec] >= model.SectionSize[sec] - avg)
        model.DeviationConstraints.add(model.SectionDeviation[sec] >= avg - model.SectionSize[sec])


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

# Section size constraint: total number of students in a section must equal the SectionSize variable
def section_size_rule(model, c, sec_num):
    return model.SectionSize[(c, sec_num)] == sum(model.x[s, (c, sec_num)] for s in model.Students)
model.SectionSizeConstraint = Constraint(model.Sections, rule=section_size_rule)


# --- Objective ---
# Maximize number of assigned student-course pairs

alpha = .1  # Can be modified
model.obj = Objective(
    expr=sum(model.x[s, sec] for s in model.Students for sec in model.Sections)
        - alpha * sum(model.SectionDeviation[sec] for sec in model.Sections),
    sense=maximize
)

# --- Solver ---
solver = SolverFactory('cbc')  # or 'glpk' or another MIP solver
result = solver.solve(model, tee=True)

# --- Output assigned students ---
results_dir = os.path.join(base_dir, "Results", "Main")
os.makedirs(results_dir, exist_ok=True)

assigned = [(s, sec[0], sec[1]) for s in model.Students for sec in model.Sections if value(model.x[s, sec]) == 1]
assigned_df = pd.DataFrame(assigned, columns=["Student Name", "Course Name", "Section"])
assigned_df.to_csv(os.path.join(results_dir, "student_schedules.csv"), index=False)

days = list(periods_df["Day of Week"].unique())
periods = sorted(periods_df["Period Number"].unique())

# Build a lookup: (Course, Section) -> {(Day, Period)}
section_to_times = {}
for _, row in periods_df.iterrows():
    key = (row["Course Name"], row["Section"])
    section_to_times.setdefault(key, set()).add((row["Day of Week"], row["Period Number"]))

# --- Output unassigned requested courses per student ---
unassigned = []
for s in model.Students:
    requested_courses = student_requests.get(s, set())
    for c in requested_courses:
        assigned_sections = [sec for sec in course_to_sections.get(c, set()) if value(model.x[s, sec]) == 1]
        if not assigned_sections:
            sections = course_to_sections.get(c, set())
            # Check if student could take any section if there were infinite capacity
            could_take_if_no_capacity = False
            for sec in sections:
                times = section_to_times.get(sec, set())
                has_conflict = False
                for d, p in times:
                    for other_sec in model.Sections:
                        if other_sec == sec:
                            continue
                        if (other_sec[0], other_sec[1], d, p) in model.SectionPeriods:
                            if value(model.x[s, other_sec]) == 1:
                                has_conflict = True
                                break
                    if has_conflict:
                        break
                if not has_conflict:
                    could_take_if_no_capacity = True
                    break
            # Now check if any section has available capacity
            has_capacity = any(value(model.SectionSize[sec]) < model.SectionCapacity[sec] for sec in sections)
            if not has_capacity:
                reason = "Capacity"
            elif not could_take_if_no_capacity:
                reason = "Time Conflict"
            else:
                reason = "Unknown"
            unassigned.append((s, c, reason))
unassigned_df = pd.DataFrame(unassigned, columns=["Student Name", "Unassigned Course", "Reason"])
unassigned_df.to_csv(os.path.join(results_dir, "unassigned_courses.csv"), index=False)

# --- Output class rosters per section as separate CSVs ---

output_dir = os.path.join(base_dir, "Results", "Class_Rosters")
os.makedirs(output_dir, exist_ok=True)

for sec in model.Sections:
    members = [s for s in model.Students if value(model.x[s, sec]) == 1]
    if members:
        course_name = str(sec[0])
        section_num = str(sec[1])
        # Sanitize filename
        safe_course = re.sub(r'[^A-Za-z0-9_\-]', '_', course_name)
        filename = f"{safe_course}_{section_num}.csv"
        df = pd.DataFrame({"Student Name": members})
        df.to_csv(os.path.join(output_dir, filename), index=False)

# --- Output individual student schedules as CSVs ---
student_output_dir = os.path.join(base_dir, "Results", "Student_Schedules")
os.makedirs(student_output_dir, exist_ok=True)

for s in model.Students:
    # Build a schedule grid: period -> day -> class.section or ""
    schedule = {p: {d: "" for d in days} for p in periods}
    for sec in model.Sections:
        if value(model.x[s, sec]) == 1:
            times = section_to_times.get(sec, set())
            for d, p in times:
                schedule[p][d] = f"{sec[0]}.{sec[1]}"
    # Create DataFrame: rows=periods, columns=days (with day names)
    df = pd.DataFrame(
        [[schedule[p][d] for d in days] for p in periods],
        index=periods,
        columns=days
    )
    df.index.name = "Period"
    safe_name = re.sub(r'[^A-Za-z0-9_\-]', '_', str(s))
    df.to_csv(os.path.join(student_output_dir, f"{safe_name}.csv"))
