from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Subject, Profile

# Create your views here.

@login_required
def profile(request):
    user = request.user
    user_profile = user.profile
    
    # Get all subjects for the template
    subjects = Subject.objects.all().order_by('name')
    
    # Get the user's currently selected subjects
    selected_subject_ids = list(user_profile.subjects.values_list('id', flat=True))
    
    if request.method == 'POST':
        # Update display name
        display_name = request.POST.get('display_name')
        if display_name:
            # Assuming the display name should update the user's first name
            user.first_name = display_name
            user.save()
        
        # Update bio - we need to add this field to the Profile model
        # This is just a placeholder as the bio field doesn't exist yet
        # bio = request.POST.get('bio')
        
        # Update selected subjects
        selected_subject_ids = request.POST.getlist('selected_subjects[]')
        
        if selected_subject_ids:
            # Clear existing subjects and add new ones
            user_profile.subjects.clear()
            for subject_id in selected_subject_ids:
                try:
                    subject = Subject.objects.get(id=subject_id)
                    user_profile.subjects.add(subject)
                except Subject.DoesNotExist:
                    continue
        
        # Update notification preferences
        user_profile.notify_on_join = 'notify_on_join' in request.POST
        user_profile.notify_on_message = 'notify_on_message' in request.POST
        user_profile.notify_on_new_group = 'notify_on_new_group' in request.POST
        
        # Save the profile
        user_profile.save()
        
        messages.success(request, "Your profile has been updated!")
        return redirect('dashboard')
    
    context = {
        'user': user,
        'subjects': subjects,
        'selected_subject_ids': selected_subject_ids,
        'profile': user_profile
    }
    
    return render(request, 'userProfile/profile.html', context)

@login_required
def profile_setup(request):
    user_profile = request.user.profile
    
    if request.method == 'POST':
        # Get selected subjects from the form
        selected_subject_ids = request.POST.getlist('selected_subjects[]')
        
        if selected_subject_ids:
            # Clear existing subjects and add new ones
            user_profile.subjects.clear()
            for subject_id in selected_subject_ids:
                try:
                    subject = Subject.objects.get(id=subject_id)
                    user_profile.subjects.add(subject)
                except Subject.DoesNotExist:
                    continue
            
            # Mark profile as completed
            user_profile.profile_completed = True
            user_profile.save()
            
            messages.success(request, "Your profile has been updated!")
            return redirect('profile')
    
    # Get all subjects for the template
    subjects = Subject.objects.all().order_by('name')
    
    # Get the user's currently selected subjects for pre-selection
    selected_subject_ids = list(user_profile.subjects.values_list('id', flat=True))
    
    return render(request, 'userProfile/profile_setup.html', {
        'subjects': subjects,
        'selected_subject_ids': selected_subject_ids
    })


