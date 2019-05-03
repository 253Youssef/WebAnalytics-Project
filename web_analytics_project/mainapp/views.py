from django.shortcuts import render
from django.http import HttpResponse
from .models import Post

def home(request):
    context = {'Posts': Post.objects.all()}
    return render(request, 'mainapp/index.html', context)

def about(request):
    
    return render(request, 'mainapp/about.html', {'title': 'About Us'})

