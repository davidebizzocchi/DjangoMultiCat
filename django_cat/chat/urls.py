from django.urls import path, include
from chat.views import home, ChatView, ChatListView, create_chat, delete_chat
from chat.api import router

app_name = "chat"

urlpatterns = [
    path('', home, name='home'),
    path('chats/', ChatListView.as_view(), name='chat_list'),
    path('chats/new/', create_chat, name='create_chat'),
    path('chats/<str:chat_id>/', ChatView.as_view(), name='chat_detail'),
    path('chats/<str:chat_id>/delete/', delete_chat, name='delete_chat'),
]

urlpatterns.extend(router.urls_paths(""))
