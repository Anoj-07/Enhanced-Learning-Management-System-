from rest_framework import serializers
from .models import Course, Enrollment, Assessment, Submission, SponsorProfile, Sponsorship, Transaction, Notification
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password



# Course Serializer ------------------------------------------------
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ['created_at']

# Enrollment Serializer ------------------------------------------------
class EnrollmentSerializer(serializers.ModelSerializer):
    student_first_name = serializers.CharField(source="student.first_name", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "student_first_name",
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

        # Prevent duplicate enrollments
        if Enrollment.objects.filter(student=user, course=course).exists():
            raise serializers.ValidationError("You are already enrolled in this course.")

        enrollment = Enrollment.objects.create(**validated_data)
        return enrollment


# Login and Register -------------------------------------------------
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

# for Group model ------------------------------------------------
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


# for Assessment model ------------------------------------------------
class AssessmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Assessment model.
    Adds read-only course name for easier API responses.
    """
   
    course_name = serializers.CharField(source="course.name", read_only=True)

    class Meta:
        model = Assessment
        fields = ["id", "course", "course_name", "title", "description", "due_date"]
        read_only_fields = ["id", "course_name"]

# for Submission model ------------------------------------------------
class SubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.first_name", read_only=True)
    assessment_title = serializers.CharField(source="assessment.title", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "assessment",
            "assessment_title",
            "student",
            "student_name",
            "submitted_file",
            "submitted_at",
            "grade",
        ]
        read_only_fields = ["submitted_at", "student", "grade"]

    def create(self, validated_data):
        """
        Automatically assign the logged-in user as the student.
        """
        request = self.context.get("request")
        user = request.user

        validated_data["student"] = user
        return super().create(validated_data)

# SponsorProfile Serializer ------------------------------------------------
class SponsorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for SponsorProfile model.
    Handles sponsor-specific data such as organization name and total funds.
    """

    sponsor_username = serializers.CharField(source="sponsor.username", read_only=True)
    sponsor_email = serializers.CharField(source="sponsor.email", read_only=True)

    class Meta:
        model = SponsorProfile
        fields = [
            "id",
            "sponsor",
            "sponsor_username",
            "sponsor_email",
            "organization_name",
            "total_funds",
        ]
        read_only_fields = ["sponsor"]

    def create(self, validated_data):
        """
        Automatically link the logged-in sponsor to their profile.
        Prevents duplicate profiles.
        """
        validated_data.pop('sponsor', None)
        user = self.context['request'].user
        profile = SponsorProfile.objects.create(sponsor=user, **validated_data)
        return profile
    

# Sponsorship Serializer ------------------------------------------------
class SponsorshipSerializer(serializers.ModelSerializer):
    """
    Serializer for Sponsorship model.
    Automatically attaches sponsor based on the logged-in user.
    Prevents other roles from creating sponsorships.
    """
    sponsor_name = serializers.CharField(source="sponsor.sponsor.username", read_only=True)
    student_name = serializers.CharField(source="student.username", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)

    class Meta:
        model = Sponsorship
        fields = [
            "id",
            "sponsor",          # sponsor profile object (read-only)
            "sponsor_name",     # username of sponsor
            "student",          # student being sponsored
            "student_name",     # username of student
            "course",           # optional course
            "course_name",      # name of the course
            "amount",           # sponsorship amount
            "created_at",       # timestamp
        ]
        read_only_fields = [
            "created_at",
            "sponsor",
            "sponsor_name",
            "student_name",
            "course_name"
        ]

    def create(self, validated_data):
        """
        Automatically link the sponsor to the logged-in user.
        Ensures only sponsors can create sponsorships.
        """
        request = self.context.get("request")
        user = request.user

        # ✅ Only sponsors can create sponsorships
        if not user.groups.filter(name="Sponsor").exists():
            raise serializers.ValidationError("Only sponsors can create sponsorships.")

        # ✅ Get sponsor profile
        sponsor_profile = getattr(user, "sponsor_profile", None)
        if sponsor_profile is None:
            raise serializers.ValidationError("Sponsor profile not found for this user.")

        # ✅ Attach sponsor automatically
        validated_data["sponsor"] = sponsor_profile

        return super().create(validated_data)


