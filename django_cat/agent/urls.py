from django.urls import path
from agent.views import (
    AgentListView,
    AgentCreateView,
    AgentDetailView,
    AgentDeleteView,
    AgentUpdateView,
)

app_name = 'agent'

urlpatterns = [
    path('', AgentListView.as_view(), name='home'),
    path('list/', AgentListView.as_view(), name='list'),
    path('new/', AgentCreateView.as_view(), name='create'),
    path('<str:agent_id>/', AgentDetailView.as_view(), name='detail'),
    path('<str:agent_id>/delete/', AgentDeleteView.as_view(), name='delete'),
    path('<str:agent_id>/edit/', AgentUpdateView.as_view(), name='update'),
]
