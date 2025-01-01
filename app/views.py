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
