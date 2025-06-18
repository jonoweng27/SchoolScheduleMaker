import pandas as pd

class ScheduleDataValidator:
    VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}

    def __init__(self):
        self.errors = []

    def validate(self, students_df, schedules_df, periods_df):
        self.errors.clear()  
        # List of validation steps in order
        # Group validation steps that can be done in parallel
        validation_steps = [
            lambda: [self._validate_students(students_df),
                 self._validate_schedules(schedules_df),
                 self._validate_periods(periods_df)],
            lambda: self._check_empty(students_df, schedules_df, periods_df),
            lambda: self._check_duplicates(students_df, schedules_df, periods_df),
            lambda: self._check_referential_integrity(students_df, schedules_df, periods_df),
            lambda: [self._check_capacity(schedules_df),
                 self._check_period_number(periods_df)],
        ]
        for step in validation_steps:
            if self.errors:
                return False, self.errors
            step()
        if self.errors:
            return False, self.errors
        return True, self.errors

    def _validate_students(self, df):
        required_columns = {"Student Name", "Course Name"}
        self._check_columns(df, required_columns, "Students")
        self._check_nulls(df, required_columns, "Students")

    def _validate_schedules(self, df):
        required_columns = {"Course Name", "Section", "Capacity"}
        self._check_columns(df, required_columns, "Schedules")
        self._check_nulls(df, required_columns, "Schedules")
        # Only check int if there are no nulls in the columns
        for col in ["Section", "Capacity"]:
            if col in df.columns and not df[col].isnull().any():
                self._check_int(df, [col], "Schedules")

    def _validate_periods(self, df):
        required_columns = {"Course Name", "Section", "Day of Week", "Period Number"}
        self._check_columns(df, required_columns, "Periods")
        self._check_nulls(df, required_columns, "Periods")
        # Only check int if there are no nulls in the columns
        for col in ["Section", "Period Number"]:
            if col in df.columns and not df[col].isnull().any():
                self._check_int(df, [col], "Periods")
        # Only check days if columns and nulls returned no errors
        if not self.errors:
            self._check_days(df, "Day of Week", "Periods")

    # Check if any required columns are missing
    def _check_columns(self, df, required, name):
        missing = required - set(df.columns)
        if missing:
            self.errors.append(f"{name} data missing columns: {', '.join(missing)}")

    # Check if any columns have null values and report the rows
    def _check_nulls(self, df, columns, name):
        for col in columns:
            if col in df.columns and df[col].isnull().any():
                null_rows = df[df[col].isnull()]
                row_indices = self._display_rows(null_rows.index.tolist())
                self.errors.append(
                    f"{name} data has null values in column: {col} (rows: {row_indices})"
                )

    # Check if the required columns have only integers
    def _check_int(self, df, columns, name):
        for col in columns:
            if col in df.columns:
                def is_int_like(x):
                    try:
                        return float(x).is_integer()
                    except:
                        return False

                invalid_mask = df[col].apply(lambda x: not is_int_like(x))
                invalid_rows = df.index[invalid_mask].tolist()
                if invalid_rows:
                    self.errors.append(
                        f"{name} data column '{col}' must contain integer-like values. Invalid rows: {self._display_rows(invalid_rows)}"
                    )


    # Check if the 'Day of Week' column contains valid days
    def _check_days(self, df, col, name):
        if col in df.columns:
            invalid_mask = ~df[col].isin(self.VALID_DAYS)
            if invalid_mask.any():
                invalid_days = set(df[col][invalid_mask].unique())
                invalid_rows = df.index[invalid_mask].tolist()
                self.errors.append(
                    f"{name} data has invalid days: {', '.join(map(str, invalid_days))} (rows: {self._display_rows(invalid_rows)})"
                )

    # Check referential integrity between students, schedules, and periods
    def _check_referential_integrity(self, students_df, schedules_df, periods_df):
        if "Course Name" in students_df.columns and "Course Name" in schedules_df.columns:
            valid_courses = set(schedules_df["Course Name"])
            invalid_courses = set(students_df["Course Name"]) - valid_courses
            if invalid_courses:
                invalid_rows = students_df[students_df["Course Name"].isin(invalid_courses)].index.tolist()
                self.errors.append(
                    f"Students data references unknown courses: {', '.join(map(str, invalid_courses))} (rows: {self._display_rows(invalid_rows)})"
                )
        if {"Course Name", "Section"}.issubset(schedules_df.columns) and {"Course Name", "Section"}.issubset(periods_df.columns):
            schedule_keys = set(zip(schedules_df["Course Name"], schedules_df["Section"]))
            period_keys = set(zip(periods_df["Course Name"], periods_df["Section"]))
            invalid_periods = period_keys - schedule_keys
            if invalid_periods:
                invalid_rows = periods_df[
                    periods_df.apply(
                        lambda row: (row["Course Name"], row["Section"]) in invalid_periods, axis=1
                    )
                ].index.tolist()
                self.errors.append(
                    f"Periods data references unknown course-section pairs: {invalid_periods} (rows: {self._display_rows(invalid_rows)})"
                )
        # Check if any course-section in schedules does not have a corresponding period (i.e., does not meet at all)
        if {"Course Name", "Section"}.issubset(schedules_df.columns) and {"Course Name", "Section"}.issubset(periods_df.columns):
            schedule_keys = set(zip(schedules_df["Course Name"], schedules_df["Section"]))
            period_keys = set(zip(periods_df["Course Name"], periods_df["Section"]))
            missing_periods = schedule_keys - period_keys
            if missing_periods:
                invalid_rows = schedules_df[
                    schedules_df.apply(
                        lambda row: (row["Course Name"], row["Section"]) in missing_periods, axis=1
                    )
                ].index.tolist()
                self.errors.append(
                    f"Schedules data has course-section(s) that do not meet at all: {missing_periods} (rows: {self._display_rows(invalid_rows)})"
                )

    # Check for duplicates in students, schedules, and periods data
    def _check_duplicates(self, students_df, schedules_df, periods_df):
        # Students: no duplicate (Student Name, Course Name)
        if {"Student Name", "Course Name"}.issubset(students_df.columns):
            dup_mask = students_df.duplicated(subset=["Student Name", "Course Name"], keep=False)
            if dup_mask.any():
                dup_groups = students_df[dup_mask].groupby(["Student Name", "Course Name"]).groups
                for key, indices in dup_groups.items():
                    self.errors.append(
                    f"Students data has duplicate entry for {key} at rows: {self._display_rows(list(indices))}"
                    )
        # Schedules: unique (Course Name, Section)
        if {"Course Name", "Section"}.issubset(schedules_df.columns):
            dup_mask = schedules_df.duplicated(subset=["Course Name", "Section"], keep=False)
            if dup_mask.any():
                dup_groups = schedules_df[dup_mask].groupby(["Course Name", "Section"]).groups
                for key, indices in dup_groups.items():
                    self.errors.append(
                    f"Schedules data has duplicate entry for {key} at rows: {self._display_rows(list(indices))}"
                    )
        # Periods: unique (Course Name, Section, Day of Week, Period Number)
        if {"Course Name", "Section", "Day of Week", "Period Number"}.issubset(periods_df.columns):
            dup_mask = periods_df.duplicated(subset=["Course Name", "Section", "Day of Week", "Period Number"], keep=False)
            if dup_mask.any():
                dup_groups = periods_df[dup_mask].groupby(
                    ["Course Name", "Section", "Day of Week", "Period Number"]
                ).groups
                for key, indices in dup_groups.items():
                    self.errors.append(
                    f"Periods data has duplicate entry for {key} at rows: {self._display_rows(list(indices))}"
                    )

    # Check for non-positive capacity values in schedules
    def _check_capacity(self, schedules_df):
        if "Capacity" in schedules_df.columns:
            if (schedules_df["Capacity"] <= 0).any():
                invalid_rows = schedules_df[schedules_df["Capacity"] <= 0].index.tolist()
                self.errors.append(f"Schedules data has non-positive values in 'Capacity' (rows: {self._display_rows(invalid_rows)}).")

    # Check if 'Period Number' is within a valid range
    def _check_period_number(self, periods_df, min_period=1, max_period=20):
        if "Period Number" in periods_df.columns:
            invalid = periods_df[(periods_df["Period Number"] < min_period) | (periods_df["Period Number"] > max_period)]
            if not invalid.empty:
                invalid_rows = invalid.index.tolist()
                self.errors.append(
                    f"Periods data has 'Period Number' outside valid range ({min_period}-{max_period}) (rows: {self._display_rows(invalid_rows)})."
                )
    
    # Check if any of the dataframes are empty
    def _check_empty(self, students_df, schedules_df, periods_df):
        if students_df.empty:
            self.errors.append("Students data is empty.")
        if schedules_df.empty:
            self.errors.append("Schedules data is empty.")
        if periods_df.empty:
            self.errors.append("Periods data is empty.")

    # Convert DataFrame index list to user-facing row numbers (header is row 1)
    def _display_rows(self, indices):
        return [i + 2 for i in indices]