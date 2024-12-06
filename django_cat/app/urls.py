"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from app.static_view import HomeView, Error403View, Error404View, Error500View

from ninja import NinjaAPI
from chat.api import router as chat_router

api = NinjaAPI()
api.add_router("/chat/", chat_router)

handler403 = Error403View.as_view()
handler404 = Error404View.as_view()
handler500 = Error500View.as_view()

urlpatterns = [
    path('XYZ2024-admin/', admin.site.urls),
    path("", HomeView.as_view(), name="home"),
    path("users/", include("users.urls", namespace="users")),
    path("chat/", include("chat.urls", namespace="chat")),
    path("api/", api.urls),
]

