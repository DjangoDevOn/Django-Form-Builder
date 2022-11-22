from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_admin')
    list_filter = ('is_admin',)

    fieldsets = (
        (None, {'fields': ('team_user', 'manager_id', 'email', 'password', 'profile_photo', 'first_name', 'last_name',)}),
        ('Permissions', {'fields': ('is_admin', 'is_staff','is_active')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )

    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
admin.site.register(Feedback)