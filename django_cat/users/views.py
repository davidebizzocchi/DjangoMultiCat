from django.shortcuts import render, redirect
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from .forms import UserRegistrationForm
from .models import UserProfile
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from icecream import ic

class RegisterUserView(UserPassesTestMixin, CreateView):
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('home')  # Cambia 'home' con il tuo URL di destinazione
    redirect_authenticated_user = True

    def test_func(self):
        # Ritorna True solo se l'utente NON è autenticato
        ic(not self.request.user.is_authenticated)
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        return redirect(self.get_success_url())

    def form_valid(self, form):
        # Create user without saving to DB
        user: User = form.save(commit=False)
        ic(user)
        user.set_unusable_password()
        user.save()
        
        # Create UserProfile
        UserProfile.objects.create(user=user)
        
        return super().form_valid(form)

class UserLoginView(LoginView):
    template_name = 'users/login.html'
    success_url = reverse_lazy('home')
    redirect_authenticated_user = True

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        # Ignoriamo la password e usiamo solo lo username
        ic(username)
        user = authenticate(self.request, username=username)
        if user is not None:
            login(self.request, user)
            return redirect(self.get_success_url())
        return super().form_invalid(form)

class UserLogoutView(LoginRequiredMixin, LogoutView):
    template_name = 'users/logout.html'
    next_page = reverse_lazy('home')
    http_method_names = ["get", "post"]
    login_url = reverse_lazy('users:login')  # opzionale

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    # def get(self, request, *args, **kwargs):
    #     # Se l'utente non è autenticato, redirect alla home
    #     if not request.user.is_authenticated:
    #         return redirect('home')
    #     # Altrimenti mostra la pagina di conferma
    #     return render(request, self.template_name)

    # def post(self, request, *args, **kwargs):
    #     # Esegue il logout
    #     logout(request)
    #     return redirect(self.next_page)
