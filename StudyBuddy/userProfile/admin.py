from django.contrib import admin
from .models import Subject, Profile

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'profile_completed')
    list_filter = ('profile_completed', 'notify_on_join', 'notify_on_message', 'notify_on_new_group')
    search_fields = ('user__username', 'user__email')
    filter_horizontal = ('subjects',)
