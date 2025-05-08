from django.urls import include, path
from .views import RegisterUserView, UserLoginView, UserLogoutView, UserProfileView, DeleteUserView, UserListView, ApproveUserView

app_name = 'users'

manage_urlpatterns = [
    path('list/', UserListView.as_view(), name='list'),
    path("approve/<int:pk>/", ApproveUserView.as_view(), name="approve"),
]

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path("delete/", DeleteUserView.as_view(), name="delete"),

    path("manage/", include((manage_urlpatterns, 'manage')), name='manage'),
]