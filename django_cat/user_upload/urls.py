from django.urls import path
from . import views

app_name = 'user_upload'

urlpatterns = [
    path('', views.FileListView.as_view(), name='list'),
    path('upload/', views.FileUploadView.as_view(), name='upload'),
    path('files/<str:file_id>/delete/', views.FileDeleteView.as_view(), name='delete'),
    path('files/<str:file_id>/associate/', views.FileAssociationView.as_view(), name='assoc'),
]
