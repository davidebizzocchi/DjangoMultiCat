from django.shortcuts import render, redirect
from django.views.generic import CreateView, TemplateView, UpdateView, DetailView
from django.urls import reverse_lazy
from users.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout, login
from django.contrib.auth.mixins import UserPassesTestMixin

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.account.auth_backends import AuthenticationBackend
from allauth.account.models import EmailAddress

from users.forms import UserRegistrationForm, LoginForm, UserProfileConfigurationForm
from users.models import UserProfile

from common.mixin import LoginRequiredMixin

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator

from icecream import ic


class AllauthGoogleMixin:
    def __init__(self, *args, **kwargs):
        self.backend = AuthenticationBackend()

        super().__init__(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.POST.get("action", "none") == "google":
            adapter = GoogleOAuth2Adapter(request)
            # adapter.redirect_uri_protocol = "https"

            # redirect = adapter.get_provider().redirect_from_request(request)
            # redirect["Location"] = redirect.url.replace("http%", "https%")

            return adapter.get_provider().redirect_from_request(request)
        
        return super().post(request, *args, **kwargs)


class RegisterUserView(AllauthGoogleMixin, UserPassesTestMixin, CreateView):
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('home')  # Change 'home' with your destination URL
    redirect_authenticated_user = True

    def test_func(self):
        # Returns True only if user is NOT authenticated
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        return redirect(self.success_url)

    def form_valid(self, form):
        try:
            # Auto-login after registration with specified backend
            user = User.objects.create_user(email=form.cleaned_data.get("email"), password=form.cleaned_data.get("password"))
            EmailAddress.objects.create(email=form.cleaned_data.get("email"), user=user, primary=True, verified=False)

            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect(self.success_url)

        except Exception as e:
            ic(e)
            return super().form_invalid(form)

class UserLoginView(AllauthGoogleMixin, LoginView):
    template_name = 'users/login.html'
    success_url = reverse_lazy('home')
    redirect_authenticated_user = True
    form_class = LoginForm

    def form_valid(self, form):
        user = self.backend.authenticate(self.request, **form.cleaned_data)
        if user is not None:
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect(self.success_url)

        return super().form_invalid(form)

class UserLogoutView(LoginRequiredMixin, LogoutView):
    template_name = 'users/logout.html'
    next_page = reverse_lazy('home')
    http_method_names = ["get", "post"]
    login_url = reverse_lazy('users:login')

class UserProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'users/profile.html'
    form_class = UserProfileConfigurationForm
    success_url = reverse_lazy('users:profile')
    context_object_name = 'user'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context.update({
            "email": self.user.email,
            "name": self.user.name,
            "is_approved": self.user.is_approved,
            "configured": self.user.configured,
            "avatar_url": self.user.avatar_url,
            "cheshire_id": getattr(self.user, 'cheshire_id', None)
        })

        return context
    
    def get_object(self, queryset = ...):
        return self.user

@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteUserView(LoginRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):

        logout(request)
        self.usr.delete()
        return JsonResponse({"status": "success", "redirect_url": reverse_lazy('home')})

class UserListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'users/list.html'
    login_url = reverse_lazy('users:login')
    
    def test_func(self):
        return self.usr.is_staff
    
    def handle_no_permission(self):
        return redirect('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        return context

class ApproveUserView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = 'users/approve.html'
    context_object_name = 'user'

    is_superuser_required = True
    is_staff_required = True

    def post(self, request, *args, **kwargs):
        profile: UserProfile = self.get_object()
        action = request.POST.get('action')

        if action == 'approve':
            profile.approve(True)
        elif action == 'revoke':
            profile.approve(False)

        return redirect('users:manage:list')