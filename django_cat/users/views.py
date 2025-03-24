from django.shortcuts import render, redirect
from django.views.generic import CreateView, TemplateView
from django.urls import reverse_lazy
from users.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.account.auth_backends import AuthenticationBackend
from allauth.account.models import EmailAddress

from users.forms import UserRegistrationForm, LoginForm  # Add LoginForm to import
from users.models import UserProfile

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
        return redirect(self.get_success_url())

    def form_valid(self, form):
        try:
            # Auto-login after registration with specified backend
            user = User.objects.create_user(email=form.cleaned_data.get("email"), password=form.cleaned_data.get("password"))
            EmailAddress.objects.create(email=form.cleaned_data.get("email"), user=user, primary=True, verified=False)
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect(self.success_url)

        except Exception as e:
            ic(e)
            return super().form_valid(form)

class UserLoginView(AllauthGoogleMixin, LoginView):
    template_name = 'users/login.html'
    success_url = reverse_lazy('home')
    redirect_authenticated_user = True
    form_class = LoginForm  # Changed from UserRegistrationForm to LoginForm

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
    login_url = reverse_lazy('users:login')  # optional

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'
    login_url = reverse_lazy('users:login')
    
    def get(self, request, *args, **kwargs):
        user_profile: UserProfile = request.user.userprofile
        context = {
            'username': request.user.username,
            'cheshire_id': user_profile.cheshire_id
        }
        return render(request, self.template_name, context)

@method_decorator(require_http_methods(["POST"]), name='dispatch')
class DeleteUserView(LoginRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        user = request.user
        logout(request)
        user.delete()
        return JsonResponse({"status": "success", "redirect_url": reverse_lazy('home')})

class UserListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'users/list.html'
    login_url = reverse_lazy('users:login')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        return redirect('home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        return context
