from django.urls import path
from .views import AdminAnalyticsView, SponsorDashboardViewSet

urlpatterns = [
    path("admin/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("sponsor/", SponsorDashboardViewSet.as_view({'get': 'dashboard'}), name="sponsor-dashboard"),
]
