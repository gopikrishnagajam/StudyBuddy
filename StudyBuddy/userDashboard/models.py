from django.db import models
from django.conf import settings
from userProfile.models import Subject
from django.urls import reverse
from django.utils import timezone

class StudyGroup(models.Model):
    """Model representing a study group"""
    title = models.CharField(max_length=100)
    description = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='study_groups')
    host = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hosted_groups')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='GroupMembership', related_name='joined_groups')
    max_members = models.PositiveIntegerField(default=8)
    meeting_date = models.DateField()
    meeting_time = models.TimeField()
    meeting_location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('group_details', args=[str(self.id)])
    
    @property
    def current_member_count(self):
        return self.members.count()
    
    @property
    def is_full(self):
        return self.current_member_count >= self.max_members
    
    @property
    def next_meeting_datetime(self):
        meeting_datetime = timezone.datetime.combine(self.meeting_date, self.meeting_time)
        return meeting_datetime
    
    class Meta:
        ordering = ['meeting_date', 'meeting_time']

class GroupMembership(models.Model):
    """Model representing the membership relationship between users and study groups"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'group')
        
    def __str__(self):
        return f"{self.user.username} in {self.group.title}"

class GroupMessage(models.Model):
    """Model for messages in a study group"""
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Message from {self.user.username} in {self.group.title} at {self.timestamp}"
    
    class Meta:
        ordering = ['timestamp']

class GroupJoinRequest(models.Model):
    """Model for handling group join requests requiring admin approval"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='join_requests')
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='join_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'group')
        ordering = ['-requested_at']
        
    def __str__(self):
        return f"{self.user.username}'s request to join {self.group.title} ({self.get_status_display()})"
