from django.contrib import admin
from .models import Department, Calender, Profile, MultipleFile, Meeting, ExpectedCalender
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.forms import UserChangeForm
from .import views as V
from datetime import datetime, timedelta
from django.http import request
from django.db import models, connection
from django.forms import CheckboxSelectMultiple
from django.contrib.admin.widgets import FilteredSelectMultiple
from .forms import AddressRadio, UploadMultiple
import requests
from  django import forms
# from django.db.models import F

# Register your models here.
admin.site.site_header = 'Quản trị'

# class JoinComponentInline(admin.TabularInline):
#     # model = JoinComponent
#     model = Calender.join_component.through
#     verbose_name_plural = 'Thành phần tham gia'
#     # extra = 1

# class PrepareUnitInline(admin.TabularInline):
#     model = PrepareUnit
#     verbose_name_plural = 'Đơn vị chuẩn bị'
#     # extra = 1


class FileInline(admin.TabularInline):
    model = MultipleFile
    extra = 0


class CalenderAdmin(admin.ModelAdmin):
    class Media:
        js = (
            "admin/js/date_change.js",
            "admin/switch-alert/sweetalert2.min.js",
        )
        css = {
            'all': (
                "admin/css/override.css", 
                "admin/sweetalert2/dist/sweetalert2.min.css"
            )
        }
    save_on_top = True
    inlines = [FileInline]
    # inlines = [JoinComponentInline, PrepareUnitInline]
    list_display = ('week', 'start_time', 'end_time', 'chair_unit')
    search_fields = ['week', 'start_time', 'end_time', 'chair_unit']
    # list_filter = ('join_component', 'prepare_unit')
    # filter_horizontal = ('join_component',)

    fieldsets = [
        ['Thông tin lịch', {
            'fields': ['start_time', 'end_time', ('location', 'address', ), 'chair_unit', 'join_quantity', 'content', ('requirement1', 'requirement2', 'requirement3'), ('requirement4', 'requirement5'), 'other_requirements', ('join_component', 'other_component'), ('prepare_unit', 'other_prepare')]
        }],
        # ('Thành phần', {
        #     'fields': ('join_component', 'other_component', 'prepare_unit',),
        # }),
    ]
    # formfield_overrides = {
    #     models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    # }
    editable_fields = []
    readonly_fields = ['get_user', 'get_department']
    exclude = ['week', 'status']

    change_list_template = "calender/index.html"

    """
    This method is used for user to select department
    """
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # user_id = request.user.pk
        # group = V.getGroupUserId(user_id)
        # group_list = [i['group_id'] for i in group]
        # if 3 not in group_list:
        #     if db_field.name == 'chair_unit':
        #         # print(request.user)
        #         depart_id = Profile.objects.filter(user_id=user_id)
        #         # print(depart_id[0].department_id)
        #         idd = depart_id[0].department_id if depart_id[0] else 1
        #         kwargs['queryset'] = Department.objects.filter(id=idd)
        # print('db_field.name: ', db_field.name)
        if db_field.name == 'chair_unit':
            kwargs['queryset'] = Department.objects.filter(active=True).order_by('group', 'sequence')
        return super(CalenderAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        # print('db_field.name: ', db_field.name)
        if db_field.name == 'join_component' or db_field.name == 'prepare_unit':
            kwargs['queryset'] = Department.objects.filter(active=True).order_by('group', 'sequence')
        return super(CalenderAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def get_user(self, instance):
        id_user = instance.create_uid.id if instance else 0
        # print('instance get_user: ', id_user)
        sql = "select last_name from auth_user where id = {}".format(id_user)
        user_name = V.connect_sql(sql)
        return user_name[0]['last_name'] if user_name else ''
    get_user.short_description = 'Người tạo'

    def get_department(self, instance):
        # print('instance: ', instance)
        id_dep = instance.create_depart_id_id if instance else 0
        # print('id_dep: ', id_dep)
        sql = "select name from calender_department where id = {}".format(id_dep if id_dep else 0)
        dep_name = V.connect_sql(sql)
        return dep_name[0]['name'] if dep_name else ''
    get_department.short_description = 'Phòng tạo'

    def has_add_permission(self, request): 
        return True

    def changelist_view(self, request, extra_context=None):
        # if request.method == "GET":
        #     status = request.GET['draft']
        #     print('status: ', status)
        date = datetime.now().strftime('%d-%m-%Y')
        data = V.start_end_of_week(date)
        #print(date)
        user_id = request.user.pk
        department = V.getDepartment(user_id)
        group = V.getGroupUserId(user_id)
        group_list = [i['group_id'] for i in group]
        # print('department: ', department)
        department_id = department[0]['department_id']
        week = V.convertNumberWeek(date)
        status = V.check_Calender(date, department_id)
        # print(status)
        #status = V.getCalenderStatus(department_id, week)
        # print('group_list: ', group_list)
        list_users = V.getlistusers(department_id)
        list_chair_unit = Department.objects.filter(active=True).order_by('group', 'sequence')
        # If user is the letter then display the calendar of her
        calender = V.get_calender_type(date, '0','approval')
        date_list = V.dateOfWeek_type(date, '0', 'approval')
        # print('date_list: ', date_list)
        # print('calender: ', calender)
        expected_list = V.expected_list(date)
        extra_context = {
            'title': 'CHƯƠNG TRÌNH LẬP LỊCH CÔNG TÁC TUẦN',
            'date': date,
            'week': week,
            'start': data['start'],
            'end': data['end'],
            'group': group,
            'group_list': group_list,
            'status': status,
            'list_chair_unit': list_chair_unit,
            'list_users': list_users,
            'date_list': date_list,
            'calender': calender,
            'expected_list': expected_list,
            'department_id': department_id
        }
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, extra_content=None):
        if 'get_user' not in self.fieldsets[0][1]['fields'] or 'get_department' not in self.fieldsets[0][1]['fields']:
            self.fieldsets[0][1]['fields'].append('get_user')
            self.fieldsets[0][1]['fields'].append('get_department')
        return super(CalenderAdmin, self).change_view(request, object_id)
        
    def convertNumberWeek(self, date):
        p = int(date.strftime("%V")) + 1
        return p

    def save_model(self, request, obj, form, change):
        # Updating calender
        if obj.pk is None:
            sql = "select department_id from calender_profile where user_id = %s"
            depart_id = V.connect_sql(sql, request.user.pk)
            if depart_id:
                obj.create_depart_id_id = depart_id[0]['department_id']
                obj.create_uid = request.user
        
            sql = "select group_id from auth_user_groups where user_id = %s"
            depart_level = V.connect_sql(sql, request.user.pk)

            if len(depart_level) > 0:
                for i in depart_level:
                    # Nếu trưởng phòng, văn thư tạo lịch thì cập nhật đã duyệt lịch mức phòng luôn
                    if i['group_id'] == 2 or i['group_id'] == 3:
                        obj.status = 'ACCEPT'
                        obj.check_calender = 1

            sql_comp = "select cd.id from calender_profile cp inner join calender_department cd on cp.department_id = cd.id where user_id = {} and ( cd.name like N'GĐPC%' or cd.name like N'%PGĐ KD%' or cd.name like N'%PGĐ KT%' or cd.name like N'%PGĐ ĐTXD%' )".format(request.user.pk)
            comp_level = V.connect_sql(sql_comp)

            # Nếu BGĐ nhập lịch thì chuyển duyệt ban hành.
            if len(comp_level) > 0:
                obj.status = 'DONE'
                obj.check_calender = 1
                obj.check_calender_letter = 1
        else:
            if obj.check_calender_letter == 1:
                sql = "select start_time, end_time, location_id, address from calender_calender where id = {}".format( obj.pk)
                # print(sql)
                time_adress_change = V.connect_sql(sql)
                default_start_time = time_adress_change[0]['start_time'].strftime('%Y-%m-%d %H:%M:%S')
                default_end_time = time_adress_change[0]['end_time'].strftime('%Y-%m-%d %H:%M:%S')
                start_time = obj.start_time.strftime('%Y-%m-%d %H:%M:%S')
                end_time = obj.end_time.strftime('%Y-%m-%d %H:%M:%S')
                if start_time != default_start_time or end_time != default_end_time:
                    obj.cancel_status = 6           # Change time
                    obj.write_date = datetime.now()
                    print("adminnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn")
                    insert_chat = "INSERT INTO QNaPC_ChangeToChat(id, id_pb, username, sended, send_time, cancel_status, write_date, user_edit)  VALUES (%s, NULL, NULL, 0, NULL, %s, %s, %s)"
                    V.execute_sql(insert_chat, obj.pk, obj.cancel_status, datetime.now(), request.user.pk)

                
                default_location = time_adress_change[0]['location_id']
                default_address = time_adress_change[0]['address']
                if default_location != obj.location_id or default_address != obj.address:
                    obj.cancel_status = 5           # Change address
                    obj.write_date = datetime.now()
                    insert_chat = "INSERT INTO QNaPC_ChangeToChat(id, id_pb, username, sended, send_time, cancel_status, write_date, user_edit)  VALUES (%s, NULL, NULL, 0, NULL, %s, %s, %s)"
                    V.execute_sql(insert_chat, obj.pk, obj.cancel_status, datetime.now(), request.user.pk)

        obj.week = self.convertNumberWeek(obj.start_time)
        super(CalenderAdmin, self).save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # if not request.user.is_superuser:
        #     return False
        user_id = request.user.pk
        department = V.getDepartment(user_id)
        department_id = department[0]['department_id']
        group = V.getGroupUserId(user_id)
        #print(group)
        # start = obj.start_time
        # print(start)
        # week = self.convertNumberWeek(start)
        #print(week)

        group_list = [i['group_id'] for i in group]
        if 3 in group_list:
            return False
            # if V.check_calender_letter(24, department_id) != "NEW": 
            #     return False
            # else:
            #     return True
        else:
            return True
    

# class DepartmentAdmin(admin.ModelAdmin):
#     inlines = (JoinComponentInline, PrepareUnitInline)


# class MyUserAdmin(UserAdmin):
#     # form = MyUserChangeForm
#     model = Person
#     # add_fieldsets = UserAdmin.add_fieldsets +  (
#     #     (None, { 'fields': ('depart', ) }),
#     # )
#     fieldsets = UserAdmin.fieldsets + (
#         (None, { 'fields': ('depart', ) }),
#     )

# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class EmployeeInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Phòng ban'
    fk_name = 'user'
    min_num = 1
    
# Define a new User admin
class MyUserAdmin(UserAdmin):
    class Meta:
        js = (
            "admin/js/remove_checkbox.js"
        )
    inlines = (EmployeeInline,)
    list_display = ['username', 'email', 'last_name', 'is_active', 'get_groups', 'get_department', 'last_login']
    list_select_related = ('profile', )
    
    def get_department(self, instance):
        return instance.profile.department
    get_department.short_description = 'Phòng ban'   

    def get_groups(self, obj):
        return ", ".join([p.name for p in obj.groups.all()])
    get_groups.short_description = 'Nhóm'   

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(MyUserAdmin, self).get_inline_instances(request, obj)


class MyGroupAdmin(GroupAdmin):
    def has_delete_permission(self, request, obj=None):
        return False

# class MyAdminSite(AdminSite):
#     # Disable View on Site link on admin page
#     site_url = None
    
class DepartmentAdmin(admin.ModelAdmin):
    ordering = ['group', 'sequence']
    list_display = ('name', 'group', 'sequence', 'active', 'note')
    search_fields = ('name', 'group', 'sequence', 'active', 'note')
    list_filter = ('name', 'group', 'sequence', 'active', 'note')
    actions = ('change_status_active', )

    def change_status_active(modeladmin, request, queryset):
        # print(request)
        # print(queryset)
        selected = queryset.values_list('pk', flat=True)
        # print(selected)
        for i in selected:
            active = Department.objects.get(id = i).active
            Department.objects.filter(id = i).update(active= not active)
    change_status_active.short_description = 'Đổi trạng thái'

class MeetingAdmin(admin.ModelAdmin):
    ordering = ['group', 'sequence']
    list_display = ('name', 'group', 'sequence', 'note')
    search_fields = ('name', 'group', 'sequence', 'note')
    list_filter = ('name', 'group', 'sequence', 'note')


class ExpectedAdmin(admin.ModelAdmin):
    ordering = ['week']
    list_display = ('week', 'content', 'create_uid', 'create_date')
    search_fields = ('week', 'content', )
    list_filter = ('week', 'content', )
    exclude = ('create_uid', 'write_uid', )

    def save_model(self, request, obj, form, change):
        obj.create_uid = request.user
        # obj.write_date = datetime.now()
        super(ExpectedAdmin, self).save_model(request, obj, form, change)

admin.site.register(ExpectedCalender, ExpectedAdmin)


admin.site.register(Department, DepartmentAdmin)
admin.site.register(Meeting, MeetingAdmin)

admin.site.register(Calender, CalenderAdmin)

admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)

admin.site.unregister(Group)
admin.site.register(Group, MyGroupAdmin)

admin.site.site_url = None