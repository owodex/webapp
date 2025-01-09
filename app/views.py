from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request, 'index.html')

def products(request):
    return render(request, 'service.html')

def support(request):
    return render(request, 'contact.html')

def signup(request):
    return render(request, "signup.html")

def login(request):
    return render(request, "login.html")

def rate_calculator(request):
    return render(request, "rate_calculator.html")

def terms(request):
    return render(request, "terms.html")

def privacy_policy(request):
    return render(request, "privacy_policy.html")

def dashboard(request):
    return render(request, "dashboard/index.html")    

def services(request):
    return render(request, "dashboard/services.html")

def transactions(request):
    return render(request, "dashboard/transaction.html")

def settings(request):
    return render(request, "dashboard/settings.html")

def profile(request):
    return render(request, "dashboard/profile.html")

def logout(request):
    return render(request, "dashboard/logout.html")

def giftcards(request):
    return render(request, "dashboard/giftcards.html")

def airtime_data(request):
    return render(request, 'dashboard/airtime-data.html')

def pay_bills(request):
    return render(request, 'dashboard/pay-bills.html')

def bonus(request):
    return render(request, 'dashboard/bonus.html')

def trade_giftcard(request):
    return render(request, 'dashboard/trade_giftcards.html')