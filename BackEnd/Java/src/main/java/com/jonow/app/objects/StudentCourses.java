package com.jonow.app.objects;

public class StudentCourses {
    int studentId;
    int courseId;

    public StudentCourses(int studentId, int courseId) {
        this.studentId = studentId;
        this.courseId = courseId;
    }

    public Integer getStudent() {
        return studentId;
    }

    public Integer getCourse() {
        return courseId;
    }

}
