from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Event,  EventPermission,  EventHistory

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
        }
        return data

class EventSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'location',
            'start_time', 'end_time', 'created_by',
            'created_at', 'is_recurring', 'recurrence_pattern'
        ]
        read_only_fields = ['created_by', 'created_at']

    def validate(self, data):
        user = self.context['request'].user

        # Use updated data if present, otherwise fall back to existing instance values if available
        start_time = data.get('start_time') if 'start_time' in data else (self.instance.start_time if self.instance else None)
        end_time = data.get('end_time') if 'end_time' in data else (self.instance.end_time if self.instance else None)

        # Only validate if both are provided
        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError("End time must be after start time.")

            # Conflict detection for overlapping events
            overlapping = Event.objects.filter(
                created_by=user,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
           
            if self.instance:
                overlapping = overlapping.exclude(id=self.instance.id)

            if overlapping.exists():
                raise serializers.ValidationError("This event conflicts with another scheduled event.")

        return data

class BatchEventSerializer(serializers.ListSerializer):
    child = EventSerializer()

    def create(self, validated_data):
        events = [Event(**item) for item in validated_data]
        return Event.objects.bulk_create(events)


class EventPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventPermission
        fields = ('user', 'event', 'role')

    def validate(self, data):
        if data['role'] not in ['owner', 'editor', 'viewer']:
            raise serializers.ValidationError("Invalid role")
        return data
    

class EventHistorySerializer(serializers.ModelSerializer):
    edited_by = serializers.StringRelatedField()

    class Meta:
        model = EventHistory
        fields = '__all__'



