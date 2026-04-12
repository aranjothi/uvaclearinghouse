from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Club, Membership, Event, DirectMessage, Announcement


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'profile_slug', 'is_user_admin')
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('profile_slug', 'age', 'birthday', 'year', 'school', 'profile_picture')}),
        ('Site Role', {'fields': ('is_user_admin',)}),
    )


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'executive_code')
    readonly_fields = ('executive_code',)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'club', 'role')
    list_filter = ('role', 'club')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'date')


@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'created_at', 'is_read')
    list_filter = ('is_read',)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'author', 'visibility', 'created_at')
    list_filter = ('visibility', 'club')