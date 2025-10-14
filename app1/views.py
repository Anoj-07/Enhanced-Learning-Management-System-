from django.shortcuts import render
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    DjangoModelPermissions,
    BasePermission,
)
from rest_framework.viewsets import (
    ModelViewSet,
    GenericViewSet,
    ReadOnlyModelViewSet,
    ViewSet,
)
from .models import (
    Course,
    Enrollment,
    Assessment,
    Submission,
    SponsorProfile,
    SponsorTransaction,
    Sponsorship,
    Notification,
)
from .Serializer import (
    CourseSerializer,
    EnrollmentSerializer,
    LoginSerializer,
    GroupSerializer,
    UserSerializer,
    AssessmentSerializer,
    SubmissionSerializer,
    SponsorProfileSerializer,
    SponsorshipSerializer,
)
from django.contrib.auth import authenticate
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from .ai import generate_course_description
from django.contrib.auth.models import User, Group
from rest_framework.authtoken.models import Token
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from decimal import Decimal, InvalidOperation
from .utils import simulate_payment
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filter import SponsorshipFilter


# this is claSS for pagination --------------------------------------------------------------
class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for courses, students, sponsorships, etc.
    """
    page_size = 10  # default items per page
    page_size_query_param = "page_size"  # allow ?page_size=20
    max_page_size = 100


# Create your views here.


# view or create a course --------------------------------------------------------------
class CourseViewSet(ModelViewSet):
    """
    Course CRUD API with role-based access:
    - Instructor: Can create, update, view their own courses.
    - Admin: Can create, update, delete, and view all courses.
    - Student: Can only view courses (enrolled or all).
    - Sponsor: Can only view courses.

    AI Description:
    - Automatically generates course description if not provided.
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "instructor__username", "difficulty_level"]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Filter courses based on user role:
        - Instructor: only their courses
        - Student: all courses (optionally filter enrolled courses)
        - Sponsor: all courses (optionally filter sponsored courses)
        - Admin: all courses
        """
        user = self.request.user

        # Instructor sees only their courses
        if user.groups.filter(name="Instructor").exists():
            return Course.objects.filter(instructor=user)

        # Student can see all courses (can be filtered for enrolled courses if needed)
        elif user.groups.filter(name="Student").exists():
            return Course.objects.all()

        # Sponsor can see all courses (or filter sponsored courses)
        elif user.groups.filter(name="Sponsor").exists():
            return Course.objects.all()

        # Admin sees all courses
        elif user.groups.filter(name="Admin").exists() or user.is_staff:
            return Course.objects.all()

        # Default: no access
        return Course.objects.none()

    def perform_create(self, serializer):
        """
        Handles course creation:
        1. Automatically assigns logged-in instructor.
        2. Generates AI description if not provided.
        """
        user = self.request.user

        # Only instructors and admins can create courses
        if not (
            user.groups.filter(name="Instructor").exists()
            or user.groups.filter(name="Admin").exists()
            or user.is_staff
        ):
            raise PermissionDenied("You do not have permission to create a course.")

        name = serializer.validated_data.get("name")
        difficulty_level = serializer.validated_data.get("difficulty_level")
        description = serializer.validated_data.get("description")

        try:
            # Generate AI description if empty
            if not description:
                description = generate_course_description(name, difficulty_level)

            # Save course with instructor and description
            serializer.save(instructor=user, description=description)

        except Exception as e:
            raise APIException(f"Error generating course description: {str(e)}")


# -----------------------------
# User API (Register + Login) --------------------------------------------------------------------
# -----------------------------
class UserViewSet(GenericViewSet):
    """
    Handles user registration and login.
    Groups are used for role assignment.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = []  # Registration/Login is open

    # @action(detail=False, methods=['post'])
    def register(self, request):
        """
        POST /users/register/
        Register a new user:
        - username, password, email, first_name, last_name
        - Optionally assign groups (roles)
        """
        serializer = self.get_serializer(
            data=request.data
        )  # get_serializer method returns the serializer class defined in the view
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def login(self, request):
        """
        Custom endpoint: POST /login/
        Authenticates a user:
        - Accepts username and password
        - Returns user details if credentials are valid
        - Returns error if invalid credentials
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data.get("username")
            password = serializer.validated_data.get("password")

            user = authenticate(username=username, password=password)
            print(user)

            if user is None:
                return Response(
                    {"error": "Invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            else:
                token, _ = Token.objects.get_or_create(user=user)

                return Response(
                    {
                        "token": token.key,
                        "username": user.username,
                        "email": user.email,
                    },
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupApiViewSet(ReadOnlyModelViewSet):
    """
    API endpoint to manage user groups.
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = []


# -----------------------------
# Enrollment API
# -----------------------------
# class for custom permission for EnrollmentViewSet -------------------------------------------------------
class IsStudentOrAdmin(BasePermission):
    """
    Allow student to update their own enrollment, or admin/staff to update any.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
        return (
            obj.student == user
            or user.is_staff
            or user.groups.filter(name="Admin").exists()
        )


class EnrollmentViewSet(ModelViewSet):
    """
    Handles course enrollments.
    Students can enroll in courses.
    Instructors/Admins can view enrollments.
    """

    serializer_class = EnrollmentSerializer
    permission_classes = [
        IsAuthenticated,
        DjangoModelPermissions,
    ]  # Must be logged in # this is for permission

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]    
    search_fields = ["course__name", "student__username"]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name="Admin").exists() or user.is_staff:
            return Enrollment.objects.all()
        elif user.groups.filter(name="Instructor").exists():
            # Instructor sees enrollments for their courses
            return Enrollment.objects.filter(course__instructor=user)
        elif user.groups.filter(name="Student").exists():
            # Student sees only their enrollments
            return Enrollment.objects.filter(student=user)
        else:
            return Enrollment.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if user.is_anonymous or not user.groups.filter(name="Student").exists():
            raise PermissionDenied("Only authenticated students can enroll in courses.")

        course = serializer.validated_data.get("course")
        if not course:
            raise ValidationError("Course must be provided.")

        # Prevent duplicate enrollment
        if Enrollment.objects.filter(student=user, course=course).exists():
            raise ValidationError("You are already enrolled in this course.")

        # Paid course check: is_paid True OR price > 0
        if course.is_paid or course.price > 0:
            # Check if student has sponsorship for this course
            has_sponsorship = Sponsorship.objects.filter(
                student=user, course=course
            ).exists()
            # Check if student has completed payment for this course
            has_payment = course.course_transactions.filter(
                user=user, status="Completed"
            ).exists()
            if not (has_sponsorship or has_payment):
                raise PermissionDenied(
                    "This is a paid course. You must pay or have sponsorship to enroll."
                )

        # Free course or paid course with sponsorship/payment
        serializer.save(student=user)

    @action(
        detail=True,
        methods=["patch"],
        url_path="update_progress",
        permission_classes=[IsStudentOrAdmin],
    )
    def update_progress(self, request, pk=None):
        enrollment = self.get_object()

        # Validate progress
        progress = request.data.get("progress")
        try:
            progress = float(progress)
        except (ValueError, TypeError):
            return Response(
                {"error": "Progress must be a number"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (0 <= progress <= 100):
            return Response(
                {"error": "Progress must be between 0 and 100"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        enrollment.progress = progress
        enrollment.save()
        return Response({"message": "Progress updated successfully"})

    @action(detail=False, methods=["post"], url_path="simulate-payment")
    def simulate_payment_api(self, request):
        student = request.user
        course_id = request.data.get("course")

        # Validate course ID
        if not course_id:
            return Response(
                {"error": "Course ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if student is already enrolled
        if Enrollment.objects.filter(student=student, course=course).exists():
            return Response(
                {"message": f"You are already enrolled in {course.name}."},
                status=status.HTTP_200_OK,
            )

        # Free course → enroll directly
        if not course.is_paid or course.price == 0:
            Enrollment.objects.create(student=student, course=course, progress=0)
            return Response(
                {"message": f"Successfully enrolled in free course {course.name}."},
                status=status.HTTP_201_CREATED,
            )

        # Paid course → simulate payment first
        payment_success = simulate_payment(student, course)

        if payment_success:
            # Enroll student after payment
            Enrollment.objects.create(student=student, course=course, progress=0)
            return Response(
                {"message": f"Payment completed and enrolled in {course.name}."},
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {"error": "Payment failed. Cannot enroll in course."},
                status=status.HTTP_400_BAD_REQUEST,
            )


# class for Assessement -----------------------------------------------------
class AssessmentViewSet(ModelViewSet):
    """
    Handles CRUD operations for Assessments.
    - Only instructors (course owners) can create or update assessments.
    - Students can only view assessments.
    """

    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [
        IsAuthenticated,
        DjangoModelPermissions,
    ]  # Must be logged in # this is for permission

    def perform_create(self, serializer):
        """
        Automatically ensure that only instructors of a course can create assessments.
        """
        user = self.request.user
        course = serializer.validated_data.get("course")

        # Check if the user is the instructor of this course
        if course.instructor != user:
            return Response(
                {"error": "You are not the instructor for this course."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer.save()

    def get_queryset(self):
        """
        Filter assessments based on the user's role:
        - Instructors see their course assessments.
        - Students see assessments of enrolled courses.
        - Admins see all assessments.
        """
        user = self.request.user

        if user.groups.filter(name="Admin").exists():
            return Assessment.objects.all()
        elif user.groups.filter(name="Instructor").exists():
            return Assessment.objects.filter(course__instructor=user)
        elif user.groups.filter(name="Student").exists():
            return Assessment.objects.filter(course__course_enrollments__student=user)
        else:
            return Assessment.objects.none()


# custom role for  Submission ViewSet ----------------------------------------------
class IsInstructorOrAdmin(BasePermission):
    """
    Allows access only to Instructors (who own the course) or Admin/Staff users.
    """

    def has_permission(self, request, view):
        # Must be authenticated first
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Object-level check:
        - Instructor can grade only submissions for their own course's assessment.
        - Admin/Staff can grade any.
        """
        user = request.user

        # Check if user is Admin or staff
        if user.is_staff or user.groups.filter(name="Admin").exists():
            return True

        # Check if user is instructor of the related course
        return (
            user.groups.filter(name="Instructor").exists()
            and obj.assessment.course.instructor == user
        )


class SubmissionViewSet(ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [
        IsAuthenticated,
        DjangoModelPermissions,
    ]  # Must be logged in # this is for permission

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="Admin").exists() or user.is_staff:
            return Submission.objects.all()
        elif user.groups.filter(name="Instructor").exists():
            return Submission.objects.filter(assessment__course__instructor=user)
        elif user.groups.filter(name="Student").exists():
            return Submission.objects.filter(student=user)
        return Submission.objects.none()

    @action(detail=True, methods=["patch"], permission_classes=[IsInstructorOrAdmin])
    def grade_submission(self, request, pk=None):
        """
        PATCH /submissions/{id}/grade_submission/
        Allows Instructor or Admin to grade a student's submission.
        """
        submission = self.get_object()
        grade = request.data.get("grade")

        try:
            grade = float(grade)
        except (ValueError, TypeError):
            return Response(
                {"error": "Grade must be a numeric value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (0 <= grade <= 100):
            return Response(
                {"error": "Grade must be between 0 and 100"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission.grade = grade
        submission.save()

        return Response(
            {"message": "Submission graded successfully", "grade": submission.grade},
            status=status.HTTP_200_OK,
        )


# SponsorProfile viewset ------------------------------------------------------------
class SponsorProfileViewSet(ModelViewSet):
    """
    API endpoint for managing Sponsor Profiles.
    - Sponsors can create and view their own profile.
    - Admins can view and manage all profiles.
    """

    queryset = SponsorProfile.objects.all()
    serializer_class = SponsorProfileSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    def get_queryset(self):
        """
        Filter sponsor data based on user role:
        - Admin: See all sponsor profiles.
        - Sponsor: See only their own profile.
        """
        user = self.request.user

        if user.is_staff or user.groups.filter(name="Admin").exists():
            return SponsorProfile.objects.all()
        elif user.groups.filter(name="Sponsor").exists():
            return SponsorProfile.objects.filter(sponsor=user)
        return SponsorProfile.objects.none()

    def perform_create(self, serializer):
        """
        Automatically attach the logged-in sponsor to the created profile.
        """
        user = self.request.user

        # Only sponsors can create profiles
        if not user.groups.filter(name="Sponsor").exists():
            raise PermissionDenied("Only sponsors can create sponsor profiles.")

        serializer.save(sponsor=user)

    # To update funds incrementally
    # inside SponsorProfileViewSet

    @action(detail=True, methods=["patch"], url_path="add-funds")
    def add_funds(self, request, pk=None):
        sponsor_profile = self.get_object()
        amount = request.data.get("amount") or request.data.get("total_funds")

        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError, InvalidOperation):
            return Response(
                {"error": "Please provide a valid positive number for 'amount'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount <= 0:
            return Response(
                {"error": "Amount must be a positive number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sponsor_profile.total_funds += amount
        sponsor_profile.save()

        # ✅ Record transaction
        SponsorTransaction.objects.create(
            sponsor=sponsor_profile.sponsor,
            transaction_type="ADD",
            amount=amount,
            balance_after=sponsor_profile.total_funds,
            description=f"Added {amount} funds.",
        )

        return Response(
            {
                "message": f"Successfully added {amount} to sponsor funds.",
                "total_funds": str(sponsor_profile.total_funds),
            }
        )

    @action(detail=True, methods=["patch"], url_path="deduct-funds")
    def deduct_funds(self, request, pk=None):
        sponsor_profile = self.get_object()
        amount = request.data.get("amount")

        try:
            amount = Decimal(str(amount))
        except (ValueError, TypeError, InvalidOperation):
            return Response(
                {"error": "Please provide a valid positive number for 'amount'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount <= 0:
            return Response(
                {"error": "Amount must be a positive number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if sponsor_profile.total_funds < amount:
            return Response(
                {"error": "Insufficient funds to deduct this amount."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sponsor_profile.total_funds -= amount
        sponsor_profile.save()

        # ✅ Record transaction
        SponsorTransaction.objects.create(
            sponsor=sponsor_profile.sponsor,
            transaction_type="DEDUCT",
            amount=amount,
            balance_after=sponsor_profile.total_funds,
            description=f"Deducted {amount} funds.",
        )

        return Response(
            {
                "message": f"Successfully deducted {amount} from sponsor funds.",
                "total_funds": str(sponsor_profile.total_funds),
            }
        )

    @action(detail=True, methods=["get"], url_path="transactions")
    def view_transactions(self, request, pk=None):
        """
        GET /sponsorprofiles/{id}/transactions/

        Returns a list of all transactions for this sponsor.
        """
        sponsor_profile = self.get_object()
        transactions = SponsorTransaction.objects.filter(
            sponsor=sponsor_profile.sponsor
        )
        data = [
            {
                "type": t.transaction_type,
                "amount": str(t.amount),
                "balance_after": str(t.balance_after),
                "timestamp": t.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "description": t.description,
            }
            for t in transactions
        ]
        return Response(data)


# View for SponsorShip model ------------------------------------------------------
class SponsorshipViewSet(ModelViewSet):
    """
    Manage sponsorships between sponsors and students.
    Sponsors can create sponsorships for students/courses they fund.
    Admins can view and manage all sponsorships.
    """

    queryset = Sponsorship.objects.all()
    serializer_class = SponsorshipSerializer
    permission_classes = [IsAuthenticated, DjangoModelPermissions]

    filter_backends = [filters.SearchFilter]
    search_fields = ["student__username",  "course__name"]
    filterset_class = SponsorshipFilter
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        # Admins see all
        if user.is_staff or user.groups.filter(name="Admin").exists():
            return Sponsorship.objects.all()
        # Sponsors see their own sponsorships
        elif user.groups.filter(name="Sponsor").exists():
            return Sponsorship.objects.filter(sponsor__sponsor=user)
        return Sponsorship.objects.none()

    def perform_create(self, serializer):
        """
        Automatically attach the logged-in sponsor's SponsorProfile to the sponsorship.
        Deducts funds automatically.
        """
        user = self.request.user

        # ✅ Get sponsor profile
        try:
            sponsor_profile = SponsorProfile.objects.get(sponsor=user)
        except SponsorProfile.DoesNotExist:
            raise PermissionDenied(
                "You must have a SponsorProfile to create sponsorships."
            )

        sponsorship = serializer.save(sponsor=sponsor_profile)

        # ✅ Deduct amount from funds
        if sponsor_profile.total_funds < sponsorship.amount:
            raise ValidationError("Insufficient funds for this sponsorship.")

        sponsor_profile.total_funds -= sponsorship.amount
        sponsor_profile.save()

        # ✅ Record transaction
        SponsorTransaction.objects.create(
            sponsor=user,
            transaction_type="DEDUCT",
            amount=sponsorship.amount,
            balance_after=sponsor_profile.total_funds,
            description=f"Sponsorship for {sponsorship.student.username}",
        )


# notification system for Instructor and Sponsor ---------------------------------------------------


class InstructorNotificationViewSet(ViewSet):
    """
    Whenever a student updates progress or completes a course,
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user
        if not user.groups.filter(name="Instructor").exists():
            return Response(
                {"detail": "Access denied. Only instructors can view this."}, status=403
            )

        notifications = Notification.objects.filter(user=user).order_by("-created_at")
        data = [
            {
                "id": n.id,
                "message": n.message,
                "created_at": n.created_at,
                "is_read": n.is_read,
            }
            for n in notifications
        ]
        return Response(data)
