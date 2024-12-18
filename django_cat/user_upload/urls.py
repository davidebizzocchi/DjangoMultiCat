from django.urls import path
from . import views

app_name = 'user_upload'

urlpatterns = [
    path('upload/', views.FileUploadView.as_view(), name='upload_file'),
    path('files/', views.FileListView.as_view(), name='file_list'),
    path('files/<str:file_id>/delete/', views.FileDeleteView.as_view(), name='file-delete'),
    path('files/<str:file_id>/associate/', views.FileAssociationView.as_view(), name='file-assoc'),
]
