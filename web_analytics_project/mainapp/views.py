from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Post
from .forms import ModelForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail

from .text_generation_django import generate_text_function

def home(request):
    context = {'Posts': Post.objects.all()}
    return render(request, 'mainapp/index.html', context)

def about(request):    
    return render(request, 'mainapp/about.html', {'title': 'About Us'})

class PostListView(ListView):
    model = Post
    template_name = 'mainapp/index.html'
    context_object_name = 'Posts'
    ordering = ['-date_posted']
    paginate_by = 5

class UserPostListView(ListView):
    model = Post
    template_name = 'mainapp/user_posts.html'
    context_object_name = 'Posts'
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')

class PostDetailView(DetailView):
    model = Post

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

@login_required
def text_model(request):
    if request.method == 'POST':
        model_form = ModelForm(request.POST, request.FILES)
        if model_form.is_valid():
            cd = model_form.cleaned_data
            title = cd.get('title')
            start_string =  cd.get('start_string')
            length =  cd.get('length')
            text = str(request.FILES['file'].read())

            subject = title + ' Generated Text'
            generated_sentences, train_perplexity, loss = generate_text_function(text, start_string, length)
            message = 'Perplexity: ' + train_perplexity + '\n\n'
            message += 'Loss: ' + loss + '\n\n'
            index = 1
            for sentence in generated_sentences:
                message += str(index) + '. ' + sentence + '\n\n'
                index += 1
            recipient_list = [request.user.email]
            
            email = EmailMessage(subject, message, to=recipient_list)
            email.send()

            messages.success(request, f'Please check your email for the generated text')
            return redirect('mainapp:home')
    else:
        model_form = ModelForm()

    context = {'model_form': model_form}

    return render(request, 'mainapp/text_model.html', context)



