from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, date
import os
from django.utils import timezone
from django.utils.timezone import now
    
class Department(models.Model):
    Name=models.CharField(max_length=200)
    Description=models.TextField(null=True,blank=True)

    def __str__(self):
        return self.Name
    

class CollegeYear(models.Model):
    Year=models.CharField(max_length=50)
    Department=models.ForeignKey(Department,on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return f"{self.Year}"
    



def student_profile(instance,filename):
    ext=filename.split('.')[-1]
    filename=f"{instance.Roll_no}_{instance.Fullname}.{ext}"
    return os.path.join('student_potos',now().strftime('%y/%m'),filename)

    
class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    Fullname=models.CharField(max_length=200)
    Roll_no=models.CharField(max_length=100)
    Department=models.ForeignKey(Department,on_delete=models.CASCADE)
    Year=models.ForeignKey(CollegeYear,on_delete=models.CASCADE,null=True,blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True) 
    phone_number=models.CharField(max_length=15)
    Email=models.EmailField(max_length=254,unique=True)
    photo=models.ImageField(upload_to=student_profile,blank=True,null=True)


    def __str__(self):
        return self.Fullname
    
    def clean(self):           #custom validation
        if self.Year and self.Year.Department!=self.Department:
            raise ValidationError("selected year does not belong to the selected department")
    




class AttendanceSession(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    login_time = models.TimeField()
    logout_time = models.TimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.login_time and self.logout_time:
            dt1 = datetime.combine(self.date, self.login_time)
            dt2 = datetime.combine(self.date, self.logout_time)
            self.duration = dt2 - dt1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.Roll_no} - {self.date} - {self.login_time} to {self.logout_time or 'Active'}"

    @property
    def department(self):
        return self.student.Department.Name

    @property
    def year(self):
        return self.student.Year.Year

    @property
    def email(self):
        return self.student.Email

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'date', 'login_time', 'logout_time'],
                name='unique_attendance_session'
            )
        ]





    

