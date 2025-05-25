from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import StudyGroup, GroupMembership, GroupMessage, GroupJoinRequest
from userProfile.models import Subject
from django.utils import timezone
import datetime

# Create your views here.

@login_required
def dashboard(request):
    # Get all study groups ordered by creation date (newest first)
    study_groups = StudyGroup.objects.all().order_by('-created_at')
    
    # Get filter parameters from GET request
    subject_filter = request.GET.get('subject')
    search_query = request.GET.get('search')
    
    # Apply filters if they exist
    if subject_filter:
        study_groups = study_groups.filter(subject_id=subject_filter)
    
    if search_query:
        study_groups = study_groups.filter(title__icontains=search_query)
    
    # Get all subjects for filter dropdown
    subjects = Subject.objects.all().order_by('name')
    
    # Get pending requests for each group where the user is the host
    pending_requests_by_group = {}
    for group in study_groups.filter(host=request.user):
        pending_count = GroupJoinRequest.objects.filter(group=group, status='pending').count()
        if pending_count > 0:
            pending_requests_by_group[group.id] = pending_count
    
    # Check for user's pending requests
    user_pending_requests = []
    if request.user.is_authenticated:
        user_pending_requests = list(GroupJoinRequest.objects.filter(
            user=request.user, 
            status='pending'
        ).values_list('group_id', flat=True))
    
    context = {
        'study_groups': study_groups,
        'subjects': subjects,
        'selected_subject': subject_filter,
        'search_query': search_query,
        'pending_requests_by_group': pending_requests_by_group,
        'user_pending_requests': user_pending_requests
    }
    
    return render(request, 'userDashboard/dashboard.html', context)

@login_required
def create_group(request):
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('group_title')
        subject_id = request.POST.get('subject')
        description = request.POST.get('description')
        meeting_date_str = request.POST.get('meeting_date')
        meeting_time_str = request.POST.get('meeting_time')
        max_members = request.POST.get('max_members')
        location = request.POST.get('location', '')
        
        # Parse date and time
        try:
            # This assumes the datepicker returns date in MM/DD/YYYY format
            month, day, year = meeting_date_str.split('/')
            meeting_date = datetime.date(int(year), int(month), int(day))
            
            # This assumes the timepicker returns time in HH:MM AM/PM format
            time_parts = meeting_time_str.split(' ')
            hour, minute = time_parts[0].split(':')
            hour = int(hour)
            minute = int(minute)
            
            # Adjust for PM
            if time_parts[1] == 'PM' and hour < 12:
                hour += 12
            # Adjust for 12 AM
            if time_parts[1] == 'AM' and hour == 12:
                hour = 0
                
            meeting_time = datetime.time(hour, minute)
        except (ValueError, IndexError):
            messages.error(request, "Invalid date or time format. Please try again.")
            return render(request, 'userDashboard/create_group.html')
        
        try:
            # Get the subject
            subject = Subject.objects.get(id=subject_id)
            
            # Create the study group
            study_group = StudyGroup.objects.create(
                title=title,
                description=description,
                subject=subject,
                host=request.user,
                max_members=max_members,
                meeting_date=meeting_date,
                meeting_time=meeting_time,
                meeting_location=location
            )
            
            # Add the creator as a member
            GroupMembership.objects.create(
                user=request.user,
                group=study_group
            )
            
            messages.success(request, f"Study group '{title}' has been created successfully!")
            return redirect('group_details', group_id=study_group.id)
        
        except Subject.DoesNotExist:
            messages.error(request, "Selected subject doesn't exist. Please try again.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    
    # GET request
    subjects = Subject.objects.all().order_by('name')
    return render(request, 'userDashboard/create_group.html', {'subjects': subjects})

@login_required
def group_details(request, group_id=None):
    if group_id:
        try:
            group = StudyGroup.objects.get(id=group_id)
            
            # Check if user is a member of this group
            is_member = group.members.filter(id=request.user.id).exists()
            is_host = group.host == request.user
            
            # Check if user has a pending join request
            has_pending_request = GroupJoinRequest.objects.filter(
                user=request.user, 
                group=group, 
                status='pending'
            ).exists()
            
            # Get pending join requests if user is host
            pending_requests = []
            if is_host:
                pending_requests = GroupJoinRequest.objects.filter(
                    group=group,
                    status='pending'
                ).select_related('user')
            
            # Get all messages for this group
            messages_list = group.messages.all().order_by('timestamp')
            
            # Handle message posting
            if request.method == 'POST' and (is_member or is_host):
                message_content = request.POST.get('message')
                if message_content:
                    # Create the message
                    GroupMessage.objects.create(
                        group=group,
                        user=request.user,
                        content=message_content
                    )
                    return redirect('group_details', group_id=group.id)
            
            context = {
                'group': group,
                'is_member': is_member,
                'is_host': is_host,
                'has_pending_request': has_pending_request,
                'pending_requests': pending_requests,
                'messages_list': messages_list
            }
            return render(request, 'userDashboard/group_detail.html', context)
        except StudyGroup.DoesNotExist:
            messages.error(request, "Study group not found.")
            return redirect('dashboard')
    return render(request, 'userDashboard/group_detail.html')

@login_required
def join_group(request, group_id):
    try:
        group = StudyGroup.objects.get(id=group_id)
        
        # Check if the user is already a member
        if group.members.filter(id=request.user.id).exists():
            messages.warning(request, "You are already a member of this group.")
        # Check if the user already has a pending request
        elif GroupJoinRequest.objects.filter(user=request.user, group=group, status='pending').exists():
            messages.info(request, "You already have a pending request to join this group.")
        elif group.is_full:
            messages.error(request, "This group is already full.")
        else:
            # Check if there's an existing declined request
            existing_request = GroupJoinRequest.objects.filter(
                user=request.user, 
                group=group, 
                status='declined'
            ).first()
            
            if existing_request:
                # Update the existing declined request to pending
                existing_request.status = 'pending'
                existing_request.requested_at = timezone.now()
                existing_request.responded_at = None
                existing_request.save()
                messages.success(request, f"Your request to join {group.title} has been resubmitted to the group host!")
            else:
                # Create a new join request
                GroupJoinRequest.objects.create(
                    user=request.user,
                    group=group,
                    status='pending'
                )
                messages.success(request, f"Your request to join {group.title} has been sent to the group host!")
    except StudyGroup.DoesNotExist:
        messages.error(request, "Study group not found.")
    
    return redirect('group_details', group_id=group_id)

@login_required
def approve_request(request, request_id):
    join_request = get_object_or_404(GroupJoinRequest, id=request_id, status='pending')
    
    # Security check - only the host can approve requests
    if request.user != join_request.group.host:
        messages.error(request, "Only the group host can approve join requests.")
        return redirect('group_details', group_id=join_request.group.id)
    
    # Check if the group is full
    if join_request.group.is_full:
        messages.error(request, "This group is already full. Cannot approve more members.")
        join_request.status = 'declined'
        join_request.responded_at = timezone.now()
        join_request.save()
        return redirect('group_details', group_id=join_request.group.id)
    
    # Approve the request and add the user to the group
    join_request.status = 'approved'
    join_request.responded_at = timezone.now()
    join_request.save()
    
    # Create the membership
    GroupMembership.objects.create(
        user=join_request.user,
        group=join_request.group
    )
    
    messages.success(request, f"You have approved {join_request.user.username}'s request to join your group.")
    return redirect('group_details', group_id=join_request.group.id)

@login_required
def decline_request(request, request_id):
    join_request = get_object_or_404(GroupJoinRequest, id=request_id, status='pending')
    
    # Security check - only the host can decline requests
    if request.user != join_request.group.host:
        messages.error(request, "Only the group host can decline join requests.")
        return redirect('group_details', group_id=join_request.group.id)
    
    # Decline the request
    join_request.status = 'declined'
    join_request.responded_at = timezone.now()
    join_request.save()
    
    messages.success(request, f"You have declined {join_request.user.username}'s request to join your group.")
    return redirect('group_details', group_id=join_request.group.id)

@login_required
def leave_group(request, group_id):
    try:
        group = StudyGroup.objects.get(id=group_id)
        
        # Check if the user is the host
        if group.host == request.user:
            messages.warning(request, "As the host, you cannot leave the group. You can delete it instead.")
        else:
            # Check if the user is a member
            membership = GroupMembership.objects.filter(
                user=request.user,
                group=group
            ).first()
            
            if membership:
                membership.delete()
                messages.success(request, f"You have left {group.title}.")
            else:
                messages.warning(request, "You are not a member of this group.")
    except StudyGroup.DoesNotExist:
        messages.error(request, "Study group not found.")
    
    return redirect('dashboard')

@login_required
def edit_group(request, group_id):
    try:
        group = StudyGroup.objects.get(id=group_id)
        
        # Check if the user is the host
        if group.host != request.user:
            messages.error(request, "Only the host can edit the group details.")
            return redirect('group_details', group_id=group_id)
        
        if request.method == 'POST':
            # Get form data
            title = request.POST.get('group_title')
            subject_id = request.POST.get('subject')
            description = request.POST.get('description')
            meeting_date_str = request.POST.get('meeting_date')
            meeting_time_str = request.POST.get('meeting_time')
            max_members = request.POST.get('max_members')
            location = request.POST.get('location', '')
            
            # Check if max_members is at least equal to current member count
            current_member_count = group.current_member_count
            try:
                max_members = int(max_members)
                if max_members < current_member_count:
                    messages.error(request, f"Maximum members cannot be less than the current member count ({current_member_count}).")
                    subjects = Subject.objects.all().order_by('name')
                    return render(request, 'userDashboard/edit_group.html', {
                        'group': group,
                        'subjects': subjects
                    })
            except ValueError:
                messages.error(request, "Invalid maximum members value.")
                subjects = Subject.objects.all().order_by('name')
                return render(request, 'userDashboard/edit_group.html', {
                    'group': group,
                    'subjects': subjects
                })
            
            # Parse date and time
            try:
                # This assumes the datepicker returns date in MM/DD/YYYY format
                month, day, year = meeting_date_str.split('/')
                meeting_date = datetime.date(int(year), int(month), int(day))
                
                # This assumes the timepicker returns time in HH:MM AM/PM format
                time_parts = meeting_time_str.split(' ')
                hour, minute = time_parts[0].split(':')
                hour = int(hour)
                minute = int(minute)
                
                # Adjust for PM
                if time_parts[1] == 'PM' and hour < 12:
                    hour += 12
                # Adjust for 12 AM
                if time_parts[1] == 'AM' and hour == 12:
                    hour = 0
                    
                meeting_time = datetime.time(hour, minute)
            except (ValueError, IndexError):
                messages.error(request, "Invalid date or time format. Please try again.")
                return render(request, 'userDashboard/edit_group.html', {'group': group})
            
            try:
                # Get the subject
                subject = Subject.objects.get(id=subject_id)
                
                # Update the group
                group.title = title
                group.description = description
                group.subject = subject
                group.max_members = max_members
                group.meeting_date = meeting_date
                group.meeting_time = meeting_time
                group.meeting_location = location
                group.save()
                
                messages.success(request, f"Study group '{title}' has been updated successfully!")
                return redirect('group_details', group_id=group.id)
            
            except Subject.DoesNotExist:
                messages.error(request, "Selected subject doesn't exist. Please try again.")
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        
        # GET request
        subjects = Subject.objects.all().order_by('name')
        return render(request, 'userDashboard/edit_group.html', {
            'group': group,
            'subjects': subjects
        })
    except StudyGroup.DoesNotExist:
        messages.error(request, "Study group not found.")
        return redirect('dashboard')
