
from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('home/', views.home, name='home'),
]