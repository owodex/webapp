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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name = "home"),
    path('products/', products, name = "products"),
    path('support', support, name = "support"),
    path('signup/', signup, name ='signup'),
    path('login/', login, name ='login'),
    path('rate-calculator/', rate_calculator, name ='rate_calculator'),
    path('terms/', terms, name ='terms'),
    path('privacy_policy/', privacy_policy, name ='privacy_policy'),
    path('dashboard/', dashboard, name ='dashboard'),
    path('services/', services, name ='services'),
    path('transactions/', transactions, name ='transactions'),
    path('profile/', profile, name ='profile'),
    path('settings/', settings, name ='settings'),
    path('logout/', logout, name ='logout'),
    path('giftcards/', giftcards, name ='giftcards'),
    path('pay_bills/', pay_bills, name ='pay_bills'),
    path('airtime_data/', airtime_data, name ='airtime_data'),
    path('bonus/', bonus, name ='bonus'),
    path('trade_giftcard/', trade_giftcard, name ='trade_giftcard'),

]
