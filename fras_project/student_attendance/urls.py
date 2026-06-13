
from django.urls import path

from . import views

from django.contrib.auth import views as auth_views

urlpatterns = [

    path('adminlogin/', views.admin_login, name='adminlogin'),

    path("adminhome/",views.AdminHome,name="admin_homepage"),
    path("",views.Homepage,name="hp"),
    
    path("stulist/",views.StudentList,name="admin_stu"),
    path("deptlist/",views.DepartmentList,name="admin_dept"),
    path("stuform/",views.StudentForm,name="admin_stuform"),
    path("deptform/",views.DepartmentForm,name="admin_deptform"),
    path("studelete/<int:id>/",views.StudentDelete,name="studelete"),
    path("stuupdate/<int:id>/",views.StudentUpdate,name="stuupdate"),
    path("deptdelete/<int:id>/",views.DepartmentDelete,name="deptdelete"),
    path("deptupdate/<int:id>/",views.DepartmentUpdate,name="deptupdate"),
    

    path("logslist/",views.AttendanceList,name="attendancelogs"),
    path("logdelete/<int:id>/",views.LogDelete,name="log_delete"),

    path("stuhome/",views.StudentHome,name="stu_homepage"),
    path('student/login_video_feed/', views.student_login_video_feed, name='login'),
    path('student/logout_video_feed/', views.student_logout_video_feed, name='logout'),
    path('video_feed/', views.video_feed, name='video_feed'),

 
    path('students/export/pdf/', views.export_students_pdf, name='export_students_pdf'),
    path('logs/export/pdf/', views.export_attendance_pdf, name='export_attendance_pdf'),


    

    path('student-profiles/', views.StudentProfileImages, name='student_profiles'),
    
    path('upload-frame/', views.upload_frame, name='upload_frame'),
    path('retake/<str:roll_no>/', views.retake, name='retake'),

    path('student/login/', views.student_login_view, name='student_login'),
    path('student/<int:student_id>/', views.student_detail_view, name='student_detail'),
]
