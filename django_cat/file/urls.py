from django.urls import path, include
from file import views
from file.api import router


app_name = 'file'

urlpatterns = [
    path('', views.FileListView.as_view(), name='list'),
    path('upload/', views.FileUploadView.as_view(), name='upload'),
    path('files/<str:file_id>/delete/', views.FileDeleteView.as_view(), name='delete'),
    path('files/<str:file_id>/associate/', views.FileAssociationView.as_view(), name='assoc'),

    path("api/", include((list(router.urls_paths("")), "api"), namespace="api")),
]
