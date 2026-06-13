import django_filters    # pip install django_filter and add in settings(installed app) before creating this file
from django.db.models import Q
from .models import *

class StudentFilter(django_filters.FilterSet):
    search=django_filters.CharFilter(method='multi_search',label="search")    # why we defined search means, it is customizable(charFilter),dropdown filter is in built 
    class Meta:
        model=Student
        fields=['Department']  #for dropdown search

    def multi_search(self,queryset,name,value):
        return queryset.filter(
            Q(Fullname__icontains=value) |      # Q is used  for handle logics (or,and), | - bitwise OR
            Q(Email__icontains=value) |
            Q(Roll_no__icontains=value) 

        )
    
class LogsFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='multi_search', label="Search")

    class Meta:
        model = AttendanceSession
        fields = {
            'student__Department': ['exact'],
            'student__Year': ['exact'],
            'date': ['exact'],
        }

    def multi_search(self, queryset, name, value):
        return queryset.filter(
            Q(student__Fullname__icontains=value) |
            Q(student__Email__icontains=value) |
            Q(student__Roll_no__icontains=value)
        )






