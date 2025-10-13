from django.utils import timezone
from datetime import timedelta
from .models import Assessment, Enrollment
from utils.email_service import send_email_notification

def send_due_date_reminders():
    upcoming_assessments = Assessment.objects.filter(due_date__lte=timezone.now() + timedelta(days=1))
    for assessment in upcoming_assessments:
        enrolled_students = Enrollment.objects.filter(course=assessment.course)
        for enrollment in enrolled_students:
            email = enrollment.student.email
            if email:
                subject = f"Reminder: '{assessment.title}' due soon!"
                message = (
                    f"Dear {enrollment.student.username},\n\n"
                    f"Your assessment '{assessment.title}' for the course '{assessment.course.name}' "
                    f"is due on {assessment.due_date.strftime('%Y-%m-%d %H:%M')}.\n\n"
                    f"Please make sure to submit before the deadline.\n\n"
                    f"Regards,\nLMS Team"
                )
                send_email_notification(subject, message, [email])
