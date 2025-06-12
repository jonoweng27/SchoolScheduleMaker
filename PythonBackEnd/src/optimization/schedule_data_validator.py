import pandas as pd

class ScheduleDataValidator:
    VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}

    def __init__(self):
        self.errors = []

    def validate(self, students_df, schedules_df, periods_df):
        self.errors.clear()
        self._validate_students(students_df)
        self._validate_schedules(schedules_df)
        self._validate_periods(periods_df)
        self._check_referential_integrity(students_df, schedules_df, periods_df)
        self._check_duplicates(students_df, schedules_df, periods_df)
        self._check_capacity(schedules_df)
        self._check_period_number(periods_df)
        self._check_empty(students_df, schedules_df, periods_df)
        return len(self.errors) == 0, self.errors

    def _validate_students(self, df):
        required_columns = {"Student Name", "Course Name"}
        self._check_columns(df, required_columns, "Students")
        self._check_nulls(df, required_columns, "Students")

    def _validate_schedules(self, df):
        required_columns = {"Course Name", "Section", "Capacity"}
        self._check_columns(df, required_columns, "Schedules")
        self._check_nulls(df, required_columns, "Schedules")
        self._check_int(df, ["Section", "Capacity"], "Schedules")

    def _validate_periods(self, df):
        required_columns = {"Course Name", "Section", "Day of Week", "Period Number"}
        self._check_columns(df, required_columns, "Periods")
        self._check_nulls(df, required_columns, "Periods")
        self._check_int(df, ["Section", "Period Number"], "Periods")
        self._check_days(df, "Day of Week", "Periods")

    # Check if any required columns are missing
    def _check_columns(self, df, required, name):
        missing = required - set(df.columns)
        if missing:
            self.errors.append(f"{name} data missing columns: {', '.join(missing)}")

    # Check if any columns have null values
    def _check_nulls(self, df, columns, name):
        for col in columns:
            if col in df.columns and df[col].isnull().any():
                self.errors.append(f"{name} data has null values in column: {col}")

    # Check if the required columns have only integers
    def _check_int(self, df, columns, name):
        for col in columns:
            if col in df.columns and not pd.api.types.is_integer_dtype(df[col]):
                try:
                    df[col] = df[col].astype(int)
                except Exception:
                    self.errors.append(f"{name} data column '{col}' must be integers.")

    # Check if the 'Day of Week' column contains valid days
    def _check_days(self, df, col, name):
        if col in df.columns:
            invalid = set(df[col].unique()) - self.VALID_DAYS
            if invalid:
                self.errors.append(f"{name} data has invalid days: {', '.join(map(str, invalid))}")

    # Check referential integrity between students, schedules, and periods
    def _check_referential_integrity(self, students_df, schedules_df, periods_df):
        # Students' courses exist in schedules
        if "Course Name" in students_df.columns and "Course Name" in schedules_df.columns:
            valid_courses = set(schedules_df["Course Name"])
            invalid_courses = set(students_df["Course Name"]) - valid_courses
            if invalid_courses:
                self.errors.append(f"Students data references unknown courses: {', '.join(map(str, invalid_courses))}")

        # Periods' (Course Name, Section) exist in schedules
        if {"Course Name", "Section"}.issubset(schedules_df.columns) and {"Course Name", "Section"}.issubset(periods_df.columns):
            schedule_keys = set(zip(schedules_df["Course Name"], schedules_df["Section"]))
            period_keys = set(zip(periods_df["Course Name"], periods_df["Section"]))
            invalid_periods = period_keys - schedule_keys
            if invalid_periods:
                self.errors.append(f"Periods data references unknown course-section pairs: {invalid_periods}")

    # Check for duplicates in students, schedules, and periods data
    def _check_duplicates(self, students_df, schedules_df, periods_df):
        # Students: no duplicate (Student Name, Course Name)
        if {"Student Name", "Course Name"}.issubset(students_df.columns):
            dup = students_df.duplicated(subset=["Student Name", "Course Name"])
            if dup.any():
                self.errors.append("Students data has duplicate (Student Name, Course Name) entries.")

        # Schedules: unique (Course Name, Section)
        if {"Course Name", "Section"}.issubset(schedules_df.columns):
            dup = schedules_df.duplicated(subset=["Course Name", "Section"])
            if dup.any():
                self.errors.append("Schedules data has duplicate (Course Name, Section) entries.")

        # Periods: unique (Course Name, Section, Day of Week, Period Number)
        if {"Course Name", "Section", "Day of Week", "Period Number"}.issubset(periods_df.columns):
            dup = periods_df.duplicated(subset=["Course Name", "Section", "Day of Week", "Period Number"])
            if dup.any():
                self.errors.append("Periods data has duplicate (Course Name, Section, Day of Week, Period Number) entries.")

    # Check for non-positive capacity values in schedules
    def _check_capacity(self, schedules_df):
        if "Capacity" in schedules_df.columns:
            if (schedules_df["Capacity"] <= 0).any():
                self.errors.append("Schedules data has non-positive values in 'Capacity'.")

    # Check if 'Period Number' is within a valid range
    def _check_period_number(self, periods_df, min_period=1, max_period=20):
        if "Period Number" in periods_df.columns:
            invalid = periods_df[(periods_df["Period Number"] < min_period) | (periods_df["Period Number"] > max_period)]
            if not invalid.empty:
                self.errors.append(f"Periods data has 'Period Number' outside valid range ({min_period}-{max_period}).")
    
    # Check if any of the dataframes are empty
    def _check_empty(self, students_df, schedules_df, periods_df):
        if students_df.empty:
            self.errors.append("Students data is empty.")
        if schedules_df.empty:
            self.errors.append("Schedules data is empty.")
        if periods_df.empty:
            self.errors.append("Periods data is empty.")