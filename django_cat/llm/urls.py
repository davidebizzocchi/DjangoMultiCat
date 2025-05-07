from django.urls import path
from llm.views import (
    CreateLLMView, 
    LLMListView, 
    LLMDetailView, 
    LLMUpdateView, 
    LLMDeleteView
)

app_name = 'llm'

urlpatterns = [
    path('', LLMListView.as_view(), name='list'),
    path('create/', CreateLLMView.as_view(), name='create'),
    path('<int:pk>/', LLMDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', LLMUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', LLMDeleteView.as_view(), name='delete'),
]
