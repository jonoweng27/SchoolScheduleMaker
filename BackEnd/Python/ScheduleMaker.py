import pandas as pd
from pyomo.environ import *

import os

# --- Load CSV data ---
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Data', 'BasicData'))
courses_df = pd.read_csv(os.path.join(base_dir, "Course.csv"))               # course_id, course_name, num_periods_in_week, school_id
schedule_df = pd.read_csv(os.path.join(base_dir, "ClassSchedule.csv"))       # schedule_id, section, course_id, teacher_id, capacity, school_id
periods_df = pd.read_csv(os.path.join(base_dir, "ClassSchedulePeriod.csv"))  # schedule_id, period_id, day_of_week
requests_df = pd.read_csv(os.path.join(base_dir, "StudentsCourses.csv"))     # student_id, course_id

# --- Initialize model ---
model = ConcreteModel()

# --- Sets ---
model.Students = Set(initialize=requests_df["Student"].unique())
model.Courses = Set(initialize=courses_df["Course ID"].unique())
model.Schedules = Set(initialize=schedule_df["Schedule ID"].unique())

# Map each schedule to its course
schedule_to_course = dict(zip(schedule_df["Schedule ID"], schedule_df["Course ID"]))
model.ScheduleToCourse = Param(model.Schedules, initialize=schedule_to_course)

# Map each schedule to its capacity
schedule_to_capacity = dict(zip(schedule_df["Schedule ID"], schedule_df["Class Capacity"]))
model.ScheduleCapacity = Param(model.Schedules, initialize=schedule_to_capacity)

# --- Helper sets ---
# All schedule_ids that correspond to a course
course_to_schedules = schedule_df.groupby("Course ID")["Schedule ID"].apply(set).to_dict()

# Map (schedule, day, period) for each scheduled class
schedule_periods = {(row['Schedule ID'], row['Day of Week'], row['Period ID']) for _, row in periods_df.iterrows()}
model.SchedulePeriods = Set(dimen=3, initialize=schedule_periods)

# Requested courses by student
student_requests = requests_df.groupby("Student")["Course Number"].apply(set).to_dict()
model.StudentCourseRequests = Param(model.Students, within=Any, initialize=lambda model, s: student_requests.get(s, set()))

# --- Variables ---
# x[s, sched] = 1 if student s is assigned to schedule_id `sched`
model.x = Var(model.Students, model.Schedules, domain=Binary)

# --- Constraints ---

# Each student can be assigned to at most one section of each requested course
def course_assignment_rule(model, s, c):
    scheds = course_to_schedules.get(c, [])
    valid_scheds = [sched for sched in scheds if sched in model.Schedules]
    if not valid_scheds:
        return Constraint.Skip  # Nothing to constrain
    return sum(model.x[s, sched] for sched in valid_scheds) <= 1
model.AssignOneSectionPerCourse = Constraint(model.Students, model.Courses, rule=course_assignment_rule)

# A student can only be assigned to requested courses
def only_requested_courses(model, s, sched):
    course = model.ScheduleToCourse[sched]
    if course not in student_requests.get(s, set()):
        return model.x[s, sched] == 0
    return Constraint.Skip
model.OnlyRequestedCourses = Constraint(model.Students, model.Schedules, rule=only_requested_courses)

# Capacity constraint: number of students in a class cannot exceed capacity
def capacity_rule(model, sched):
    return sum(model.x[s, sched] for s in model.Students) <= model.ScheduleCapacity[sched]
model.CapacityConstraint = Constraint(model.Schedules, rule=capacity_rule)

# No time conflicts for any student (can't take two classes at same time)
def no_time_conflicts(model, s, d, p):
    overlapping_schedules = [sched for sched in model.Schedules if (sched, d, p) in model.SchedulePeriods]
    if not overlapping_schedules:
        return Constraint.Skip
    return sum(model.x[s, sched] for sched in overlapping_schedules) <= 1
model.NoTimeConflicts = Constraint(model.Students, range(1, 6), range(1, 15), rule=no_time_conflicts)

# --- Objective ---
# Maximize number of assigned student-course pairs
model.obj = Objective(expr=sum(model.x[s, sched] for s in model.Students for sched in model.Schedules), sense=maximize)

# --- Solver ---
solver = SolverFactory('cbc')  # or 'glpk' or another MIP solver
result = solver.solve(model, tee=True)

# --- Output assigned students ---
assigned = [(s, sched) for s in model.Students for sched in model.Schedules if value(model.x[s, sched]) == 1]
assigned_df = pd.DataFrame(assigned, columns=["Student", "Schedule ID"])
assigned_df.to_csv("student_schedule_output.csv", index=False)
