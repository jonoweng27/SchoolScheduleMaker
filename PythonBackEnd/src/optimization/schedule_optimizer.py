import pandas as pd
from pyomo.environ import *

class ScheduleOptimizer:
    
    # -- Initialize the optimizer with necessary data structures
    def __init__(self):
        self.model = None
        self.section_to_times = None
        self.course_to_sections = None
        self.section_periods = None
        self.student_requests = None
        self.students_df = None
        self.schedules_df = None
        self.periods_df = None

    def run_solver(self, students_df, schedules_df, periods_df):
        # Store dataframes for later use
        self.students_df = students_df
        self.schedules_df = schedules_df
        self.periods_df = periods_df

        # Build helper structures
        self.build_lookups(periods_df, schedules_df)

        # Initialize and solve the model
        self.model = self.initialize_model()
        self.solve_model()
    
    # Build all the lookups
    def build_lookups(self, periods_df, schedules_df):
        # Build section to times mapping
        def build_section_to_times(periods_df):
            section_to_times = {}
            for _, row in periods_df.iterrows():
                key = (row["Course Name"], row["Section"])
                section_to_times.setdefault(key, set()).add((row["Day of Week"], row["Period Number"]))
            return section_to_times

        # Build course to sections mapping
        def build_course_to_sections(schedules_df):
            course_to_sections = schedules_df.groupby("Course Name")["Section"].apply(set).to_dict()
            course_to_sections = {c: {(c, s) for s in sections} for c, sections in course_to_sections.items()}
            return course_to_sections

        # Build section periods set
        def build_section_periods(periods_df):
            return {(row['Course Name'], row['Section'], row['Day of Week'], row['Period Number']) for _, row in periods_df.iterrows()}

        # Build student requests mapping
        def build_student_requests(students_df):
            return students_df.groupby("Student Name")["Course Name"].apply(set).to_dict()

        self.section_to_times = build_section_to_times(periods_df)
        self.course_to_sections = build_course_to_sections(schedules_df)
        self.section_periods = build_section_periods(periods_df)
        self.student_requests = build_student_requests(self.students_df)

    # Model initialization and solving
    def initialize_model(self):
        students_df = self.students_df
        schedules_df = self.schedules_df
        periods_df = self.periods_df
        course_to_sections = self.course_to_sections
        section_periods = self.section_periods
        student_requests = self.student_requests

        model = ConcreteModel()

        # Sets
        model.Students = Set(initialize=students_df["Student Name"].unique())
        model.Courses = Set(initialize=schedules_df["Course Name"].unique())
        model.Sections = Set(initialize=[(row["Course Name"], row["Section"]) for _, row in schedules_df.iterrows()])

        section_to_course = {(row["Course Name"], row["Section"]): row["Course Name"] for _, row in schedules_df.iterrows()}
        model.SectionToCourse = Param(model.Sections, initialize=section_to_course)

        section_to_capacity = {(row["Course Name"], row["Section"]): row["Capacity"] for _, row in schedules_df.iterrows()}
        model.SectionCapacity = Param(model.Sections, initialize=section_to_capacity)

        model.SectionPeriods = Set(dimen=4, initialize=section_periods)
        model.StudentCourseRequests = Param(model.Students, within=Any, initialize=lambda model, s: student_requests.get(s, set()))

        # Section size variable
        model.SectionSize = Var(model.Sections, domain=NonNegativeIntegers)
        # Number of unassigned courses per student
        model.UnassignedCourses = Var(model.Students, domain=NonNegativeIntegers)
        # x[s, (c, sec)] = 1 if student s is assigned to (Course Name, Section)
        model.x = Var(model.Students, model.Sections, domain=Binary)

        # Encourage even section sizes
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
        model.NoTimeConflicts = Constraint(
            model.Students,
            periods_df["Day of Week"].unique(),
            periods_df["Period Number"].unique(),
            rule=no_time_conflicts
        )

        # Section size constraint: total number of students in a section must equal the SectionSize variable
        def section_size_rule(model, c, sec_num):
            return model.SectionSize[(c, sec_num)] == sum(model.x[s, (c, sec_num)] for s in model.Students)
        model.SectionSizeConstraint = Constraint(model.Sections, rule=section_size_rule)


        # Constraint: Link UnassignedCourses to assignments
        def unassigned_courses_rule(model, s):
            requested = student_requests.get(s, set())
            assigned = sum(
                model.x[s, sec]
                for c in requested
                for sec in course_to_sections.get(c, set())
                if sec in model.Sections
            )
            return model.UnassignedCourses[s] == len(requested) - assigned
        model.UnassignedCoursesConstraint = Constraint(model.Students, rule=unassigned_courses_rule)

        # Variables for min and max unassigned
        model.MinUnassigned = Var(domain=NonNegativeIntegers)
        model.MaxUnassigned = Var(domain=NonNegativeIntegers)

        # Constraints for min/max
        def min_unassigned_rule(model, s):
            return model.MinUnassigned <= model.UnassignedCourses[s]
        model.MinUnassignedConstraint = Constraint(model.Students, rule=min_unassigned_rule)

        def max_unassigned_rule(model, s):
            return model.MaxUnassigned >= model.UnassignedCourses[s]
        model.MaxUnassignedConstraint = Constraint(model.Students, rule=max_unassigned_rule)

        # --- Objective ---
        # Maximize number of assigned student-course pairs
        alpha = .1
        beta = .1
        model.obj = Objective(
            expr=sum(model.x[s, sec] for s in model.Students for sec in model.Sections)
                - alpha * sum(model.SectionDeviation[sec] for sec in model.Sections)
                - beta * (model.MaxUnassigned - model.MinUnassigned),
            sense=maximize
        )

        return model

    def solve_model(self):
        solver = SolverFactory('cbc')
        # Set a time limit of 10 seconds (CBC uses 'seconds' option)
        solver.options['seconds'] = 10
        result = solver.solve(self.model, tee=False)
        # Note: If the solver stops early, it will return the best feasible solution found so far.
        return result

    # --- Output assigned students ---
    def get_assigned_courses(self):
        assigned = [
            (s, sec[0], sec[1])
            for s in self.model.Students
            for sec in self.model.Sections
            if value(self.model.x[s, sec]) == 1
        ]
        return pd.DataFrame(assigned, columns=["Student Name", "Course Name", "Section"])

    # --- Output unassigned requested courses per student ---
    def get_unassigned_courses(self):
        unassigned = []
        model = self.model
        for s in model.Students:
            requested_courses = self.student_requests.get(s, set())
            for c in requested_courses:
                assigned_sections = [sec for sec in self.course_to_sections.get(c, set()) if value(model.x[s, sec]) == 1]
                if not assigned_sections:
                    sections = self.course_to_sections.get(c, set())
                    could_take_if_no_capacity = False
                    for sec in sections:
                        times = self.section_to_times.get(sec, set())
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
                    has_capacity = any(value(model.SectionSize[sec]) < model.SectionCapacity[sec] for sec in sections)
                    if not has_capacity:
                        reason = "Capacity"
                    elif not could_take_if_no_capacity:
                        reason = "Time Conflict"
                    else:
                        reason = "Unknown"
                    unassigned.append((s, c, reason))
        return pd.DataFrame(unassigned, columns=["Student Name", "Unassigned Course", "Reason"])

    # --- Output class rosters for a given course and section ---
    def get_class_roster(self, course, section):
        model = self.model
        sec_key = (course, section)
        if sec_key not in model.Sections:
            return pd.DataFrame(columns=["Student Name"])
        members = [s for s in model.Students if value(model.x[s, sec_key]) == 1]
        return pd.DataFrame({"Student Name": members})

    # --- Output class rosters for all sections ---
    def get_all_class_rosters(self):
        rosters = {}
        for sec in self.model.Sections:
            course, section = sec
            df = self.get_class_roster(course, section)
            if not df.empty:
                rosters[sec] = df
        return rosters
    
    # --- Output an individual student schedule ---
    def get_student_schedule(self, student):
        model = self.model
        days = list(self.periods_df["Day of Week"].unique())
        periods = sorted(self.periods_df["Period Number"].unique())
        schedule = {p: {d: "" for d in days} for p in periods}
        for sec in model.Sections:
            if value(model.x[student, sec]) == 1:
                times = self.section_to_times.get(sec, set())
                for d, p in times:
                    schedule[p][d] = f"{sec[0]}.{sec[1]}"
        df = pd.DataFrame(
            [[schedule[p][d] for d in days] for p in periods],
            index=periods,
            columns=days
        )
        df.index.name = "Period"
        return df

    # --- Output all student schedules ---
    def get_all_student_schedules(self):
        schedules = {}
        for s in self.model.Students:
            schedules[s] = self.get_student_schedule(s)
        return schedules