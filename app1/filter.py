import django_filters
from .models import Enrollment

class SponsorStudentFilter(django_filters.FilterSet):
    progress__gte = django_filters.NumberFilter(field_name='progress', lookup_expr='gte')
    progress__lte = django_filters.NumberFilter(field_name='progress', lookup_expr='lte')
    student__first_name = django_filters.CharFilter(field_name='student__first_name', lookup_expr='icontains')
    course__title = django_filters.CharFilter(field_name='course__title', lookup_expr='icontains')

    class Meta:
        model = Enrollment
        fields = ['progress__gte', 'progress__lte', 'student__first_name', 'course__title']
