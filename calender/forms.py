from django import forms
from .models import Calender, Department, MultipleFile, CalendarContent, Profile
from django.contrib.admin.widgets import AdminSplitDateTime, RelatedFieldWidgetWrapper
from django.forms import inlineformset_factory, modelformset_factory
from django.contrib.admin import site as admin_site

ADDRESS = [
    (1, 'Phòng họp thuộc cơ quan đơn vị'),
    (2, 'Nơi khác'),
]

class CalenderForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CalenderForm, self).__init__(*args, **kwargs)
        self.fields["start_time"].widget = DateTimeInput()
        self.fields['prepare_unit'].queryset = Department.objects.all()

    start_time = forms.DateTimeField()
    prepare_unit = forms.ModelChoiceField(queryset=Department.objects.all())


class DateTimeInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kwargs):
        kwargs["format"] = "%Y/%m/%dT%H:%M"
        super().__init__(**kwargs)


class DisableForm(forms.Form):
    creater = forms.CharField(label='Người tạo', disabled=True)
    department = forms.CharField(label='Phòng tạo', disabled=True)
    fields = "__all__"


class ExpectedForm(forms.Form):
    week = forms.IntegerField(label='Tuần', min_value=1)
    content = forms.CharField(label='Nội dung', widget=forms.Textarea)
    fields = "__all__"

class FileForm(forms.ModelForm):
    class Meta:
        model = MultipleFile
        fields = "__all__"

class CalenderChangeForm(forms.ModelForm):
    start_time = forms.SplitDateTimeField(label='Thời gian bắt đầu')
    end_time = forms.SplitDateTimeField(label='Thời gian kết thúc')
    
    class Meta:
        model = Calender
        # fields = "__all__"
        fields = ['start_time', 'end_time', 'address', 'chair_unit', 'join_quantity', 'content_ids', 'content', 'requirement1', 'requirement2', 'requirement3', 'requirement4', 'requirement5', 'other_requirements', 'join_component', 'other_component', 'prepare_unit', 'other_prepare']
        # localized_fields = ('start_time',)

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id', None)
        super(CalenderChangeForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].widget = AdminSplitDateTime()
        self.fields['end_time'].widget = AdminSplitDateTime()
        self.fields['content_ids'].queryset = CalendarContent.objects.filter(active=True)
        if self.user_id:
            profile = Profile.objects.get(user=self.user_id)
            if profile.department:
                depart_id = profile.department.id
                self.fields['join_component'].queryset = Department.objects.filter(parent=depart_id)
                self.fields['prepare_unit'].queryset = Department.objects.filter(parent=depart_id)
            
        # self.fields["start_time"].widget = DateTimeInput()
        # self.fields["start_time"].input_formats = ["%Y/%m/%dT%H:%M", "%Y/%m/%d %H:%M"]
        # self.fields["end_time"].widget = DateTimeInput()
        # self.fields["end_time"].input_formats = ["%d-%m-%YT%H:%M", "%d-%m-%Y %H:%M"]

    def clean(self):
        cleaned_data = super(CalenderChangeForm, self).clean()
        # name = cleaned_data.get('name')
        # print('CLEAN DATA: ', cleaned_data)
        # print('CLEAN DATA count: ', len(cleaned_data))
        if len(cleaned_data) <= 14:
            raise forms.ValidationError('Vui lòng nhập đầy đủ thông tin!')
        return cleaned_data
    
    # def save(self, force_update=True):
    #     resp = super().save(force_update=True)
    #     print("saveee")
    #     return resp

        
CalenderFormSet = modelformset_factory(Calender, form=CalenderChangeForm, fields=('start_time', 'end_time', 'location', 'address', 'chair_unit', 'join_quantity', 'content', 'requirement1', 'requirement2', 'requirement3', 'requirement4', 'requirement5', 'other_requirements', 'join_component', 'other_component', 'prepare_unit', 'other_prepare',), extra=0)
FileFormSet = inlineformset_factory(Calender, MultipleFile, fields=('files',), can_delete=True, extra=1, max_num=5)


class AddressRadio(forms.ModelForm):
    addresses = forms.ChoiceField(label='Địa điểm', choices=ADDRESS, widget=forms.RadioSelect())
    class Meta:
        model = Calender
        fields = ['address',]
    def save(self, *args, **kwargs):
        if self.cleaned_data['addresses']:
            pass
            # do something with your extra fields,
            # remove values from other fields, etc.
        super(AddressRadio, self).save(*args, **kwargs)


class UploadMultiple(forms.ModelForm):
    # file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    class Meta:
        model = MultipleFile
        fields = ['files']
        widgets = {
            'files': forms.ClearableFileInput(attrs={'multiple': True}),
        }