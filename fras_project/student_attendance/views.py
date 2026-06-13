from django.shortcuts import render,redirect,get_object_or_404


from .models import Student,Department,AttendanceSession
from .forms import Department_Form, Student_Form,StudentLoginForm
from .filters import StudentFilter,LogsFilter


from django.http import StreamingHttpResponse
from .camera import VideoCamera

from django.contrib import messages

from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa

from django.utils.timezone import now

from .attendance_utils import mark_login

import os
import base64
from django.core.files.base import ContentFile
from django.conf import settings
from django.views.decorators import gzip

from django.utils import timezone

from .face_utils import load_known_faces
from .camera import VideoCamera


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.storage import default_storage


from django.core.files import File

from django.contrib.auth.decorators import login_required

from django.contrib.auth import authenticate, login






@login_required
def admin_homepage(request):
    return render(request, 'admin_homepage.html')


def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('admin_homepage')  # go to admin homepage after login
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'base/admin_login.html')  # Show login form for GET




"""
@csrf_exempt
def upload_frame(request):
    if request.method == 'POST':
        roll_no = request.POST.get('roll_no')
        frame = request.FILES.get('frame')

        if not roll_no or not frame:
            return JsonResponse({'error': 'Missing data'}, status=400)

        # Create the directory for the student's frames
        folder_path = os.path.join(settings.BASE_DIR, 'student profile', roll_no)
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, frame.name)

        with default_storage.open(file_path, 'wb+') as destination:
            for chunk in frame.chunks():
                destination.write(chunk)

        return JsonResponse({'status': 'Frame uploaded successfully'})
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

"""







import os
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

@csrf_exempt
def upload_frame(request):
    """
    Receives a single file upload (FormData: roll_no, frame).
    Saves to: <STUDENT_PROFILE_ROOT>/<roll_no>/<unique-filename>.jpg
    Returns JSON with status and saved filename / path (or error).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    roll_no = request.POST.get('roll_no')
    frame = request.FILES.get('frame')

    if not roll_no or not frame:
        return JsonResponse({'error': 'Missing roll_no or frame'}, status=400)

    
    base_dir = getattr(settings, 'STUDENT_PROFILE_ROOT', None)
    if not base_dir:
        return JsonResponse({'error': 'STUDENT_PROFILE_ROOT not configured'}, status=500)

    
    folder_path = os.path.join(base_dir, str(roll_no))
    try:
        os.makedirs(folder_path, exist_ok=True)
    except Exception as e:
        return JsonResponse({'error': f'Failed to create folder: {e}'}, status=500)

   
    timestamp = int(time.time() * 1000)
    
    orig_ext = os.path.splitext(frame.name)[1].lower() or '.jpg'
    filename = f"frame_{timestamp}{orig_ext}"
    file_path = os.path.join(folder_path, filename)

    try:
        
        with open(file_path, 'wb+') as f:
            for chunk in frame.chunks():
                f.write(chunk)
    except Exception as e:
        return JsonResponse({'error': f'Failed to save file: {e}'}, status=500)

    return JsonResponse({'status': 'ok', 'saved': file_path})





@csrf_exempt
def retake(request, roll_no):
    if request.method == 'POST':
        folder_path = os.path.join(settings.BASE_DIR, 'student profile', roll_no)

        if os.path.exists(folder_path):
            import shutil                         #deletes the folder
            shutil.rmtree(folder_path)
            return JsonResponse({'status': 'Previous training data deleted'})
        else:
            return JsonResponse({'status': 'No training data to delete'})
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)





known_face_encodings, known_face_names = load_known_faces()
camera = VideoCamera(known_face_encodings, known_face_names, recognize_faces=True, detection_model='cnn')



@gzip.gzip_page
def student_login_video_feed(request):
    camera = VideoCamera(known_face_encodings, known_face_names, recognize_faces=True, detection_model='cnn', action='login')
    return StreamingHttpResponse(gen(camera), content_type='multipart/x-mixed-replace; boundary=frame')

@gzip.gzip_page
def student_logout_video_feed(request):
    camera = VideoCamera(known_face_encodings, known_face_names, recognize_faces=True, detection_model='cnn', action='logout')
    return StreamingHttpResponse(gen(camera), content_type='multipart/x-mixed-replace; boundary=frame')





def AdminHome(request):

    total_students = Student.objects.count()

    today = now().date()

    # Count unique students who logged in today
    today_logins = AttendanceSession.objects.filter(date=today).values('student').distinct().count()


    present_percent = round((today_logins / total_students) * 100, 1) if total_students > 0 else 0
    absent_percent = round(100 - present_percent, 1) if total_students > 0 else 0

    context = {
        'total_students': total_students,
        'today_logins': today_logins,
        'present_percent': present_percent,
        'absent_percent': absent_percent,
    }
    return render(request,"base/admin_home.html",context)




def AttendanceList(request):
    logs_qs = AttendanceSession.objects.order_by('-date', '-login_time')
    logs_filter = LogsFilter(request.GET, queryset=logs_qs)
    filtered_qs = logs_filter.qs

    seen = set()
    unique_attendance = []

    for entry in filtered_qs:
        key = (entry.student_id, entry.date, entry.login_time)
        if key not in seen:
            seen.add(key)
            unique_attendance.append(entry)

    context = {
        "attendance_logs": unique_attendance,
        "logs_filter": logs_filter  # Pass the filter to the template
    }
    return render(request, "base/logs.html", context)


def StudentList(request):
    myfilter=StudentFilter(request.GET,queryset=Student.objects.all())
    filtered_qs = myfilter.qs 
    total_students = filtered_qs.count()
    total_male_student = filtered_qs.filter(gender='M').count()
    total_female_student = filtered_qs.filter(gender='F').count()
    context={
        "student_list":myfilter.qs,
        "total_student":total_students,
        "total_male_student":total_male_student,
        "total_female_student":total_female_student,
        "myfilter":myfilter
    }
    return render(request,"base/stu_list.html",context)

def DepartmentList(request):
    departments=Department.objects.all()
    total_departments=departments.count()
    context={
        "department_list":departments,
        "total_department":total_departments
    }

    return render(request,"base/dept_list.html",context)





def StudentForm(request):
    if request.method == 'POST':
        sform = Student_Form(request.POST)
        if sform.is_valid():
            student = sform.save(commit=False)

            image_data = request.POST.get('captured_image')

            if image_data:
                print("📸 Image received.")

                try:
                    # Decode the base64 image
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    data = base64.b64decode(imgstr)

                    roll = student.Roll_no
                    filename = f"{roll}.{ext}"

                    # Save image to custom folder
                    save_dir = os.path.join(settings.BASE_DIR, 'student profile')
                    os.makedirs(save_dir, exist_ok=True)
                    save_path = os.path.join(save_dir, filename)

                    print("💾 Writing image to:", save_path)

                    with open(save_path, 'wb') as f:
                        f.write(data)

                    print("✅ Image saved to:", save_path)

                    # Save the image to the ImageField as well
                    with open(save_path, 'rb') as f:
                        student.photo.save(filename, File(f), save=False)

                    print("✅ Image linked to model field.")

                except Exception as e:
                    print("❌ Failed to save image:", e)

            else:
                print("⚠️ No image data received.")

            student.save()
            return redirect('admin_stu')

    else:
        sform = Student_Form()

    return render(request, "base/stu_form.html", {'form': sform})





def DepartmentForm(request):
    if request.method=="POST":
        dform=Department_Form(request.POST)
        if dform.is_valid():
            dform.save()
            return redirect("admin_dept")
        
    else:
        dform=Department_Form()

    return render(request,"base/dept_form.html",{'form':dform})








def LogDelete(request,id):
    Logs=AttendanceSession.objects.get(pk=id)
    Logs.delete()
    return redirect("attendancelogs")


def StudentDelete(request,id):
    student=Student.objects.get(pk=id)
    student.delete()
    return redirect("admin_stu")

def StudentUpdate(request,id):
    student=get_object_or_404(Student,id=id)
    if request.method=='GET':
        form=Student_Form(instance=student)
        return render(request,"base/stu_form.html",{'form':form})
    
    else:
        form=Student_Form(request.POST,instance=student)
        if form.is_valid():
            form.save()
            return redirect("admin_stu")
            
        return render(request,"base/stu_form.html",{'form':form})
        

def DepartmentDelete(request,id):
    department=Department.objects.get(pk=id)
    department.delete()
    return redirect("admin_dept")

def DepartmentUpdate(request,id):
    department=get_object_or_404(Department,id=id)
    if request.method=="GET":
        form=Department_Form(instance=department)
        return render(request,"base/dept_form.html",{'form':form})
    
    else:
        form=Department_Form(request.POST,instance=department)
        if form.is_valid():
            form.save()
            return redirect("admin_dept")
        return render(request,"base/dept_form.html",{'form':form})
    


def StudentHome(request):
    return render(request,"base/student_home.html")


def StudentLogin(request):
    return render(request,"base/login.html")

def StudentLogout(request):
    return render(request,"base/logout.html")


def Homepage(request):
    return render(request,"base/homepage.html")




camera = VideoCamera(known_face_encodings, known_face_names, recognize_faces=True, detection_model='cnn')

def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def video_feed(request):
    return StreamingHttpResponse(gen(camera), content_type='multipart/x-mixed-replace; boundary=frame')





def StudentProfileImages(request):
    folder_path = settings.STUDENT_PROFILE_ROOT
    search_query = request.GET.get('search', '').lower()
    images = []

    # Loop through the files in the student profile folder
    for file in os.listdir(folder_path):
        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            # Check if the search query matches the filename
            if search_query in file.lower():
                image_url = settings.STUDENT_PROFILE_URL + file
                images.append({'url': image_url, 'filename': file})

    context = {'images': images, 'search_query': search_query}
    return render(request, 'base/student_profiles.html', context)








def export_students_pdf(request):
    filtered_students = StudentFilter(request.GET, queryset=Student.objects.all())
    students = filtered_students.qs  # filtered queryset

    template = get_template('base/students_pdf.html')
    html = template.render({'student_list': students})

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="students.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response







def export_attendance_pdf(request):
    # Apply filters (if any)
    logs_filter = LogsFilter(request.GET, queryset=AttendanceSession.objects.order_by('-date', '-login_time'))
    filtered_logs = logs_filter.qs

    # Remove duplicates like in your AttendanceList view
    seen = set()
    unique_attendance = []
    for entry in filtered_logs:
        key = (entry.student_id, entry.date, entry.login_time)
        if key not in seen:
            seen.add(key)
            unique_attendance.append(entry)

   
    template = get_template('base/attendance_pdf.html')
    html = template.render({'attendance_logs': unique_attendance})

    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="attendance_logs.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF', status=500)
    return response





def student_login_view(request):
    if request.method == 'POST':
        form = StudentLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            roll_no = form.cleaned_data['roll_no']

            try:
                # Try to find the student by username and roll_no
                student = Student.objects.get(Fullname=username, Roll_no=roll_no)
                # Redirect to student detail page or render student info + attendance logs
                return redirect('student_detail', student_id=student.id)
            except Student.DoesNotExist:
                messages.error(request, "Invalid username or roll number.")
    else:
        form = StudentLoginForm()

    return render(request, 'base/student_login.html', {'form': form})







def student_detail_view(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    attendance_logs = AttendanceSession.objects.filter(student=student).order_by('-date', '-login_time')

    
    photo_filename = f"{student.Roll_no}.jpg"  
    photo_path = os.path.join(settings.STUDENT_PROFILE_ROOT, photo_filename)

    
    if os.path.exists(photo_path):
        photo_url = settings.STUDENT_PROFILE_URL + photo_filename
    else:
        photo_url = None 

    context = {
        'student': student,
        'attendance_logs': attendance_logs,
        'photo_url': photo_url,
    }
    return render(request, 'base/student_detail.html', context)



