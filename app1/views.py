from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import Course
from .Serializer import CourseSerializer
from rest_framework.exceptions import APIException
from .ai import generate_course_description
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
