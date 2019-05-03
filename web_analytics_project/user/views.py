from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created successfully for {username}!')
            return redirect('mainapp:home')
        else:
            messages.error(request, f'Account not created successfully!!!')
            return redirect('mainapp:home')
    else:
        form = UserCreationForm()
    return render(request, 'user/register.html', {'form':form})

def login(request):
    return render(request, 'mainapp/login.html', {'title': 'Login'})
