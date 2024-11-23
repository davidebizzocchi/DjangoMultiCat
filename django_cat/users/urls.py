from django.urls import path
from .views import RegisterUserView, UserLoginView, UserLogoutView, UserProfileView, DeleteUserView, UserListView

app_name = 'users'

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path("delete/", DeleteUserView.as_view(), name="delete"),
    path('list/', UserListView.as_view(), name='list'),
]