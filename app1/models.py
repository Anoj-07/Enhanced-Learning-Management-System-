from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

# Create your models here.
# profile model for Admin, Instructor, student, sponsor
# use in view and serializer to Group users


# course Model
class Course(models.Model):
    """
    Represents a course created by an instructor.
    Courses can be free or paid.
    """
    DIFFICULTY_CHOICES = [
        ("Beginner", "Beginner"),
        ("Intermediate", "Intermediate"),
        ("Advanced", "Advanced")
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    difficulty_level = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="instructor_courses", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Payment info
    is_paid = models.BooleanField(default=False, help_text="Indicates if the course is paid")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Price if paid")

    def __str__(self):
        return f"{self.name} ({self.difficulty_level})"


# Enrollment Model
class Enrollment(models.Model):
    """
    Tracks which students are enrolled in which courses.
    Tracks progress percentage.
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="course_enrollments")
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')  # prevent duplicate enrollment

    def __str__(self):
        return f"{self.student.username} → {self.course.name}"

# Assessment model
class Assessment(models.Model):
    """
    Represents an assessment (quiz/test) for a course.
    """

    course =  models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assessments")
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()

    def __str__(self):
        return f"{self.title} ({self.course.name})"
    

# submission model
class Submission(models.Model):
    """
    Student submissions for assessments.
    Represents a student's submission for a specific assessment.

    This model stores the details of a student's submission, including:
    - The related assessment.
    - The student who submitted it.
    - The submitted file (if any).
    - The submission timestamp.
    - The grade assigned (if evaluated).
    """
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_submissions")
    submitted_file = models.FileField(upload_to="submissions/", blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.student.username}'s submission for {self.assessment.title}"

# sponsorProfile model

class SponsorProfile(models.Model):
    """
    Extra info for sponsors.
    """

    sponsor = models.OneToOneField(User, on_delete=models.CASCADE, related_name="sponsor_profile")
    organization_name = models.CharField(max_length=255, blank=True, null=True)
    total_funds = models.DecimalField(max_digits=15, decimal_places=2, default=0.00
                                      , help_text="Total funds available for sponsorships")
    
    def __str__(self):
        return f"Sponsor: {self.sponsor.username}"


#Sponsorship model
class Sponsorship(models.Model):
    """
    Links sponsors to students or paid courses they fund.
    """
    sponsor = models.ForeignKey(SponsorProfile, on_delete=models.CASCADE, related_name="sponsorships")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="student_sponsorships")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="course_sponsorships", blank=True, null=True,
                               help_text="Optional if sponsorship is course-specific")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sponsor.sponsor.username} sponsors {self.student.username}"


# Notification model
class Notification(models.Model):
    """
    In-app notifications for users.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username}"
    


# for payment transaction model
class Transaction(models.Model):
    """
    Stores payment transaction details for sponsors or students.
    Customized for Nepalese payment gateways (eSewa, Khalti, Fonepay, IME Pay).
    """
    PAYMENT_STATUS = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Failed", "Failed"),
    ]

    PAYMENT_METHOD = [
        ("eSewa", "eSewa"),
        ("Khalti", "Khalti"),
        ("Fonepay", "Fonepay"),
        ("IMEPay", "IME Pay"),
        ("BankTransfer", "Bank Transfer"),
        ("Cash", "Cash"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_transactions")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="course_transactions", blank=True, null=True,
                               help_text="If this payment is for a course")
    sponsorship = models.ForeignKey(
        "Sponsorship",
        on_delete=models.SET_NULL,
        related_name="transactions",
        null=True,
        blank=True,
        help_text="If this payment is part of a sponsorship"
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default="Pending")
    transaction_id = models.CharField(max_length=255, unique=True, help_text="Transaction ID from gateway")
    reference_code = models.CharField(max_length=255, blank=True, null=True, help_text="Optional ref. like Khalti token/eSewa refId")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount} via {self.payment_method} ({self.status})"


class SponsorTransaction(models.Model):
    """
    Records each fund transaction made by a sponsor.

    ✅ Fields:
    - sponsor: Reference to the sponsor user.
    - transaction_type: ADD or DEDUCT.
    - amount: Decimal value for transaction amount.
    - balance_after: Balance after the transaction.
    - timestamp: Auto-generated timestamp for transaction.
    - description: Optional field for notes.
    """

    TRANSACTION_TYPES = (
        ('ADD', 'Add Funds'),
        ('DEDUCT', 'Deduct Funds'),
    )

    sponsor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sponsor_transactions")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sponsor.username} - {self.transaction_type} - {self.amount}"

    class Meta:
        ordering = ['-timestamp']
