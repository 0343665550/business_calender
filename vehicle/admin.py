from django.contrib import admin
from vehicle.models import *
from vehicle.views import sql_calender_detail, date_of_week
from datetime import datetime
from calender.models import *
from django.http import HttpResponse
from calender.views import start_end_of_week, getDepartment, convertNumberWeek, getGroupUserId

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
    ordering = ['name', 'manage_unit']
    list_display = ('name', 'number', 'frame_number', 'machine_number', 'fuel', 'manage_unit', 'vehicle_type')
    # Search foreignkey fields is error
    search_fields = ('name', 'number', 'frame_number', 'machine_number', 'fuel', 'manage_unit__name', 'vehicle_type__name')
    list_filter = ('name', 'number', 'frame_number', 'machine_number', 'fuel', 'manage_unit', 'vehicle_type__name')
    fieldsets = [
        ['Thông tin xe', {
            'fields': ['name', 'number', 'frame_number', 'machine_number', 'fuel', 'manage_unit', 'vehicle_type', 'note']
        }],
    ]

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
        
        week = convertNumberWeek(cur_date)
        status_list = VehicleCalender.STATUS
        register_unit_list = Department.objects.filter(active=True, is_vehicle_calender=True).order_by('group', 'sequence')
        calender_list = sql_calender_detail(cur_date, "0", True, "ASSIGNED")
        date_list = date_of_week(cur_date, "0", True, "ASSIGNED")
        # =================TAB TO THE RIGHT=================
        calender_list_right = sql_calender_detail(cur_date, "0", False, "ASSIGNED")
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
            'has_perm_assign': has_perm_assign
        }
        # print(context)
        # return HttpResponse(context)
        return super().changelist_view(request, extra_context=context)


admin.site.register(VehicleType, VehicleTypeAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(VehicleCalender, VehicleCalenderAdmin)