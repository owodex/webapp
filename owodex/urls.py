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
from app.views import CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name = "home"),
    path('blog/', blog_list, name='blog_list'),
    path('blog/<slug:slug>/', blog_detail, name='blog_detail'),
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
    # path('api/vtpass/service-variations', vtpass_service_variations, name='vtpass_service_variations'),
    path('verify-email/<str:uidb64>/<str:token>/', verify_email, name='verify_email'),
    path('profile/', profile, name ='profile'),
    path('settings/', user_settings, name ='settings'),
    path('logout/', user_logout, name ='logout'),
    path('profile/', profile, name ='profile'),
    path('delete-account/', delete_account, name='delete_account'),
    path('giftcards/', giftcards, name ='giftcards'),
    path('pay_bills/', pay_bills, name ='pay_bills'),
    path('api/cable/variation-codes/<str:provider>/',get_cable_variations, name='cable_variations'),
    path('validate-smart-card/', validate_smart_card, name='validate_smart_card'),
    path('verify-meter/', verify_meter, name='verify_meter'),
     path('api/notification-count/', get_notification_count, name='get_notification_count'),
     path('mark-all-notifications-read/', mark_all_notifications_read, name='mark_all_notifications_read'),
    path('airtime_data/', airtime_data, name ='airtime_data'),
    path('bonus/', bonus, name ='bonus'),
    path('withdraw-bonus/', withdraw_bonus, name ='withdraw_bonus'),
    path('api/get-gift-cards/', get_gift_cards, name='get_gift_cards'),
    path('api/get-currencies/', get_currencies, name='get_currencies'),
    path('api/get-card-types/', get_card_types, name='get_card_types'),
    path('api/get-denominations/', get_denominations, name='get_denominations'),
    path('api/get-rate/', get_rate, name='get_rate'),
    path('api/get-g-rate/', get_g_rate, name='get_g_rate'),
    path('search/', search, name='search'),
    path('trade-giftcard/<int:giftcard_id>/', trade_giftcard, name='trade_giftcard'),
    path('buy-giftcard/<int:giftcard_id>/', buy_giftcard, name='buy_giftcard'),
    path('submit-deposit/', submit_deposit, name='submit_deposit'),
    path('admin/send-notification/', send_notification, name="send_notification"),
    path('api/owodex-tag-transfer/', owodex_tag_transfer, name='owodex_tag_transfer'),
    path('api/bank-transfer/', bank_transfer, name='bank_transfer'),
    path('api/get-beneficiaries/', get_beneficiaries, name='get_beneficiaries'),
    path('api/purchase-data/', submit_data_request, name='purchase_data'),
    path('api/purchase-airtime/', submit_airtime_request, name='purchase_airtime'),
    path('get-data-plans/', get_data_plans, name='get_data_plans'),
    path('submit-cable-request/', submit_cable_request, name='submit_cable_request'),
    path('submit_electricity_request/', submit_electricity_request, name='submit_electricity_request'),
    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
