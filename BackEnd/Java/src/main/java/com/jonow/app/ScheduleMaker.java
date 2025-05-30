package com.jonow.app;

import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Function;

import com.jonow.app.objects.*;

public class ScheduleMaker {
    private Set<ClassSchedule> classSchedule;
    private Set<ClassSchedulePeriods> classSchedulePeriods;
    private List<StudentCourses> studentCourses;
    private Set<StudentSchedules> studentSchedules;
    private Set<Course> courses;

    public ScheduleMaker(Set<ClassSchedule> classSchedule, Set<ClassSchedulePeriods> classSchedulePeriods,
            List<StudentCourses> studentCourses, Set<Course> courses) {
        this.classSchedule = classSchedule;
        this.classSchedulePeriods = classSchedulePeriods;
        this.studentCourses = studentCourses;
        this.courses=courses;
        generate();
    }

    private void generate() {

        // Sort by # of periods in each course (highest to lowest)
        sortStudentCoursesBy(this::getNumberOfPeriodsPerClass, false);

        // Sort by # of sections in each course (lowest to highest)
        sortStudentCoursesBy(this::getNumberOfSectionsPerClass, true);

        // Assign Student to available course (NEED A WAY TO KEEP TRACK OF WHICH CLASSES A STUDENT IS ALREADY IN)
        studentSchedules = new HashSet<>();
        int scheduleId = 1;

        for (StudentCourses studentCourse : studentCourses) {
            List<ClassSchedule> availableSchedules = getAvailableSectionsForCourse(studentCourse);
            //if the List is empty, that means either: 1) Two classes conflict (in which case of one of the classes has another section, try to move it into that section). Or, 2) Spit back a message to the client saying a student is in two classes that cannot "shtim" together
            if (availableSchedules.isEmpty()) {
                System.out.println("Student " + studentCourse.getStudent() + " is in two classes that cannot be taken together");
                continue;
            }
            //assign the student to a random class in the list
            addStudentToRandomClass(scheduleId, studentCourse, availableSchedules);
        }
        // Check for class imbalances (and shuffle as necessary)
    }

    private void addStudentToRandomClass(int scheduleId, StudentCourses studentCourse,
            List<ClassSchedule> availableSchedules) {
        ClassSchedule randomSchedule = availableSchedules.get((int) (Math.random() * availableSchedules.size()));
        studentSchedules.add(new StudentSchedules(scheduleId++, studentCourse.getStudent(), randomSchedule.getScheduleId()));
    }


    //Gets all the available sections of this course for this student to take
    //Meaning, it returns all the sections that are offered for this course, excluding the periods where the student is enrolled in other classes
    private List<ClassSchedule> getAvailableSectionsForCourse(StudentCourses studentCourse) {
        return classSchedule.stream()
                .filter(cs -> cs.getCourseId().equals(studentCourse.getCourse()))
                .filter(cs -> studentSchedules.stream()
                        .noneMatch(ss -> ss.getStudentId().equals(studentCourse.getStudent())
                                && classSchedulePeriods.stream()
                                    .anyMatch(csp -> csp.getScheduleId().equals(ss.getScheduleId())
                                            && classSchedulePeriods.stream()
                                                .anyMatch(csp2 -> csp2.getScheduleId().equals(cs.getScheduleId())
                                                        && csp.getPeriodId().equals(csp2.getPeriodId())))))
                //TODO: Also filter out by classes that are "full"
                .toList();
    }
    
    // Generalized sort method
    private void sortStudentCoursesBy(Function<StudentCourses, Long> function, boolean ascending) {
        if (ascending) {
            Collections.sort(studentCourses, (a, b) -> Long.compare(function.apply(a), function.apply(b)));
        } else {
            Collections.sort(studentCourses, (a, b) -> Long.compare(function.apply(b), function.apply(a)));
        }
    }


    private long getNumberOfSectionsPerClass(StudentCourses a) {
        return classSchedule.stream().filter(cs -> cs.getCourseId().equals(a.getCourse())).count();
    }


    private long getNumberOfPeriodsPerClass(StudentCourses a) {
        return courses.stream()
            .filter(course -> course.getCourseId().equals(a.getCourse()))
            .mapToInt(Course::getNumPeriodsInWeek)
            .sum();
    }

    public Set<StudentSchedules> getResult() {
        return studentSchedules;
    }
}
