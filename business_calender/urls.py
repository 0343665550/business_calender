"""business_calender URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include 
from calender.views import Login 
from . import views
from django.contrib.auth.views import LoginView

urlpatterns = [
    path('jet/',include('jet.urls','jet')),
    path('jet/dashboard/',include('jet.dashboard.urls','jet-dashboard')),
    path('admin/', admin.site.urls),
    path("", include("calender.urls" , namespace='Lịch công tác công ty')),
    path("calender/", include("calender.urls" , namespace='Lịch công tác phòng ban')),
    path('login/', LoginView.as_view(),name='login'),
    path('public/',views.public,name='public'),
    path('private/',views.private,name='private'),
    path('shows/<int:week>/',views.shows, name='shows'),
    # =====================VEHICLE============================
    path('vehicle/', include("vehicle.urls", namespace="Lịch xe")),
]
