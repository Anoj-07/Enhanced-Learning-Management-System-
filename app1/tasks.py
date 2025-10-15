from django.utils import timezone
from datetime import timedelta
from .models import Assessment, Enrollment
from .utils import send_email_notification

def send_due_date_reminders():
    """
    Sends email reminders to students about upcoming assessment due dates.
    1 day before the due date.
    1. Fetch assessments due in the next day.   
    2. For each assessment, get enrolled students.
    3. Send email reminders to each student.
    4. Log the email sending activity.
    5. Handle any exceptions during email sending.
    """
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
