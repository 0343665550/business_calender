from django.urls import path
from vehicle.views import *

app_name = "vehicle"

urlpatterns = [
    path("unexpected_error/", error_action, name="error_action"),
    path("vehicle/", VehicleCalender.as_view(), name="index"),
    path("vehiclecalender/<int:cid>/", update_detail_view, name="update_detail_view"),
    path("vehiclecalender/add/", add_view, name="add_view"),
    path("vehicle_calender/confirm/", confirm_action, name="confirm_action"),
    path("vehicle_calender/approval/", approval_action, name="approval_action"),
    path("vehicle_calender/assign/<int:cid>/", info_modal_division, name="assign_modal_action"),
    path('export_xlsx/', export_xlsx, name='export_xlsx'),
]