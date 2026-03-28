from django.contrib import admin
from .models import User, Club, Membership, Event, Thread, ThreadMessage, DirectMessage

admin.site.register(User)
admin.site.register(Club)
admin.site.register(Membership)
admin.site.register(Event)

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'club', 'created_by', 'created_at', 'is_announcement']
    list_filter = ['club', 'is_announcement']

@admin.register(ThreadMessage)
class ThreadMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'thread', 'created_at', 'is_pinned']
    list_filter = ['is_pinned']

@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'created_at', 'is_read']
    