from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, User, AbstractUser
)
from django.utils.translation import gettext_lazy as _
import os
from django.conf import settings
from django.core.exceptions import ValidationError
from . import connect_sql as query
from datetime import datetime, timedelta

# Create your models here.
class Department(models.Model):
    DEPARTMENT_UNIT = [
        ('IN', 'Trong cơ quan'),
        ('OUT', 'Ngoài cơ quan')
    ]
    name = models.CharField('Tên phòng ban', max_length=255, unique=True)
    group = models.CharField(
        'Đơn vị',
        max_length=3,
        choices=DEPARTMENT_UNIT,
        default='IN')
    sequence = models.IntegerField(
        'Thứ tự',
        default=0
    )
    is_vehicle_calender = models.BooleanField("Lịch xe", default=False)
    # parent = models.ForeignKey('self', verbose_name="Trực thuộc phòng", on_delete=models.CASCADE, null=True, blank=True)
    note = models.TextField('Ghi chú', null = True, blank=True)
    active = models.BooleanField('Kích hoạt', default=True)

    class Meta:
        verbose_name = _('Phòng ban')
        verbose_name_plural = _('Phòng ban')

    def __str__(self):
        return "%s" % (self.name, )
        #return "%s - %s" % (self.name, self.group)


class Meeting(models.Model):
    MEETING_UNIT = [
        ('IN', 'Trong cơ quan'),
        ('OUT', 'Ngoài cơ quan')
    ]
    name = models.CharField('Tên phòng họp', max_length=255, unique=True)
    group = models.CharField(
        'Đơn vị',
        max_length=3,
        choices=MEETING_UNIT,
        default='IN')
    sequence = models.IntegerField(
        'Thứ tự',
        default=0
    )
    note = models.TextField('Ghi chú', null = True, blank=True)

    class Meta:
        verbose_name = _('Phòng họp')
        verbose_name_plural = _('Phòng họp')

    def __str__(self):
        return "%s" % (self.name, )
        #return "%s - %s" % (self.name, self.group)


class Calender(models.Model):
    def clean(self):
        start = self.start_time
        end = self.end_time
        location = self.location
        address = self.address
        create_date = self.create_date

        if start:
            now = datetime.strptime(datetime.now().strftime('%d-%m-%Y'), '%d-%m-%Y').date()
            # print(now)
            day = datetime.strptime(start.strftime('%d-%m-%Y'), '%d-%m-%Y').date()
            # print(day)

            current_week = int(now.strftime("%V"))
            select_week = int(day.strftime("%V"))
            if self.pk is None and current_week == select_week:
                # print("333333333333333333333")
                self.cancel_status = 3          # additional status
                self.write_date = datetime.now()
                
            days = day - timedelta(days=1)
            if self.pk is None and (days == now or day == now):
                # print("44444444444444444444")
                self.cancel_status = 4          # unexpected status
                self.write_date = datetime.now()
        

        if create_date == None:
            if location and start and end:
                start = start.strftime('%Y-%m-%d %H:%M:%S')
                end = end.strftime('%Y-%m-%d %H:%M:%S')
                sql  = "select start_time, end_time, location_id from calender_calender where location_id = %s and ( start_time >= %s and start_time <= %s or end_time >= %s and end_time <= %s )"
                compare = query.connect_sql(sql, location.id, start, end, start, end)
                # print(compare)
                if compare:
                    raise ValidationError('Thời gian từ {} đến {} tại {} đã được đăng ký lịch.'.format(compare[0]['start_time'].strftime('%d-%m-%Y %H:%M'), compare[0]['end_time'].strftime('%d-%m-%Y %H:%M'), location.name))

            if address and start and end:
                start = start.strftime('%Y-%m-%d %H:%M:%S')
                end = end.strftime('%Y-%m-%d %H:%M:%S')
                sql  = "select start_time, end_time, address from calender_calender where address = %s and ( start_time >= %s and start_time <= %s or end_time >= %s and end_time <= %s )"
                compare = query.connect_sql(sql, address, start, end, start, end)
                if compare:
                    raise ValidationError('Thời gian từ {} đến {} tại {} đã được đăng ký lịch.'.format(compare[0]['start_time'].strftime('%d-%m-%Y %H:%M'), compare[0]['end_time'].strftime('%d-%m-%Y %H:%M'), address))

    STATUS = [
        ('NEW', 'Chưa duyệt'),
        ('ACCEPT', 'Đã duyệt'),
        ('DONE', 'Hoàn thành')
    ]
    CANCEL_STATUS = [
        (0, 'Bình thường'),
        (1, 'Hoãn/Huỷ'),
        (2, 'Thay đổi'),
        (3, 'Bổ sung'),
        (4, 'Đột xuất'),
        (5, 'Đổi địa điểm'),
        (6, 'Đổi thời gian'),
    ]
    week = models.IntegerField('Tuần')
    start_time = models.DateTimeField('Thời gian bắt đầu')
    end_time = models.DateTimeField('Thời gian kết thúc', help_text=_(
            'Nếu ngày kết thúc > ngày bắt đầu thì phải ghi chú số ngày họp dưới phần nội dung, không tự động tạo nhiều lịch họp với số ngày'
        ))
    address = models.CharField('Địa điểm', null=True, blank=True, max_length=255)
    location = models.ForeignKey(Meeting, verbose_name='Địa điểm', on_delete=models.CASCADE, null=True, blank=True)
    chair_unit = models.ForeignKey(Department, verbose_name="Chủ trì", on_delete=models.CASCADE)
    join_component = models.ManyToManyField(
        Department,
        verbose_name=_('Thành phần tham gia'),
        blank=True,
        db_table='calender_joincomponent',
        related_name="+",
        # related_query_name="calender",
    )
    prepare_unit = models.ManyToManyField(
        Department,
        verbose_name=_('Chuẩn bị'),
        blank=True,
        # help_text=_(
        #     'Nhấn giữ phím "Control", hoặc "Command" trên Mac, để chọn nhiều hơn một.'
        # ),
        db_table='calender_prepareunit',
        related_name="+",
        # related_query_name="calender",
    )
    # working_division = models.ManyToManyField(
    #     User,
    #     verbose_name=_('Phân công'),
    #     blank=True,
    #     db_table='calender_working_division',
    #     related_name="+"
    # )
    # join_component = models.ManyToManyField(
    #     'Department',
    #     verbose_name="Thành phần tham gia",
    #     through='JoinComponent',
    #     through_fields=('calender', 'department'),
    #     related_name="+"
    # )
    other_component = models.TextField('Thành phần khác', null=True, blank=True)
    other_prepare = models.TextField('Chuẩn bị khác', null=True, blank=True)
    # prepare_unit = models.ManyToManyField(
    #     Department,
    #     verbose_name="Đơn vị chuẩn bị",
    #     through='PrepareUnit',
    #     through_fields=('calender', 'department'),
    #     related_name="+"
    # )
    join_quantity = models.IntegerField('Số lượng tham gia')
    content = models.TextField(
        'Nội dung',
        help_text='Nội dung cuộc họp'
    )
    attach_file = models.FileField('Đính kèm tệp', null=True, blank=True)
    status = models.CharField(
        'Trạng thái',
        max_length=6,
        choices=STATUS,
        default='NEW'
    )
    #cancel_status = models.BooleanField('Trạng thái hoãn')
    cancel_status = models.IntegerField(
        'Trạng thái lịch',
        choices=CANCEL_STATUS,
        default=0
    )
    check_calender = models.BooleanField(
        'Trạng thái duyệt',
        default=False
    )
    check_calender_letter = models.BooleanField(
        'Trạng thái duyệt văn thư',
        default=False
    )
    requirement1 = models.BooleanField(
        'Hội nghị truyền hình',
        default=False
    )
    requirement2 = models.BooleanField(
        'Màn hình trình chiếu',
        default=False
    )
    requirement3 = models.BooleanField(
        'Backdrop',
        default=False
    )
    requirement4 = models.BooleanField(
        'Tea-break',
        default=False
    )
    requirement5 = models.BooleanField(
        'Gửi tài liệu cho khách ngoài PC',
        default=False
    )
    other_requirements = models.CharField('Yêu cầu khác', max_length=255, null=True, blank=True)
    note = models.TextField('Ghi chú', null=True, blank=True)
    create_date = models.DateTimeField('Ngày tạo', auto_now_add=True)
    write_date = models.DateTimeField('Ngày sửa', auto_now=True)
    create_uid = models.ForeignKey(User, verbose_name="Người tạo", on_delete=models.CASCADE)
    create_depart_id_id = models.IntegerField('Phòng tạo')
    slide_show = models.BooleanField('Trình chiếu', default=False)

    class Meta:
        verbose_name = _('Lịch công tác')
        verbose_name_plural = _('Lịch công tác')

    def __str__(self):
        return str(self.week)
    
    def __unicode__(self):
        return self.week
        

class MultipleFile(models.Model):
    files = models.FileField('Đính kèm tệp', null=True, blank=True)
    create_date = models.DateTimeField('Ngày tạo', auto_now_add=True)
    calendar = models.ForeignKey(Calender, verbose_name="Lịch công tác", on_delete=models.CASCADE)
    class Meta:
        verbose_name = _('Đính kèm')
        verbose_name_plural = _('Đính kèm')


class ExpectedCalender(models.Model):
    week = models.IntegerField('Tuần')
    content = models.TextField(
        'Nội dung',
        help_text='Nội dung dự kiến tuần sau'
    )
    create_uid = models.ForeignKey(User, verbose_name="Người tạo", related_name="+", on_delete=models.CASCADE)
    write_uid = models.ForeignKey(User, verbose_name="Người sửa", related_name="+", on_delete=models.CASCADE, null=True)
    create_date = models.DateTimeField('Ngày tạo', auto_now_add=True)
    write_date = models.DateTimeField('Ngày sửa', auto_now=True, null=True)

    class Meta:
        verbose_name = _('Lịch dự kiến')
        verbose_name_plural = _('Lịch dự kiến')
    
    def __str__(self):
        return str(self.week)


# class DivisionCalender(models.Model):
#     calendar = models.ForeignKey(Calender, verbose_name="Lịch công tác", on_delete=models.CASCADE)
#     divider = models.ForeignKey(User, verbose_name="Người phân công", on_delete=models.CASCADE)
#     receiver = models.ForeignKey(User, verbose_name="Người nhận", on_delete=models.CASCADE)
#     create_date = models.DateTimeField('Ngày tạo', auto_now_add=True)
#     write_date = models.DateTimeField('Ngày sửa', auto_now=True, null=True)


# class JoinComponent(models.Model):
#     calender = models.ForeignKey(Calender, on_delete=models.CASCADE)
#     department = models.ForeignKey(Department, verbose_name="Phòng ban", on_delete=models.CASCADE)
#     class Meta:
#         verbose_name = _('Phòng ban')
#         verbose_name_plural = _('Phòng ban')

# class PrepareUnit(models.Model):
#     calender = models.ForeignKey(Calender, on_delete=models.CASCADE)
#     department = models.ForeignKey(Department, verbose_name="Phòng ban", on_delete=models.CASCADE)
#     class Meta:
#         verbose_name = _('Phòng ban')
#         verbose_name_plural = _('Phòng ban')

class Profile(models.Model):
    user = models.OneToOneField(User, verbose_name="Người dùng", on_delete=models.CASCADE)      # View diagram in database will specify ...
    department = models.ForeignKey(Department, verbose_name="Phòng ban", on_delete=models.CASCADE)
    is_driver = models.BooleanField('Lái xe', default=False)
    is_manager = models.BooleanField('Ban giám đốc', default=False)

    class Meta:
        verbose_name = _('Hồ sơ')
        verbose_name_plural = _('Hồ sơ')
        
    def __str__(self):
        return str(self.user.last_name)


class Working_Division(models.Model):
    calender = models.ForeignKey(Calender, verbose_name="Lịch", on_delete=models.CASCADE)
    user = models.ForeignKey(User, verbose_name="Người được phân công", on_delete=models.CASCADE)
    active = models.BooleanField('Kích hoạt', default=True)
    create_uid = models.ForeignKey(User, verbose_name="Người tạo", related_name="+", on_delete=models.CASCADE)
    write_uid = models.ForeignKey(User, verbose_name="Người sửa", related_name="+", on_delete=models.SET_NULL, null=True)
    create_date = models.DateTimeField('Ngày tạo', auto_now_add=True)
    write_date = models.DateTimeField('Ngày sửa', null=True)

    class Meta:
        verbose_name = _("Phân công dự họp")
        verbose_name_plural = _("Phân công dự họp")
        default_permissions = ()

    def __str__(self):
        return str(self.user)