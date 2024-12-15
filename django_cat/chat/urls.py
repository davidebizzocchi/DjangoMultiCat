from django.urls import path, include
from chat.views import home, ChatView, ChatListView, create_chat, delete_chat
from chat.api import router

app_name = "chat"

urlpatterns = [
    path('', home, name='home'),
    path('list/', ChatListView.as_view(), name='list'),
    path('new/', create_chat, name='create'),
    path('<str:chat_id>/', ChatView.as_view(), name='chat'),
    path('<str:chat_id>/delete/', delete_chat, name='delete'),
]

urlpatterns.extend(router.urls_paths(""))
