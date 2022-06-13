from django.contrib import admin
from django.forms import ModelForm
from vehicle.models import *
from vehicle.views import sql_calender_detail, date_of_week
from datetime import datetime
from calender.models import *
from django.http import HttpResponse
from calender.views import start_end_of_week, getDepartment, convertNumberWeek, getGroupUserId,\
getDepartmentUserId, getlistusers, execute_sql
from django.urls import path
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.core.exceptions import ValidationError

# Register your models here.

class VehicleTypeAdmin(admin.ModelAdmin):
    ordering = ['name', 'is_left_tab']
    list_display = ('name', 'is_left_tab', 'note')
    search_fields = ('name', 'is_left_tab', 'note')
    list_filter = ('name', 'is_left_tab', 'note')
    fieldsets = [
        ['Thông tin loại xe', {
            'fields': ['name', 'is_left_tab', 'note']
        }],
    ]

    def has_view_permission(self, request, obj=None): 
        if request.user.has_perm("vehicle.manage_vehicle"):
            return True
        else:
            return False

    def has_add_permission(self, request): 
        # has_permision(request, PERM_CODE)
        if request.user.has_perm("vehicle.manage_vehicle"):
            return True
        else:
            return False

    def has_change_permission(self, request, obj=None): 
        if request.user.has_perm("vehicle.manage_vehicle"):
            return True
        else:
            return False

    def has_delete_permission(self, request, obj=None): 
        if request.user.has_perm("vehicle.manage_vehicle"):
            return True
        else:
            return False

    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.create_uid = request.user
        else:
            obj.write_date = datetime.now()
            obj.write_uid = request.user
        super(VehicleTypeAdmin, self).save_model(request, obj, form, change)


class VehicleAdmin(admin.ModelAdmin):
    class Media:
        js = (
            "admin/js/vehicle_type_change.js",
        )
        # css = {
        #     'all': (
        #         "admin/css/vehicle_form.css",
        #     )
        # }
    ordering = ['name', 'manage_unit']
    list_display = ('name', 'number', 'frame_number', 'machine_number', 'fuel', 'fuel_type', 'fuel_rate', 'crane_fuel_rate', 'generator_firing_fuel_rate', 'manage_unit', 'vehicle_type')
    # Search foreignkey fields is error
    search_fields = ('name', 'number', 'frame_number', 'machine_number', 'fuel', 'fuel_type__name', 'fuel_rate__name', 'manage_unit__name', 'vehicle_type__name')
    list_filter = ('name', 'number', 'frame_number', 'machine_number', 'fuel_rate', 'crane_fuel_rate', 'generator_firing_fuel_rate', 'fuel', 'fuel_type', 'manage_unit', 'vehicle_type__name')
    fieldsets = [
        ['Thông tin xe', {
            'fields': ['name', 'number', 'frame_number', 'machine_number', 'fuel', 'fuel_type', 'fuel_rate', 'crane_fuel_rate', 'generator_firing_fuel_rate', 'manage_unit', 'vehicle_type', 'note']
        }],
    ]
    
    readonly_fields = ()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['fuel_type'].queryset = FuelType.objects.filter(active=True)

    def has_view_permission(self, request, obj=None): 
        # opts = self.opts
        # print(opts)
        # print(request.__dict__.keys())
        # print(request.user.has_perm("vehicle.manage_vehicle"))
        if request.user.has_perm("vehicle.manage_vehicle"):
            return True
        else:
            return False

    def has_add_permission(self, request): 
        # has_permision(request, PERM_CODE)
        if request.user.has_perm("vehicle.manage_vehicle"):
            return True
        else:
            return False

    def has_change_permission(self, request, obj=None): 
        if request.user.has_perm("vehicle.manage_vehicle"):
            return True
        else:
            return False

    def has_delete_permission(self, request, obj=None): 
        if request.user.has_perm("vehicle.manage_vehicle"):
            return True
        else:
            return False

    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.create_uid = request.user
        else:
            obj.write_date = datetime.now()
            obj.write_uid = request.user
        super(VehicleAdmin, self).save_model(request, obj, form, change)

    def changeform_view(self, request, *args, **kwargs):
        # Access right for fuel_rate field
        self.readonly_fields = list(self.readonly_fields)
        if not request.user.has_perm("vehicle.change_fuel_rate"):
            self.readonly_fields.append('fuel_rate')
        
        return super(VehicleAdmin, self).changeform_view(request, *args, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        
        form = super(VehicleAdmin, self).get_form(request, obj=None, **kwargs)
        form.base_fields['fuel_type'].queryset = FuelType.objects.filter(active=True)
        return form


class VehicleCalenderAdmin(admin.ModelAdmin):
    list_display = ('week', 'start_time', 'end_time', 'departure')
    search_fields = ['week', 'start_time', 'end_time', 'departure']

    change_list_template = "vehicle/index.html"

    # Must be have change perm then menu will be appear "Lịch xe"
    def has_change_permission(self, request, obj=None): 
        return True

    def changelist_view(self, request, extra_context=None):
        cur_date = datetime.now().strftime('%d-%m-%Y')
        data = start_end_of_week(cur_date)

        user_id = request.user.pk
        department = getDepartment(user_id)
        department_id = department[0]['department_id'] if len(department) > 0 else 0
        groups = getGroupUserId(user_id)
        user_group_list = [i['group_id'] for i in groups]

        getDepart = getDepartmentUserId(user_id)
        list_users = getlistusers(getDepart[0]['department_id'])
        
        week = convertNumberWeek(cur_date)
        status_list = VehicleCalender.STATUS
        register_unit_list = Department.objects.filter(active=True, is_vehicle_calender=True).order_by('group', 'sequence')

        has_perm_driver = request.user.has_perm("vehicle.driver_vehicle")
        
        calender_list = sql_calender_detail(cur_date, "0", True, "ASSIGNED", has_perm_driver, user_id)
        date_list = date_of_week(cur_date, "0", True, "ASSIGNED")
        # =================TAB TO THE RIGHT=================
        calender_list_right = sql_calender_detail(cur_date, "0", False, "ASSIGNED", has_perm_driver, user_id)
        date_list_right = date_of_week(cur_date, "0", False, "ASSIGNED")
        # ============================PERMISIONS=============================
        has_perm_add = request.user.has_perm("vehicle.register_vehicle")
        has_perm_confirm = request.user.has_perm("vehicle.confirm_vehicle")
        has_perm_approval = request.user.has_perm("vehicle.approval_vehicle")
        has_perm_assign = request.user.has_perm("vehicle.assign_vehicle")

        context = {
            'tab_active': "left",
            'date': cur_date,
            'date_right': cur_date,
            'start': data['start'],
            'end': data['end'],
            'start_right': data['start'],
            'end_right': data['end'],
            'week': week,
            'week_right': week,
            'status_id': "ASSIGNED",
            'status_id_right': "ASSIGNED",
            'unit_id': "0",
            'unit_id_right': "0",
            'register_unit_list': register_unit_list,
            'status_list': status_list,
            'date_list': date_list,
            'date_list_right': date_list_right,
            'calender_list': calender_list,
            'calender_list_right': calender_list_right,
            'user_group_list': user_group_list,
            'has_perm_add': has_perm_add,
            'has_perm_confirm': has_perm_confirm,
            'has_perm_approval': has_perm_approval,
            'has_perm_assign': has_perm_assign,
            'list_users': list_users
        }
        # print(context)
        # return HttpResponse(context)
        return super().changelist_view(request, extra_context=context)


class FuelRateAdmin(admin.ModelAdmin):
    ordering = ['name']
    list_display = ('name', 'active')
    search_fields = ('name', 'active', 'create_date')
    list_filter = ('name', 'active', 'create_date')
    fieldsets = [
        ['Thông tin loại xe', {
            'fields': ['name', 'active']
        }],
    ]

    def has_view_permission(self, request, obj=None): 
        return True

    def has_add_permission(self, request): 
        # has_permision(request, PERM_CODE)
        if request.user.has_perm("vehicle.change_fuel_rate"):
            return True
        else:
            return False

    def has_change_permission(self, request, obj=None): 
        if request.user.has_perm("vehicle.change_fuel_rate"):
            return True
        else:
            return False

    def has_delete_permission(self, request, obj=None): 
        if request.user.has_perm("vehicle.change_fuel_rate"):
            return True
        else:
            return False

    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.create_uid = request.user
        else:
            obj.write_date = datetime.now()
            obj.write_uid = request.user
        super(FuelRateAdmin, self).save_model(request, obj, form, change)


class FuelTypeAdminForm(ModelForm):
    class Meta:
        model = FuelType
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time == end_time:
            raise ValidationError('invalid!')
        return cleaned_data


class FuelTypeAdmin(admin.ModelAdmin):
    form = FuelTypeAdminForm

    ordering = ['name']
    list_display = ('name', 'price', 'start_time', 'end_time', 'is_track', 'active')
    search_fields = ('name', 'price', 'start_time', 'end_time', 'is_track', 'active')
    list_filter = ('name', 'price', 'start_time', 'end_time', 'is_track', 'active')
    fieldsets = [
        ['Thông tin loại nhiên liệu', {
            'fields': ['name', 'price', 'start_time', 'end_time', 'is_track', 'active']
        }],
    ]

    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.create_uid = request.user
        else:
            if obj.is_track and 'price' in form.changed_data and \
                    'start_time' in form.changed_data and 'end_time' in form.changed_data:
                old_data = FuelType.objects.get(id=obj.id)
                self.save_old_record(old_data, request.user)
                # generate data in medium table m2m
                # vehicles = Vehicle.objects.filter(fuel_type=obj.id)
                # for item in vehicles:
                #     sql = "INSERT INTO vehicle_fuel_type_rel(vehicle_id, fueltype_id) VALUES (%s, %s)" % (item.id, obj.id)
                #     execute_sql(sql)
            obj.write_date = datetime.now()
            obj.write_uid = request.user
        super(FuelTypeAdmin, self).save_model(request, obj, form, change)

    def save_old_record(self, data, uid):
        old_record = FuelType(name=data.name, 
                              price=data.price, 
                              start_time=data.start_time, 
                              end_time=data.end_time, 
                              active=False,
                              is_track=True,
                              create_uid=uid,
                              write_uid=data.write_uid,
                              create_date=data.create_date,
                              write_date=datetime.now()
                        )
        old_record.save()
    
    def changelist_view(self, request, extra_context=None):
        default_filter = False
        try:
            referrer = request.META.get('HTTP_REFERER', '')

            if '?' not in referrer:
                default_filter = True
        except:
            default_filter = True

        if default_filter:
            q = request.GET.copy()
            q['active__exact'] = '1'
            request.GET = q
            request.META['QUERY_STRING'] = request.GET.urlencode()
        return super().changelist_view(request, extra_context=extra_context)


admin.site.register(VehicleType, VehicleTypeAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(VehicleCalender, VehicleCalenderAdmin)
admin.site.register(FuelRate, FuelRateAdmin)
admin.site.register(FuelType, FuelTypeAdmin)