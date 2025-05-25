from django.urls import path
from . import views

urlpatterns = [
    path('dashboard', views.dashboard, name='dashboard'),
    path('create_group', views.create_group, name='create_group'),
    path('group_details/<int:group_id>', views.group_details, name='group_details'),
    path('group_details', views.group_details, name='group_details_default'),
    path('join_group/<int:group_id>', views.join_group, name='join_group'),
    path('leave_group/<int:group_id>', views.leave_group, name='leave_group'),
    path('edit_group/<int:group_id>', views.edit_group, name='edit_group'),
    path('approve_request/<int:request_id>', views.approve_request, name='approve_request'),
    path('decline_request/<int:request_id>', views.decline_request, name='decline_request'),
]
