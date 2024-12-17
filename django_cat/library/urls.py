from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.LibraryListView.as_view(), name='list'),
    path('new/', views.NewLibraryView.as_view(), name='new'),
    path('<str:library_id>/delete/', views.DeleteLibraryView.as_view(), name='delete'),
    path('<str:library_id>/', views.LibraryDetailView.as_view(), name='library'),
]
