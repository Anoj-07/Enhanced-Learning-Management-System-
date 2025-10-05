from rest_framework import serializers
from .models import Course, Enrollment
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['created_at']


class EnrollmentSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(source="student.username", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "student_username",
            "course",
            "course_name",
            "progress",
            "enrolled_at",
        ]
        read_only_fields = ["enrolled_at", "student"]

    def create(self, validated_data):
        """
        Automatically sets the student to the logged-in user.
        Prevents duplicate enrollments.
        """
        request = self.context.get("request")
        user = request.user
        course = validated_data["course"]

        # Check if already enrolled
        if Enrollment.objects.filter(student=user, course=course).exists():
            raise serializers.ValidationError("You are already enrolled in this course.")

        enrollment = Enrollment.objects.create(student=user, **validated_data)
        return enrollment


# Login and Register
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'groups', 'email', 'first_name', 'last_name']

    def create(self, validated_data):
        raw_password = validated_data.pop('password') # remove and assigned password key and value which user sent and validated
        hash_password = make_password(raw_password) # hasing user's password using make_password function
        validated_data['password'] = hash_password # Assigning hashed password as a validated data
        return super().create(validated_data) # Passing the validated data to the parent class's create method to save the user instance

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']
