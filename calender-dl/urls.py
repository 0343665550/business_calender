from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import Calender, Login, ListCreateExpectedView, UpdateDeleteExpectedView, CalenderList, CalenderCreateView
from django.views.static import serve
from django.urls import re_path
from django.contrib.auth.decorators import login_required

from vehicle import views as vehicle_views

app_name = 'calender'

urlpatterns = [
    path('week/', views.getWeek, name = 'week'),
    path('week_draf/', views.getWeek_draf, name = 'week_draf'),
    path('uploadfile/', views.fileUploaderView, name = 'fileUploaderView'),
    path('uploadfileDepartmentDraft/', views.uploadfileDepartmentDraft, name = 'uploadfileDepartmentDraft'),
    path('uploadfileRelease/', views.uploadfileRelease, name = 'uploadfileRelease'),
    path('deletefileRelease/', views.deletefileRelease, name = 'deletefileRelease'),
    path('filter_chair/', views.filter_chair, name = 'filter_chair'),
    path('browse/', views.browse, name = 'browse'),
    path('cancel/', views.cancel, name = 'cancel'),
    path('export_xlsx/', views.export_xlsx, name='export_xlsx'),
    path("", Login.as_view() , name='login'),
    path("approval/", views.approval_calender , name='approval_calender'),
    path('depart_draft/', views.depart_draft, name = 'depart_draft'),                       # Re-render draft department calendar on tab nav-profile
    path('company_draft/', views.company_draft, name = 'company_draft'),                    # Re-render draft company calendar on tab nav-home
    path('filter_type/', views.filter_type, name = 'filter_type'),                          # Re-render company calendar is approvaled
    path('approval_draft_dep/', views.approval_draft_dep, name = 'approval_draft_dep'),  
    path('cancel_approval_draft_dep/', views.cancel_approval_draft_dep, name = 'cancel_approval_draft_dep'),   
    path('approval_draft_com/', views.approval_draft_com, name = 'approval_draft_com'),
    path('cancel_approval_draft_com/', views.cancel_approval_draft_com, name = 'cancel_approval_draft_com'), 
    path("calender/", Calender.as_view(), name='post'),
    path("confirmDelete/", views.confirmDelete , name='confirmDelete'),
	path("confirmUpdateCalender/", views.confirmUpdateCalender , name='confirmUpdateCalender'),
	path("confirmRecycleCalender/", views.confirmRecycleCalender , name='confirmRecycleCalender'),
    path('expected', views.create_expected),
    path('expected/<int:pk>', UpdateDeleteExpectedView.as_view()),
    path('check_double_calender/', views.check_double_calender, name='check_double_calender'),
    path('on_off_slide_show/', views.on_off_slide_show, name='on_off_slide_show'),
    path("confirmDelete/", views.confirmDelete , name='confirmDelete'),
	path("confirmUndoBrowse/", views.confirmUndoBrowse , name='confirmUndoBrowse'),
    path("admin/calender/draft/", login_required(Calender.as_view()), name='draft'),
    path("admin/calender/draft/add/", CalenderCreateView.as_view()),
    path("admin/calender/draft/<int:pk>/change/", views.draftEdit, name='draft_edit'),
    # path("calenders/<int:id>", CalenderUpdateView.as_view()),
    path("confirm_division/", views.confirm_division, name="confirm_division"),
    # ================================LỊCH XE=======================================
    path("admin/vehicle/vehicle_calender/", vehicle_views.VehicleCalender.as_view(), name="vehicle_get"),       # RE-RENDER NOT DEFAULT
    path("lichxe/", Login.as_view())   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
    re_path(r'^files/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
    }),
    