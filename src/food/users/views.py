from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse

def login_view(request):
    if request.user.is_authenticated:
        print('user logged in', request.user.username)
        return redirect('profile')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')
        else:
            return TemplateResponse(request, 'user/login.html', {'error': 'Invalid credentials'})
    else:
        return TemplateResponse(request, 'user/login.html')
    
def logout_view(request):
    logout(request)
    return redirect('user/login')

# @login_required
def profile(request):
    context = {"user": request.user}
    return TemplateResponse(request, "user/profile.html", context, status=200)