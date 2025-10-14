import django_filters
from .models import Sponsorship, Enrollment
from django.db import models

class SponsorshipFilter(django_filters.FilterSet):
    # Custom progress filter
    progress__gte = django_filters.NumberFilter(method='filter_progress_gte')
    progress__lte = django_filters.NumberFilter(method='filter_progress_lte')
    progress = django_filters.NumberFilter(method='filter_progress_exact')

    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    student = django_filters.CharFilter(field_name="student__username", lookup_expr="icontains")
    course = django_filters.CharFilter(field_name="course__name", lookup_expr="icontains")

    class Meta:
        model = Sponsorship
        fields = ["status", "student", "course"]

    def filter_progress_exact(self, queryset, name, value):
        return queryset.filter(
            student__enrollments__course=models.F("course"),
            student__enrollments__progress=value
        )

    def filter_progress_gte(self, queryset, name, value):
        return queryset.filter(
            student__enrollments__course=models.F("course"),
            student__enrollments__progress__gte=value
        )

    def filter_progress_lte(self, queryset, name, value):
        return queryset.filter(
            student__enrollments__course=models.F("course"),
            student__enrollments__progress__lte=value
        )
