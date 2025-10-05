from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated, AllowAny, DjangoModelPermissions
from rest_framework.viewsets import ModelViewSet, GenericViewSet, ReadOnlyModelViewSet
from .models import Course, Enrollment
from .Serializer import CourseSerializer, EnrollmentSerializer, LoginSerializer, GroupSerializer, UserSerializer
from django.contrib.auth import authenticate
from rest_framework.exceptions import APIException
from .ai import generate_course_description
from django.contrib.auth.models import User, Group
from rest_framework.authtoken.models import Token
from rest_framework import  permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
# Create your views here.

# view to create a course
class CourseViewSet(ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    # for Ai Description
    def perform_create(self, serializer):
        name = serializer.validated_data.get('name')
        description = serializer.validated_data.get('description')
        difficulty_level = serializer.validated_data.get('difficulty_level')

        try:
            if not description:
                description = generate_course_description(name, difficulty_level)
            
            serializer.save(description=description)
        except Exception as e:
            raise APIException(f"Error generating description: {str(e)}")


# -----------------------------
# User API (Register + Login)
# -----------------------------
class UserViewSet(GenericViewSet):
    """
    Handles user registration and login.
    Groups are used for role assignment.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]  # Registration/Login is open

    # @action(detail=False, methods=['post'])
    def register(self, request):
        """
        POST /users/register/
        Register a new user:
        - username, password, email, first_name, last_name
        - Optionally assign groups (roles)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Assign user to groups if provided
        group_ids = request.data.get("groups", [])
        if group_ids:
            groups = Group.objects.filter(id__in=group_ids)
            user.groups.set(groups)

        # Create auth token
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "user": UserSerializer(user).data,
            "token": token.key
        }, status=status.HTTP_201_CREATED)

    # @action(detail=False, methods=['post'])
    def login(self, request):
        """
        POST /users/login/
        Authenticates user and returns token
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(username=username, password=password)

        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user).data,
            "token": token.key
        })


        
class GroupApiViewSet(ReadOnlyModelViewSet):
    """
    API endpoint to manage user groups.
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [DjangoModelPermissions]


# -----------------------------
# Enrollment API
# -----------------------------
class EnrollmentViewSet(ModelViewSet):
    """
    Handles course enrollments.
    Students can enroll in courses.
    Instructors/Admins can view enrollments.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]  # Must be logged in

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
        """
        Automatically attach logged-in student.
        Prevents anonymous users from creating enrollments.
        """
        user = self.request.user
        if user.is_anonymous or not user.groups.filter(name="Student").exists():
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only authenticated students can enroll in courses.")

        serializer.save(student=user)

    # @action(detail=True, methods=["patch"])
    def update_progress(self, request, pk=None):
        """
        PATCH /enrollments/{id}/update_progress/
        Allows a student to update their progress in a course (0-100)
        """
        enrollment = self.get_object()

        # Only the student or admin can update progress
        user = request.user
        if user != enrollment.student and not (user.groups.filter(name="Admin").exists() or user.is_staff):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You cannot update progress for this enrollment.")

        progress = request.data.get("progress")
        try:
            progress = float(progress)
        except (ValueError, TypeError):
            return Response({"error": "Progress must be a number"}, status=status.HTTP_400_BAD_REQUEST)

        if not (0 <= progress <= 100):
            return Response({"error": "Progress must be between 0 and 100"}, status=status.HTTP_400_BAD_REQUEST)

        enrollment.progress = progress
        enrollment.save()
        return Response({"message": "Progress updated successfully"})