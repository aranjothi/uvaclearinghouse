from django.shortcuts import render

def home(request):
    return render(request, 'main/home.html')

def login_page(request):
    return render(request, 'main/login.html')

def signup_page(request):
    return render(request, 'main/signup.html')
