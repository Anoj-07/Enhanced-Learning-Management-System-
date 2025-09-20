from django.db import models
from django.contrib.auth.models import User

# Create your models here.
# profile model for Admin, Instructor, student, sponsor

class Profile(models.Model):

    """
    Extends the default User model with role and extra info.
    This keeps authentication simple using DRF's TokenAuth or JWT.
    """
    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Instructor", "Instructor"),
        ("Student", "Student"),
        ("Sponsor", "Sponsor"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    full_name = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False, help_text="If the user is verified by in the system ")

    def __str__(self):
        return f"{self.full_name} ({self.role})"


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
    description = models.TextField()
    difficulty_level = models.CharField(max_length=50, choices=DIFFICULTY_CHOICES)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="instructor_courses")
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Payment info
    is_paid = models.BooleanField(default=False, help_text="Indicates if the course is paid")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Price if paid")

    def __str__(self):
        return f"{self.name} ({self.difficulty_level})"