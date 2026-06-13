from django import forms
from .models import Department,Student,CollegeYear

class Department_Form(forms.ModelForm):
    class Meta:
        model=Department
        fields='__all__'
    
    def __init__(self,*args,**kwargs):
        super(Department_Form,self).__init__(*args,**kwargs)




class Student_Form(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ['photo']
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove duplicate Year labels but keep objects intact
        seen = set()
        unique_years = []
        for year in CollegeYear.objects.all().order_by('Year'):
            if year.Year not in seen:
                seen.add(year.Year)
                unique_years.append(year.id)
        self.fields['Year'].queryset = CollegeYear.objects.filter(id__in=unique_years)



class StudentLoginForm(forms.Form):
    username = forms.CharField(label='Full Name', max_length=200)
    roll_no = forms.CharField(label='Roll Number', max_length=100)



