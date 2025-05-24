from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, LoginView, RefreshView, LogoutView,
    EventViewSet, BatchEventCreateView, ShareEventView,
    EventHistoryView, EventHistoryDetailView, EventRollbackView, EventDiffView,
    EventPermissionListView, UpdateOrRevokePermissionView,
)

router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')

urlpatterns = [

    # Authentication Endpoints
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),

    # Event Creation / Batch 
    path('events/batch/', BatchEventCreateView.as_view(), name='batch-create-events'),

    # Event Sharing 
    path('events/<int:pk>/share/', ShareEventView.as_view(), name='event-share'),

    # Permissions Management 
    path('events/<int:pk>/permissions/', EventPermissionListView.as_view(), name='event-permissions-list'),
    path('events/<int:event_id>/permissions/<int:user_id>/', UpdateOrRevokePermissionView.as_view(), name='event-permissions-update-or-revoke'),

    # Version History & Rollback 
    path('events/<int:pk>/changelog/', EventHistoryView.as_view(), name='event-changelog'),
    path('events/<int:id>/history/<int:versionId>/', EventHistoryDetailView.as_view(), name='event-history-detail'),
    path('events/<int:event_id>/rollback/<int:version_id>/', EventRollbackView.as_view(), name='event-rollback'),

    # Changelog & Diff
    path('events/<int:event_id>/diff/<int:v1_id>/<int:v2_id>/', EventDiffView.as_view(), name='event-diff'),

    # ViewSet Routes for basic CRUD 
    path('', include(router.urls)),
]
