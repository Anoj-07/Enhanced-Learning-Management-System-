from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, DjangoModelPermissions
from app1.models import Course, Enrollment, User, SponsorProfile, Sponsorship, Transaction, Enrollment, SponsorTransaction
from django.db import models
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from django.db.models import Sum, Avg
from decimal import Decimal

# Create your views here.

# Admin Analytics View ------------------------------------------------
class AdminAnalyticsView(APIView):
    """
    Provides aggregated platform analytics for the Admin Dashboard.
    Accessible only to Admin users.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Returns platform statistics:
        - Total Users
        - Total Courses (active/inactive)
        - Total Enrollments
        - Total Sponsors
        - Total Sponsorship Amount
        """

        total_users = User.objects.count()
        total_courses = Course.objects.count()
        active_courses = Course.objects.filter(is_active=True).count() if hasattr(Course, "is_active") else total_courses
        total_enrollments = Enrollment.objects.count()
        total_sponsors = SponsorProfile.objects.count()
        total_sponsorship_amount = Sponsorship.objects.aggregate(total=models.Sum("amount"))["total"] or 0

        data = {
            "total_users": total_users,
            "total_courses": total_courses,
            "active_courses": active_courses,
            "total_enrollments": total_enrollments,
            "total_sponsors": total_sponsors,
            "total_sponsorship_amount": float(total_sponsorship_amount),
        }
        return Response(data)
    

# Sponsor Analytics View ------------------------------------------------


class SponsorDashboardViewSet(ViewSet):
    """
    Sponsor dashboard analytics:
    - Shows sponsorship impact.
    - Student details and progress.
    - Fund utilization.
    - Additional metrics:
      - total funds added
      - total funds deducted
      - total students sponsored
      - average student progress
    """

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        user = request.user

        # Only sponsors can access
        if not user.groups.filter(name="Sponsor").exists():
            return Response(
                {"detail": "Access denied. Only sponsors can view this dashboard."}, 
                status=403
            )

        sponsor_profile = getattr(user, "sponsor_profile", None)
        if not sponsor_profile:
            return Response({"detail": "Sponsor profile not found."}, status=404)

        # All sponsorships by this sponsor
        sponsorships = sponsor_profile.sponsorships.select_related("student", "course").all()

        total_sponsored_amount = sponsorships.aggregate(total=Sum("amount"))["total"] or 0

        # Fund transactions: total added and deducted
        transactions = SponsorTransaction.objects.filter(sponsor=user)
        total_funds_added = transactions.filter(transaction_type="ADD").aggregate(total=Sum("amount"))["total"] or 0
        total_funds_deducted = transactions.filter(transaction_type="DEDUCT").aggregate(total=Sum("amount"))["total"] or 0

        # Collect student details
        student_data = []
        total_progress = Decimal(0)
        student_count = 0

        for s in sponsorships:
            enrollment_qs = Enrollment.objects.filter(student=s.student)
            if s.course:
                enrollment_qs = enrollment_qs.filter(course=s.course)

            enrollments = []
            for e in enrollment_qs:
                enrollments.append({
                    "course_name": e.course.name,
                    "progress": e.progress,
                    "enrolled_at": e.enrolled_at.strftime("%Y-%m-%d %H:%M:%S"),
                })
                total_progress += Decimal(e.progress)
                student_count += 1

            student_data.append({
                "student_id": s.student.id,
                "student_username": s.student.username,
                "student_first_name": s.student.first_name,
                "student_last_name": s.student.last_name,
                "sponsored_course": s.course.name if s.course else None,
                "sponsored_amount": str(s.amount),
                "enrollments": enrollments,
            })

        # Average student progress
        average_progress = (total_progress / student_count) if student_count > 0 else 0

        data = {
            "sponsor": user.username,
            "total_funds": str(sponsor_profile.total_funds),
            "total_sponsored_amount": str(total_sponsored_amount),
            "total_funds_added": str(total_funds_added),
            "total_funds_deducted": str(total_funds_deducted),
            "total_students_sponsored": sponsorships.values("student").distinct().count(),
            "average_student_progress": float(average_progress),
            "students": student_data,
        }

        return Response(data)
