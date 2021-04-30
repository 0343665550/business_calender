from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from calender.models import Department

# Create your models here.
class VehicleType(models.Model):
    name = models.CharField('Tên loại xe', max_length=255, unique=True)
    is_left_tab = models.BooleanField('Tab hiển thị bên trái', default=False)
    note = models.TextField('Ghi chú', null=True, blank=True)
    create_uid = models.ForeignKey(User, verbose_name="Người tạo", related_name="+", on_delete=models.CASCADE)
    write_uid = models.ForeignKey(User, verbose_name="Người sửa", related_name="+", on_delete=models.SET_NULL, null=True)
    create_date = models.DateTimeField('Ngày tạo', auto_now_add=True)
    write_date = models.DateTimeField('Ngày sửa', null=True)

    class Meta:
        verbose_name = _("Loại xe")
        verbose_name_plural = _("Loại xe")
        default_permissions = ()

    def __str__(self):
        return str(self.name)


class Vehicle(models.Model):
    name = models.CharField('Tên xe', max_length=255)
    number = models.CharField('Số xe', max_length=255, unique=True)
    frame_number = models.CharField('Số khung', null=True, blank=True, max_length=255)
    machine_number = models.CharField('Số máy', null=True, blank=True, max_length=255)
    fuel = models.CharField('Nhiên liệu', max_length=255)
    manage_unit = models.ForeignKey(Department, verbose_name="Đơn vị quản lý", on_delete=models.CASCADE)
    vehicle_type = models.ForeignKey(VehicleType, verbose_name="Loại xe", on_delete=models.CASCADE)
    note = models.TextField('Ghi chú', null=True, blank=True)
    create_uid = models.ForeignKey(User, verbose_name="Người tạo", related_name="+", on_delete=models.CASCADE)
    write_uid = models.ForeignKey(User, verbose_name="Người sửa", related_name="+", on_delete=models.SET_NULL, null=True)
    create_date = models.DateTimeField('Ngày tạo', auto_now_add=True)
    write_date = models.DateTimeField('Ngày sửa', null=True)

    class Meta:
        verbose_name = _("Xe")
        verbose_name_plural = _("Xe")
        default_permissions = ()

    def __str__(self):
        return str(self.name)


class VehicleCalender(models.Model):
    STATUS = [
        ('NEW', 'Đăng ký'),
        ('CONFIRM', 'Xác nhận'),
        ('APPROVAL', 'Đã duyệt'),
        ('ASSIGNED', 'Đã phân xe'),
        ('CANCEL', 'Hủy/Hoãn')
    ]
    week = models.IntegerField('Tuần')
    start_time = models.DateTimeField('Thời gian bắt đầu', null=True)
    end_time = models.DateTimeField('Thời gian kết thúc', help_text=_(
        'Nếu ngày kết thúc > ngày bắt đầu thì phải ghi chú số ngày họp dưới phần nội dung, không tự động tạo nhiều lịch họp với số ngày'
    ), null=True)
    content = models.TextField('Nội dung công việc', help_text='Nội dung công việc')
    departure = models.CharField('Nơi đi', max_length=255)
    destination = models.CharField('Nơi đến', max_length=255)
    # register = models.ForeignKey(User, verbose_name="Người đăng ký", on_delete=models.CASCADE)
    register_unit = models.ForeignKey(Department, verbose_name="Đơn vị đăng ký", on_delete=models.CASCADE)
    vehicle_type = models.ForeignKey(VehicleType, verbose_name="Tên loại xe", on_delete=models.CASCADE)
    expected_km = models.IntegerField('Số km dự kiến', null=True, blank=True)
    expected_crane_hour = models.IntegerField('Số giờ cẩu dự kiến (Nâng, cẩu)', null=True, blank=True)
    seat_number = models.IntegerField('Số người')
    status = models.CharField('Trạng thái lịch', max_length=8, choices=STATUS, default='NEW')
    note = models.TextField('Ghi chú', null=True, blank=True)
    create_uid = models.ForeignKey(User, verbose_name="Người tạo", related_name="+", on_delete=models.CASCADE)
    write_uid = models.ForeignKey(User, verbose_name="Người sửa", related_name="+", on_delete=models.SET_NULL, null=True)
    create_date = models.DateTimeField('Ngày tạo', auto_now_add=True)
    write_date = models.DateTimeField('Ngày sửa', null=True)

    class Meta:
        verbose_name = _("Lịch xe")
        verbose_name_plural = _("Lịch xe")
        # Defaults to ('add', 'change', 'delete')
        default_permissions = ()
        
        permissions = (
            ("view_vehicle", "Xem lịch xe"),
            ("register_vehicle", "Đăng ký"),
            ("confirm_vehicle", "Xác nhận"),
            ("approval_vehicle", "Duyệt"),
            ("assign_vehicle", "Phân công"),
            ("manage_vehicle", "Quản lý"),
        )

    def __str__(self):
        return str(self.week)


class Vehicle_Division(models.Model):
    calender = models.ForeignKey(VehicleCalender, verbose_name="Lịch", on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, verbose_name="Xe", on_delete=models.CASCADE)
    active = models.BooleanField('Kích hoạt', default=True)
    create_uid = models.ForeignKey(User, verbose_name="Người tạo", related_name="+", on_delete=models.CASCADE)
    write_uid = models.ForeignKey(User, verbose_name="Người sửa", related_name="+", on_delete=models.SET_NULL, null=True)
    create_date = models.DateTimeField('Ngày tạo', auto_now_add=True)
    write_date = models.DateTimeField('Ngày sửa', null=True)

    class Meta:
        verbose_name = _("Phân công xe")
        verbose_name_plural = _("Phân công xe")
        default_permissions = ()

    def __str__(self):
        return str(self.vehicle)


class Driver_Division(models.Model):
    calender = models.ForeignKey(VehicleCalender, verbose_name="Lịch", on_delete=models.CASCADE)
    driver = models.ForeignKey(User, verbose_name="Người lái", on_delete=models.CASCADE)
    active = models.BooleanField('Kích hoạt', default=True)
    create_uid = models.ForeignKey(User, verbose_name="Người tạo", related_name="+", on_delete=models.CASCADE)
    write_uid = models.ForeignKey(User, verbose_name="Người sửa", related_name="+", on_delete=models.SET_NULL, null=True)
    create_date = models.DateTimeField('Ngày tạo', auto_now_add=True)
    write_date = models.DateTimeField('Ngày sửa', null=True)

    class Meta:
        verbose_name = _("Phân công người lái")
        verbose_name_plural = _("Phân công người lái")
        default_permissions = ()

    def __str__(self):
        return str(self.driver)

