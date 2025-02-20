from django.urls import path, include
from chat.views import (
    ChatHome, ChatStreamView, ChatListView, 
    ChatDeleteView, ChatCreateView
)
from chat.api import router

app_name = "chat"

urlpatterns = [
    path('', ChatHome.as_view(), name='home'),
    path('list/', ChatListView.as_view(), name='list'),
    path('new/', ChatCreateView.as_view(), name='create'),
    path('<str:chat_id>/', ChatStreamView.as_view(), name='chat'),
    path('<str:chat_id>/delete/', ChatDeleteView.as_view(), name='delete'),

    path("api/", include((list(router.urls_paths("")), "api")))
]

