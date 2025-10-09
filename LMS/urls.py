"""
URL configuration for LMS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app1.views import CourseViewSet, EnrollmentViewSet, UserViewSet, GroupApiViewSet, AssessmentViewSet, SubmissionViewSet, SponsorProfileViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r"courses", CourseViewSet, basename='course')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r"assessments", AssessmentViewSet, basename='assessment')
router.register(r"submissions", SubmissionViewSet, basename='submission')
router.register(r"sponsor-profiles", SponsorProfileViewSet, basename='sponsorprofile')


urlpatterns = [
    path('admin/', admin.site.urls),
    path("register/", UserViewSet.as_view({"post": "register"})),
    path("login/", UserViewSet.as_view({"post": "login"})),
    path("groups/", GroupApiViewSet.as_view({"get": "list"})),
#    path("enrollments/<int:pk>/update_progress/", EnrollmentViewSet.as_view({"patch": "update_progress"})),

]+ router.urls
