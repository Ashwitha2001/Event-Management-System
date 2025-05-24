from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True) 
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True, null=True, help_text="Recurrence pattern like 'daily', 'weekly', 'monthly'")

    def __str__(self):
        return self.title


class EventPermission(models.Model):
    PERMISSION_ROLES = [
        ('owner', 'Owner'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_permissions')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='permissions')
    role = models.CharField(max_length=10, choices=PERMISSION_ROLES)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.role})"


class EventHistory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='history')
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    edited_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event.title} edited by {self.edited_by.username if self.edited_by else 'Unknown'}"


