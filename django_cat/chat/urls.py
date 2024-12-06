from django.urls import path, include
from chat.views import home, ChatView
from chat.api import router


app_name = "chat"

urlpatterns = [
    path('', home, name='home'),
    path("chat", ChatView.as_view(), name='chat'),
]

urlpatterns.extend(router.urls_paths(""))
