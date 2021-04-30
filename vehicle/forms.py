from django import forms
from django.contrib.auth.models import User
from django.contrib.admin.widgets import AdminSplitDateTime
from .models import VehicleCalender, VehicleType, Vehicle
from calender.models import Department, Profile
from django.core.exceptions import ValidationError

class CalenderUpdateDetailForm(forms.ModelForm):
    start_time = forms.SplitDateTimeField(label='Thời gian bắt đầu')
    end_time = forms.SplitDateTimeField(label='Thời gian kết thúc')
    
    class Meta:
        model = VehicleCalender
        # fields = "__all__"
        fields = ['start_time', 'end_time', 'departure', 'destination', 'expected_km', 'expected_crane_hour', 'seat_number', 'vehicle_type', 'content', 'status', 'note', 'approved_by']
        # localized_fields = ('start_time',)

    def __init__(self, *args, **kwargs):
        super(CalenderUpdateDetailForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].widget = AdminSplitDateTime()
        self.fields['end_time'].widget = AdminSplitDateTime()
        self.fields['vehicle_type'].queryset = VehicleType.objects.filter().order_by('-is_left_tab')
        self.fields['approved_by'].required = False
        # self.fields['register'].queryset = User.objects.filter()
        # self.fields['register_unit'].queryset = Department.objects.filter(active=True, is_vehicle_calender=True).order_by('group', 'sequence')


class CalenderAddForm(forms.ModelForm):
    start_time = forms.SplitDateTimeField(label='Thời gian bắt đầu')
    end_time = forms.SplitDateTimeField(label='Thời gian kết thúc')
    approved_by_ = forms.ModelChoiceField(label='Người duyệt', queryset=Profile.objects.filter(is_manager=True), required=False)
    # approved_by_ = forms.ModelChoiceField(label='Người duyệt', queryset=Profile.objects.filter(is_manager=True).values_list('user__last_name', flat=True), required=False)
    # approved_by_ = forms.ModelChoiceField(label='Người duyệt', queryset=Profile.objects.raw("SELECT au.last_name FROM auth_user au INNER JOIN calender_profile cp ON au.id = cp.user_id WHERE cp.is_manager = 1"), required=False)
    
    class Meta:
        model = VehicleCalender
        fields = ['start_time', 'end_time', 'departure', 'destination', 'expected_km', 'expected_crane_hour', 'seat_number', 'vehicle_type', 'content', 'note', 'is_appr_manager', 'approved_by_']

    def __init__(self, *args, **kwargs):
        super(CalenderAddForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].widget = AdminSplitDateTime()
        self.fields['end_time'].widget = AdminSplitDateTime()
        self.fields['vehicle_type'].queryset = VehicleType.objects.filter().order_by('-is_left_tab')
        # self.fields['managers'].queryset = User.objects.all()

    def clean(self):
        cleaned_data = super(CalenderAddForm, self).clean()
        if cleaned_data['is_appr_manager'] and cleaned_data['approved_by_'] is None:
            raise ValidationError("Vui lòng chọn người duyệt lịch")

class CalenderDisableForm(forms.Form):
    register = forms.CharField(label='Người đăng ký', disabled=True)
    register_unit = forms.CharField(label='Đơn vị đăng ký', disabled=True)
    approved_by = forms.CharField(label='Người duyệt', disabled=True, required=False)
    
    fields = "__all__"