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
from decouple import config

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from debug_toolbar.toolbar import debug_toolbar_urls

from app.static_view import Error403View, Error404View, Error500View

from ninja import NinjaAPI
from chat.api import router as chat_router
from file.api import router as file_router
from agent.api import router as agent_router


api = NinjaAPI()
api.add_router("/chat/", chat_router)
api.add_router("/file/", file_router)
api.add_router("/agent/", agent_router)

handler403 = Error403View.as_view()
handler404 = Error404View.as_view()
handler500 = Error500View.as_view()

urlpatterns = [
    path('XYZ2024-admin/', admin.site.urls),
    path("", include("common.urls")),
    
    path('accounts/', include('allauth.urls')),
    path("users/", include("users.urls", namespace="users")),
    
    path("chat/", include("chat.urls", namespace="chat")),
    
    path("library/", include("library.urls", namespace="library")),
    path("file/", include("file.urls", namespace="file")),

    path("agent/", include("agent.urls", namespace="agent")),
    
    path("api/", api.urls),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Django toolbar
if config("TOOLBAR_DEBUG", cast=bool, default=settings.DEBUG):
    urlpatterns = debug_toolbar_urls() + urlpatterns