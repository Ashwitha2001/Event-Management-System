from django.contrib import admin
from .models import Profile, Event, EventPermission, EventHistory

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'location', 'start_time', 'end_time', 'created_by', 'is_recurring')
    list_filter = ('is_recurring', 'start_time')
    search_fields = ('title', 'description', 'location')

@admin.register(EventPermission)
class EventPermissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'event', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'event__title')

@admin.register(EventHistory)
class EventHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'event', 'edited_by', 'edited_at')
    list_filter = ('edited_at',)
    search_fields = ('event__title', 'edited_by__username')
