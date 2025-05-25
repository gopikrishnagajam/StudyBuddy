from django.contrib import admin
from .models import StudyGroup, GroupMembership, GroupMessage, GroupJoinRequest
from django.utils import timezone

class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1

class GroupMessageInline(admin.TabularInline):
    model = GroupMessage
    extra = 0
    readonly_fields = ('user', 'content', 'timestamp')

@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'host', 'meeting_date', 'meeting_time', 'current_member_count')
    list_filter = ('subject', 'meeting_date')
    search_fields = ('title', 'description', 'host__username')
    inlines = [GroupMembershipInline, GroupMessageInline]

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'date_joined', 'is_active')
    list_filter = ('is_active', 'date_joined')
    search_fields = ('user__username', 'group__title')

@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'short_content', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('content', 'user__username', 'group__title')
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'

@admin.register(GroupJoinRequest)
class GroupJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'status', 'requested_at', 'responded_at')
    list_filter = ('status', 'requested_at', 'responded_at')
    search_fields = ('user__username', 'group__title')
    readonly_fields = ('requested_at',)
    actions = ['approve_requests', 'decline_requests']
    
    def approve_requests(self, request, queryset):
        for join_request in queryset.filter(status='pending'):
            join_request.status = 'approved'
            join_request.responded_at = timezone.now()
            join_request.save()
            
            # Add user to group
            GroupMembership.objects.create(
                user=join_request.user,
                group=join_request.group
            )
        
        self.message_user(request, f"{queryset.filter(status='pending').count()} request(s) approved successfully.")
    approve_requests.short_description = "Approve selected requests"
    
    def decline_requests(self, request, queryset):
        count = queryset.filter(status='pending').update(
            status='declined', 
            responded_at=timezone.now()
        )
        self.message_user(request, f"{count} request(s) declined successfully.")
    decline_requests.short_description = "Decline selected requests"
