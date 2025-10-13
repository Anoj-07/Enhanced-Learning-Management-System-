from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from .models import Assessment, Submission, Enrollment, Sponsorship
from .utils import send_email_notification

from .models import Notification  # or your notification app path


User = get_user_model()


@receiver(m2m_changed, sender=User.groups.through)
def assign_admin_permissions(sender, instance, action, pk_set, **kwargs):
    """
    Automatically set is_staff=True when a user is added to the Admin group.
    """
    if action == "post_add":
        admin_group = Group.objects.filter(name="Admin").first()
        if admin_group and admin_group.id in pk_set:
            instance.is_staff = True
            instance.save()


# For Emailing System -----------------------------------


# For Email Notifications (Commented Out)
@receiver(post_save, sender=Assessment)
def notify_students_about_deadline(sender, instance, created, **kwargs):
    """
    Notify all enrolled students about new assessment deadlines.
    """
    if created:
        enrolled_students = Enrollment.objects.filter(course=instance.course)
        for enrollment in enrolled_students:
            student = enrollment.student
            subject = f"New Assessment: {instance.title}"
            message = (
                f"Dear {student.first_name or student.username},\n\n"
                f"A new assessment '{instance.title}' has been added for your course '{instance.course.name}'.\n"
                f"Deadline: {instance.due_date.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Please complete it before the deadline.\n\n"
                f"Best regards,\nLMS Team"
            )
            send_email_notification(subject, message, student.email)


@receiver(post_save, sender=Submission)
def notify_students_about_results(sender, instance, **kwargs):
    """
    Notify student when their assessment is graded.
    """
    if instance.grade is not None:
        student = instance.student
        subject = f"Assessment Result: {instance.assessment.title}"
        message = (
            f"Dear {student.first_name or student.username},\n\n"
            f"Your submission for '{instance.assessment.title}' has been graded.\n"
            f"Grade: {instance.grade}\n\n"
            f"Keep up the great work!\n\n"
            f"Best regards,\nLMS Team"
        )
        send_email_notification(subject, message, student.email)


@receiver(post_save, sender=Enrollment)
def notify_sponsor_about_student_progress(sender, instance, **kwargs):
    """
    Sends an email notification to sponsors whenever a student's course progress is updated.

    ✅ Output (Email Content):
    - Student Name
    - Course Name
    - Updated Progress (%)
    """

    student = instance.student
    course = instance.course
    progress = instance.progress

    # Notify only when progress > 50%
    if progress <= 50:
        return  # Exit without sending any email

    # Find all sponsors funding this student
    sponsorships = Sponsorship.objects.filter(student=student)

    if sponsorships.exists():
        for sponsorship in sponsorships:
            sponsor_user = (
                sponsorship.sponsor.sponsor
            )  # linked sponsor user (User model)

            subject = f"Progress Update: {student.username}'s progress in {course.name}"
            message = (
                f"Dear {sponsor_user.first_name or sponsor_user.username},\n\n"
                f"Your sponsored student **{student.first_name or student.username}** "
                f"has updated their progress in the course **{course.name}**.\n\n"
                f"📘 Course Name: {course.name}\n"
                f"👨‍🎓 Student Name: {student.first_name or student.username}\n"
                f"📈 Updated Progress: {progress}%\n\n"
                f"Keep supporting your student's learning journey!\n\n"
                f"Best regards,\nLMS Team"
            )

            # Send email to the sponsor
            send_email_notification(subject, message, sponsor_user.email)


# For notification system (Commented Out) -----------------------------------


@receiver(post_save, sender=Enrollment)
def notify_instructor_on_progress(sender, instance, created, **kwargs):
    """
    Notify the instructor when a student's progress updates
    and include total enrolled students in that instructor's course.
    """
    if not created and instance.progress is not None:
        course = instance.course
        instructor = course.instructor
        student = instance.student

        # Count total enrolled students in this course
        total_enrolled = Enrollment.objects.filter(course=course).count()

        # Create the notification message
        message = (
            f"Student {student.username} has achieved {instance.progress}% "
            f"completion in the course '{course.name}'.\n"
            f"Total students enrolled in this course: {total_enrolled}."
        )

        # Save notification
        Notification.objects.create(user=instructor, message=message)
