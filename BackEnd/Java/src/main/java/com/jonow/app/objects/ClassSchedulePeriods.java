package com.jonow.app.objects;

public class ClassSchedulePeriods {
    private int scheduleId;
    private int periodId;
    private int dayOfWeek;
    private int room;

    public ClassSchedulePeriods(int scheduleId, int periodId, int dayOfWeek, int room) {
        this.scheduleId = scheduleId;
        this.periodId = periodId;
        this.dayOfWeek = dayOfWeek;
        this.room = room;
    }

    public Integer getScheduleId() {
        return scheduleId;
    }

    public void setScheduleId(int scheduleId) {
        this.scheduleId = scheduleId;
    }

    public Integer getPeriodId() {
        return periodId;
    }

    public void setPeriodId(int periodId) {
        this.periodId = periodId;
    }

    public int getDayOfWeek() {
        return dayOfWeek;
    }

    public void setDayOfWeek(int dayOfWeek) {
        this.dayOfWeek = dayOfWeek;
    }

    public int getRoom() {
        return room;
    }

    public void setRoom(int room) {
        this.room = room;
    }
}
