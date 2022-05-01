from django.urls import path
from vehicle.views import *
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path

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
    path("vehicle_stage/", VehicleWorkingStageView.as_view(), name="vehicle_stage"),
    path("vehicle_stage/confirm/", stage_confirm_action, name="stage_confirm_action"),
    path("confirm_division/", confirm_division, name="confirm_division"),
    path('view_form/', view_form, name='view_form'),
    path('get_form/', get_form, name='get_form'),
    path('export_xlsx_routine/', export_xlsx_routine, name='export_xlsx_routine'),
    path('export_xlsx_form_1/', export_xlsx_form_1, name='export_xlsx_form_1')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    re_path(r'^files/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
    }),