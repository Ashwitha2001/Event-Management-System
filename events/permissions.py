from rest_framework import permissions
from .models import EventPermission

class IsEventOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        try:
            role = EventPermission.objects.get(user=request.user, event=obj).role
            return role == 'owner'
        except EventPermission.DoesNotExist:
            return False

class IsEventEditorOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        try:
            role = EventPermission.objects.get(user=request.user, event=obj).role
            return role in ['owner', 'editor']
        except EventPermission.DoesNotExist:
            return False

class IsEventViewerOrAbove(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        try:
            role = EventPermission.objects.get(user=request.user, event=obj).role
            return role in ['owner', 'editor', 'viewer']
        except EventPermission.DoesNotExist:
            return False
