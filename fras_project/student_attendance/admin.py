from django.contrib import admin
from .models import Student,Department,CollegeYear,AttendanceSession

admin.site.register(Student)
admin.site.register(Department)
admin.site.register(CollegeYear)




@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'login_time', 'logout_time', 'duration')
    list_filter = ('student', 'date', 'student__Department__Name')
    search_fields = ('student__Roll_no', 'student__Fullname', 'student__Email')
# Register your models here.
