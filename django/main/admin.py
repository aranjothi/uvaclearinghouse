from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Club, Membership


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'profile_slug')
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('profile_slug',)}),
    )


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'club', 'role')
    list_filter = ('role', 'club')
