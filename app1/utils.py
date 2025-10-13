from django.core.mail import send_mail
from django.conf import settings

from decimal import Decimal
from .models import Transaction, Course, User


def send_email_notification(subject, message, recipient_list):
    """
    Sends an email notification to users.
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_list],
        fail_silently=False,
    )


# student payment simulation utility


def simulate_payment(student: User, course: Course):
    """
    Simulates a payment for a paid course in development/testing.
    """
    if course.is_paid or course.price > 0:
        Transaction.objects.create(
            user=student,
            course=course,
            amount=Decimal(course.price),
            payment_method="Cash",  # just for testing
            status="Completed",
            transaction_id=f"DEV-{student.id}-{course.id}",
        )
        return True
    return False
