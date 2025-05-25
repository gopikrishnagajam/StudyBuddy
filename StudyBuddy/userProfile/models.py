from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class Subject(models.Model):
    """Model representing academic subjects"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']

class Profile(models.Model):
    """User profile with additional information"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    subjects = models.ManyToManyField(Subject, blank=True, related_name='interested_users')
    profile_completed = models.BooleanField(default=False)
    
    # Notification settings
    notify_on_join = models.BooleanField(default=True)
    notify_on_message = models.BooleanField(default=True)
    notify_on_new_group = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to create profile when a new user is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
