"""
MUCP TOOL
Author: Kirodh Boodhraj
"""
from django.shortcuts import render, redirect
from .forms import UserRegisterForm
from django.contrib.auth.decorators import login_required


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            # return redirect('home:login')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'home/register.html', {'form': form})

@login_required
def home_view(request):
    return render(request, 'home/home.html', {'user': request.user})

# contact us page
def contact_us(request):
    return render(request, "home/contact_us.html")
