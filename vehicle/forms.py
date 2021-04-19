from django import forms
from django.contrib.auth.models import User
from django.contrib.admin.widgets import AdminSplitDateTime
from .models import VehicleCalender, VehicleType, Vehicle
from calender.models import Department

class CalenderUpdateDetailForm(forms.ModelForm):
    start_time = forms.SplitDateTimeField(label='Thời gian bắt đầu')
    end_time = forms.SplitDateTimeField(label='Thời gian kết thúc')
    
    class Meta:
        model = VehicleCalender
        # fields = "__all__"
        fields = ['start_time', 'end_time', 'departure', 'destination', 'expected_km', 'expected_crane_hour', 'seat_number', 'vehicle_type', 'content', 'status', 'note',]
        # localized_fields = ('start_time',)

    def __init__(self, *args, **kwargs):
        super(CalenderUpdateDetailForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].widget = AdminSplitDateTime()
        self.fields['end_time'].widget = AdminSplitDateTime()
        self.fields['vehicle_type'].queryset = VehicleType.objects.filter().order_by('-is_left_tab')
        # self.fields['register'].queryset = User.objects.filter()
        # self.fields['register_unit'].queryset = Department.objects.filter(active=True, is_vehicle_calender=True).order_by('group', 'sequence')


class CalenderAddForm(forms.ModelForm):
    start_time = forms.SplitDateTimeField(label='Thời gian bắt đầu')
    end_time = forms.SplitDateTimeField(label='Thời gian kết thúc')
    
    class Meta:
        model = VehicleCalender
        fields = ['start_time', 'end_time', 'departure', 'destination', 'expected_km', 'expected_crane_hour', 'seat_number', 'vehicle_type', 'content', 'note',]

    def __init__(self, *args, **kwargs):
        super(CalenderAddForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].widget = AdminSplitDateTime()
        self.fields['end_time'].widget = AdminSplitDateTime()
        self.fields['vehicle_type'].queryset = VehicleType.objects.filter().order_by('-is_left_tab')

class CalenderDisableForm(forms.Form):
    register = forms.CharField(label='Người đăng ký', disabled=True)
    register_unit = forms.CharField(label='Đơn vị đăng ký', disabled=True)
    fields = "__all__"