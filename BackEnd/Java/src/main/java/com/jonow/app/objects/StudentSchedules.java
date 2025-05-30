package com.jonow.app.objects;

public class StudentSchedules {

    private int studentScheduleId;
    private int studentId;
    private int scheduleId;

    public StudentSchedules(int studentScheduleId, int studentId, int scheduleId) {
        this.studentScheduleId = studentScheduleId;
        this.studentId = studentId;
        this.scheduleId = scheduleId;
    }

    // Getters and Setters
    public int getStudentScheduleId() {
        return studentScheduleId;
    }

    public void setStudentScheduleId(int studentScheduleId) {
        this.studentScheduleId = studentScheduleId;
    }

    public Integer getStudentId() {
        return studentId;
    }

    public void setStudentId(int studentId) {
        this.studentId = studentId;
    }

    public Integer getScheduleId() {
        return scheduleId;
    }

    public void setScheduleId(int scheduleId) {
        this.scheduleId = scheduleId;
    }

    @Override
    public String toString() {
        return "StudentSchedules [studentScheduleId=" + studentScheduleId + ", studentId=" + studentId + ", scheduleId="
                + scheduleId + "]";
    }
    
}
