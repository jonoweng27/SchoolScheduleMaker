package com.jonow.app.objects;

public class Course {
    private int courseId;
    private String courseName;
    private int numPeriodsInWeek;

    public Course(int courseId, String courseName, int numPeriodsInWeek) {
        this.courseId = courseId;
        this.courseName = courseName;
        this.numPeriodsInWeek = numPeriodsInWeek;
    }

    public Integer getCourseId() {
        return courseId;
    }

    public void setCourseId(int courseId) {
        this.courseId = courseId;
    }

    public String getCourseName() {
        return courseName;
    }

    public void setCourseName(String courseName) {
        this.courseName = courseName;
    }

    public int getNumPeriodsInWeek() {
        return numPeriodsInWeek;
    }

    public void setNumPeriodsInWeek(int numPeriodsInWeek) {
        this.numPeriodsInWeek = numPeriodsInWeek;
    }
}
