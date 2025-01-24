"""
URL configuration for owodex project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from app.views import *
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name = "home"),
    path('products/', products, name = "products"),
    path('support', support, name = "support"),
    path('signup/', signup, name ='signup'),
    path('login/', user_login, name ='login'),
    path('rate-calculator/', rate_calculator, name ='rate_calculator'),
    path('terms/', terms, name ='terms'),
    path('privacy_policy/', privacy_policy, name ='privacy_policy'),
    path('dashboard/', dashboard, name ='dashboard'),
    path('services/', services, name ='services'),
    path('transactions/', transactions, name ='transactions'),
    path('profile/', profile, name ='profile'),
    path('settings/', user_settings, name ='settings'),
    path('logout/', user_logout, name ='logout'),
    path('profile/', profile, name ='profile'),
    path('delete-account/', delete_account, name='delete_account'),
    path('giftcards/', giftcards, name ='giftcards'),
    path('pay_bills/', pay_bills, name ='pay_bills'),
    path('airtime_data/', airtime_data, name ='airtime_data'),
    path('bonus/', bonus, name ='bonus'),
    path('search/', search, name='search'),
    path('trade_giftcard/', trade_giftcard, name ='trade_giftcard'),
    path('admin/send-notification/', send_notification, name="send_notification"),
    path('api/owodex-tag-transfer/', owodex_tag_transfer, name='owodex_tag_transfer'),
    path('api/bank-transfer/', bank_transfer, name='bank_transfer'),
    path('api/get-beneficiaries/', get_beneficiaries, name='get_beneficiaries'),
    path('submit-airtime-request/', submit_airtime_request, name='submit_airtime_request'),
    path('submit-data-request/', submit_data_request, name='submit_data_request'),
    path('submit-cable-request/', submit_cable_request, name='submit_cable_request'),
    path('submit_electricity_request/', submit_electricity_request, name='submit_electricity_request'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
