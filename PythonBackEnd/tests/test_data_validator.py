import pandas as pd
import pytest
from data_validation.schedule_data_validator import ScheduleDataValidator
import os

@pytest.fixture
def validator():
    return ScheduleDataValidator()

@pytest.fixture
def students_df():
    path = os.path.join(os.path.dirname(__file__), "data", "BasicData", "Students.csv")
    return pd.read_csv(path)

@pytest.fixture
def schedules_df():
    path = os.path.join(os.path.dirname(__file__), "data", "BasicData", "Schedules.csv")
    return pd.read_csv(path)

@pytest.fixture
def periods_df():
    path = os.path.join(os.path.dirname(__file__), "data", "BasicData", "Periods.csv")
    return pd.read_csv(path)

def test_valid_data(validator, students_df, schedules_df, periods_df):
    valid, errors = validator.validate(students_df.copy(), schedules_df.copy(), periods_df.copy())
    assert valid
    assert errors == []

def test_missing_column(validator, students_df, schedules_df, periods_df):
    df = students_df.copy().drop(columns=["Course Name"])
    valid, errors = validator.validate(df, schedules_df, periods_df)
    assert not valid
    assert any("missing columns" in e for e in errors)

def test_null_values(validator, students_df, schedules_df, periods_df):
    df = students_df.copy()
    df.loc[0, "Course Name"] = None
    valid, errors = validator.validate(df, schedules_df, periods_df)
    assert not valid
    assert any("null values" in e for e in errors)

def test_non_integer_section(validator, students_df, schedules_df, periods_df):
    df = schedules_df.copy()
    df.loc[0, "Section"] = "A"
    valid, errors = validator.validate(students_df, df, periods_df)
    assert not valid
    assert any("must be integers" in e for e in errors)

def test_invalid_day(validator, students_df, schedules_df, periods_df):
    df = periods_df.copy()
    df.loc[0, "Day of Week"] = "Funday"
    valid, errors = validator.validate(students_df, schedules_df, df)
    assert not valid
    assert any("invalid days" in e for e in errors)

def test_referential_integrity_students(validator, students_df, schedules_df, periods_df):
    df = students_df.copy()
    df.loc[0, "Course Name"] = "Nonexistent Course"
    valid, errors = validator.validate(df, schedules_df, periods_df)
    assert not valid
    assert any("references unknown courses" in e for e in errors)

def test_referential_integrity_periods(validator, students_df, schedules_df, periods_df):
    df = periods_df.copy()
    df.loc[0, "Section"] = 999
    valid, errors = validator.validate(students_df, schedules_df, df)
    assert not valid
    assert any("references unknown course-section pairs" in e for e in errors)

def test_duplicate_students(validator, students_df, schedules_df, periods_df):
    df = pd.concat([students_df, students_df.iloc[[0]]], ignore_index=True)
    valid, errors = validator.validate(df, schedules_df, periods_df)
    assert not valid
    assert any("duplicate entry for" in e and "Students data" in e for e in errors)

def test_duplicate_schedules(validator, students_df, schedules_df, periods_df):
    df = pd.concat([schedules_df, schedules_df.iloc[[0]]], ignore_index=True)
    valid, errors = validator.validate(students_df, df, periods_df)
    assert not valid
    assert any("duplicate entry for" in e and "Schedules data" in e for e in errors)

def test_duplicate_periods(validator, students_df, schedules_df, periods_df):
    df = pd.concat([periods_df, periods_df.iloc[[0]]], ignore_index=True)
    valid, errors = validator.validate(students_df, schedules_df, df)
    assert not valid
    assert any("duplicate entry for" in e and "Periods data" in e for e in errors)

def test_non_positive_capacity(validator, students_df, schedules_df, periods_df):
    df = schedules_df.copy()
    df.loc[0, "Capacity"] = -1
    valid, errors = validator.validate(students_df, df, periods_df)
    assert not valid
    assert any("non-positive values in 'Capacity'" in e for e in errors)

def test_invalid_period_number(validator, students_df, schedules_df, periods_df):
    df = periods_df.copy()
    df.loc[0, "Period Number"] = 99
    valid, errors = validator.validate(students_df, schedules_df, df)
    assert not valid
    assert any("outside valid range" in e for e in errors)

def test_empty_students(validator, students_df, schedules_df, periods_df):
    df = students_df.iloc[0:0]
    valid, errors = validator.validate(df, schedules_df, periods_df)
    assert not valid
    assert any("Students data is empty" in e for e in errors)

def test_empty_schedules(validator, students_df, schedules_df, periods_df):
    df = schedules_df.iloc[0:0]
    valid, errors = validator.validate(students_df, df, periods_df)
    assert not valid
    assert any("Schedules data is empty" in e for e in errors)

def test_empty_periods(validator, students_df, schedules_df, periods_df):
    df = periods_df.iloc[0:0]
    valid, errors = validator.validate(students_df, schedules_df, df)
    assert not valid
    assert any("Periods data is empty" in e for e in errors)

    
def test_multiple_issues(validator, students_df, schedules_df, periods_df):
    # Introduce multiple issues:
    # 1. Remove a required column from students_df
    students_broken = students_df.copy().drop(columns=["Course Name"])
    # 2. Set a non-integer section in schedules_df
    schedules_broken = schedules_df.copy()
    schedules_broken.loc[0, "Section"] = "A"
    # 3. Set an invalid day in periods_df
    periods_broken = periods_df.copy()
    periods_broken.loc[0, "Day of Week"] = "Funday"
    # Validate
    valid, errors = validator.validate(students_broken, schedules_broken, periods_broken)
    assert not valid
    assert any("missing columns" in e for e in errors)
