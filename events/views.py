from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegisterSerializer, CustomTokenObtainPairSerializer, EventSerializer, EventPermissionSerializer, EventHistorySerializer
from rest_framework import viewsets, permissions
from .models import Event, EventPermission, EventHistory
from rest_framework.permissions import IsAuthenticated
from deepdiff import DeepDiff
from django_ratelimit.decorators import ratelimit
from .permissions import IsEventOwner, IsEventEditorOrOwner, IsEventViewerOrAbove
from django.utils.decorators import method_decorator


@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User registered successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshView(TokenRefreshView):
    pass


class LogoutView(APIView):
    """
    Logout by blacklisting the refresh token.
    Client must send {"refresh": "<refresh_token>"}
    """
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, IsEventEditorOrOwner]
        elif self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsEventOwner]
        elif self.action == 'retrieve':
            permission_classes = [IsAuthenticated, IsEventViewerOrAbove]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        event = serializer.save(created_by=self.request.user)
        # Owner automatically gets owner role permission on created event
        EventPermission.objects.create(user=self.request.user, event=event, role='owner')

    def perform_update(self, serializer):
        event = self.get_object()
        # Save edit history before update
        EventHistory.objects.create(
            event=event,
            edited_by=self.request.user,
            title=event.title,
            description=event.description,
            location=event.location,
            start_time=event.start_time,
            end_time=event.end_time,
        )
        serializer.save()


@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class BatchEventCreateView(APIView):
    def post(self, request):
        serializer = EventSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Events created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShareEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response({'detail': 'Event not found'}, status=404)

        # Permission check, only owners can share
        try:
            role = EventPermission.objects.get(user=request.user, event=event).role
        except EventPermission.DoesNotExist:
            return Response({'detail': 'No permission on this event'}, status=403)

        if role != 'owner':
            return Response({'detail': 'Only owners can share the event.'}, status=403)

        data = request.data.copy()
        data['event'] = pk

        serializer = EventPermissionSerializer(data=data)
        if serializer.is_valid():
            shared_permission = serializer.save()

            # Real-time notification
            from .utils import notify_user
            notify_user(shared_permission.user.id, f"You've been added to the event: '{event.title}'")

            return Response({'message': 'Event shared successfully.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventPermissionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response({'detail': 'Event not found'}, status=404)

        # Only owner can view permission list
        try:
            role = EventPermission.objects.get(user=request.user, event=event).role
        except EventPermission.DoesNotExist:
            return Response({'detail': 'No permission on this event'}, status=403)

        if role != 'owner':
            return Response({'detail': 'Only the owner can view permission list'}, status=403)

        permissions = EventPermission.objects.filter(event=event)
        serializer = EventPermissionSerializer(permissions, many=True)
        return Response(serializer.data)


class UpdateOrRevokePermissionView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, event_id, user_id):
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return Response({'detail': 'Event not found'}, status=404)

        if not EventPermission.objects.filter(event=event, user=request.user, role='owner').exists():
            return Response({'detail': 'Only owners can update roles.'}, status=403)

        try:
            perm = EventPermission.objects.get(event=event, user_id=user_id)
        except EventPermission.DoesNotExist:
            return Response({'detail': 'Permission not found.'}, status=404)

        new_role = request.data.get('role')
        if new_role not in ['owner', 'editor', 'viewer']:
            return Response({'detail': 'Invalid role.'}, status=400)

        perm.role = new_role
        perm.save()
        return Response({'message': 'Role updated successfully.'})

    def delete(self, request, event_id, user_id):
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return Response({'detail': 'Event not found'}, status=404)

        if not EventPermission.objects.filter(event=event, user=request.user, role='owner').exists():
            return Response({'detail': 'Only owners can revoke permissions.'}, status=403)

        try:
            perm = EventPermission.objects.get(event=event, user_id=user_id)
        except EventPermission.DoesNotExist:
            return Response({'detail': 'Permission not found.'}, status=404)

        perm.delete()
        return Response({'message': 'Permission revoked successfully.'})



@method_decorator(ratelimit(key='ip', rate='5/m', block=True), name='dispatch')
class EventHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return Response({'detail': 'Event not found'}, status=404)

        history = event.history.all().order_by('-edited_at')
        serializer = EventHistorySerializer(history, many=True)
        return Response(serializer.data)


class EventHistoryDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEventViewerOrAbove]

    def get(self, request, id, versionId):
        try:
            history_version = EventHistory.objects.get(pk=versionId, event_id=id)
        except EventHistory.DoesNotExist:
            return Response({'detail': 'History version not found'}, status=404)

        serializer = EventHistorySerializer(history_version)
        return Response(serializer.data)



class EventDiffView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, event_id, v1_id, v2_id):
        try:
            version1 = EventHistory.objects.get(pk=v1_id, event_id=event_id)
            version2 = EventHistory.objects.get(pk=v2_id, event_id=event_id)
        except EventHistory.DoesNotExist:
            return Response({'detail': 'One or both versions not found'}, status=404)

        # Convert both versions to plain dictionaries
        v1_data = {
            "title": version1.title,
            "description": version1.description,
            "location": version1.location,
            "start_time": str(version1.start_time),
            "end_time": str(version1.end_time),
        }

        v2_data = {
            "title": version2.title,
            "description": version2.description,
            "location": version2.location,
            "start_time": str(version2.start_time),
            "end_time": str(version2.end_time),
        }

        diff = DeepDiff(v1_data, v2_data, ignore_order=True)
        return Response(diff)


class EventRollbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, event_id, version_id):
        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return Response({'detail': 'Event not found'}, status=404)

        try:
            version = EventHistory.objects.get(pk=version_id, event=event)
        except EventHistory.DoesNotExist:
            return Response({'detail': 'Version not found'}, status=404)

        # Only creator or editor can rollback
        if event.created_by != request.user and not EventPermission.objects.filter(event=event, user=request.user, role__in=['owner', 'editor']).exists():
            return Response({'detail': 'You do not have permission to rollback this event.'}, status=403)

        # Save current as new history before rollback
        EventHistory.objects.create(
            event=event,
            edited_by=request.user,
            title=event.title,
            description=event.description,
            location=event.location,
            start_time=event.start_time,
            end_time=event.end_time,
        )

        # Perform rollback
        event.title = version.title
        event.description = version.description
        event.location = version.location
        event.start_time = version.start_time
        event.end_time = version.end_time
        event.save()

        return Response({'message': 'Event rolled back to selected version.'})
