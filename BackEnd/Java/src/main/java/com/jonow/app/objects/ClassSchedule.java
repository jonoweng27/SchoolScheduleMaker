package com.jonow.app.objects;

public class ClassSchedule {
    private int scheduleId;
    private int sectionNumber;
    private int courseId;
    private int teacherId;
    private int classCapacity;

    public ClassSchedule(int scheduleId, int sectionNumber, int courseId, int teacherId, int classCapacity) {
        this.scheduleId = scheduleId;
        this.sectionNumber = sectionNumber;
        this.courseId = courseId;
        this.teacherId = teacherId;
        this.classCapacity = classCapacity;
    }

    public Integer getScheduleId() {
        return scheduleId;
    }

    public void setScheduleId(int scheduleId) {
        this.scheduleId = scheduleId;
    }

    public int getSectionNumber() {
        return sectionNumber;
    }

    public void setSectionNumber(int sectionNumber) {
        this.sectionNumber = sectionNumber;
    }

    public Integer getCourseId() {
        return courseId;
    }

    public void setCourseId(int courseId) {
        this.courseId = courseId;
    }

    public int getTeacherId() {
        return teacherId;
    }

    public void setTeacherId(int teacherId) {
        this.teacherId = teacherId;
    }

    public int getClassCapacity() {
        return classCapacity;
    }

    public void setClassCapacity(int classCapacity) {
        this.classCapacity = classCapacity;
    }
}
