


from django.utils import timezone
from .models import AttendanceSession
from datetime import datetime, timedelta

def mark_login(student):
    now = timezone.now()
    today = now.date()
    current_time = now.time()

   
    existing = AttendanceSession.objects.filter(
        student=student,
        date=today,
        logout_time__isnull=True
    ).first()

    if existing:
        print("⚠️ Duplicate login prevented. Session already open.")
        return existing

    
    session = AttendanceSession.objects.create(
        student=student,
        date=today,
        login_time=current_time
    )
    print("✅ Login recorded.")
    return session


def mark_logout(student):
    now = timezone.now()
    today = now.date()
    current_time = now.time()

    
    session = AttendanceSession.objects.filter(
        student=student,
        date=today,
        logout_time__isnull=True
    ).order_by('-login_time').first()

    if not session:
        print("⚠️ No open session found for logout.")
        return None

   
    session.logout_time = current_time
    dt1 = datetime.combine(session.date, session.login_time)
    dt2 = datetime.combine(session.date, session.logout_time)
    session.duration = dt2 - dt1
    session.save()
    print("✅ Logout recorded and duration calculated.")
    return session
