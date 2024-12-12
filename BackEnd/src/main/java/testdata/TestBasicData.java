package testdata;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import com.jonow.app.ScheduleMaker;
import com.jonow.app.objects.ClassSchedule;
import com.jonow.app.objects.ClassSchedulePeriods;
import com.jonow.app.objects.Course;
import com.jonow.app.objects.StudentCourses;
import com.jonow.app.objects.StudentSchedules;



public class TestBasicData {
    
    public static void main(String[] args) {
        String filePath = "..\\Data\\BasicData\\";
        Set<ClassSchedule> classSchedules = readClassSchedules(filePath + "ClassSchedule.csv");
        Set<ClassSchedulePeriods> classSchedulePeriods = readClassSchedulePeriods(filePath + "ClassSchedulePeriod.csv");
        List<StudentCourses> studentCourses = readStudentCourses(filePath + "StudentsCourses.csv");
        Set<Course> courses = readCourses(filePath + "Course.csv");
        ScheduleMaker scheduleMaker = new ScheduleMaker(classSchedules, classSchedulePeriods, studentCourses, courses);
        List<StudentSchedules> result = new ArrayList<>(scheduleMaker.getResult());
        Collections.sort(result, (a,b)->Integer.compare(((StudentSchedules) a).getStudentId(), ((StudentSchedules) b).getStudentId()));
        System.out.println(result);
    }

    private static Set<ClassSchedule> readClassSchedules(String filePath) {
        Set<ClassSchedule> classSchedules = new HashSet<>();
        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String line = br.readLine(); // Skip the header line
            while ((line = br.readLine()) != null) {
                String[] values = line.split(",");
                ClassSchedule classSchedule = new ClassSchedule(
                    Integer.parseInt(values[0]), 
                    Integer.parseInt(values[1]), 
                    Integer.parseInt(values[2]), 
                    Integer.parseInt(values[3]), 
                    Integer.parseInt(values[4])
                );
                classSchedules.add(classSchedule);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return classSchedules;
    }

    private static Set<ClassSchedulePeriods> readClassSchedulePeriods(String filePath) {
        Set<ClassSchedulePeriods> ClassSchedulePeriodss = new HashSet<>();
        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String line = br.readLine(); // Skip the header line
            while ((line = br.readLine()) != null) {
                String[] values = line.split(",");
                ClassSchedulePeriods classSchedulePeriods = new ClassSchedulePeriods(
                    Integer.parseInt(values[0]),
                    Integer.parseInt(values[1]),
                    Integer.parseInt(values[2]),
                    1
                );
                ClassSchedulePeriodss.add(classSchedulePeriods);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return ClassSchedulePeriodss;
    }

    private static List<StudentCourses> readStudentCourses(String filePath) {
        List<StudentCourses> studentCourses = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String line = br.readLine(); // Skip the header line
            while ((line = br.readLine()) != null) {
                String[] values = line.split(",");
                StudentCourses studentCourse = new StudentCourses(
                    Integer.parseInt(values[0]), 
                    Integer.parseInt(values[1])
                );
                studentCourses.add(studentCourse);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return studentCourses;
    }

    
    private static Set<Course> readCourses(String filePath) {
        Set<Course> courses = new HashSet<>();
        try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
            String line = br.readLine(); // Skip the header line
            while ((line = br.readLine()) != null) {
                String[] values = line.split(",");
                Course course = new Course(
                    Integer.parseInt(values[0]), 
                    values[1], 
                    Integer.parseInt(values[2])
                );
                courses.add(course);
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
        return courses;
    }
}
