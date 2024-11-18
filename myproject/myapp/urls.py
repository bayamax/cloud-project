# myapp/urls.py

from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import (
    CustomLoginView, SignUpView, ProjectJoinView, account_view,
    GoalCreateView, MilestoneCreateView, StartMilestoneView,
    CompleteMilestoneView, project_participants, delete_milestone,
    project_description_update, project_description_form,
    update_milestone_order, ThreadListView, ThreadDetailView,
    BecomeOwnerView
)

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('projects/join/<int:pk>/', ProjectJoinView.as_view(), name='project_join'),
    path('account/', views.account_view, name='account'),
    path('account/<str:username>/', views.account_view, name='account_with_username'),
    path('projects/<int:pk>/goal/create/', GoalCreateView.as_view(), name='goal_create'),
    path('goals/<int:goal_id>/milestone/create/', views.MilestoneCreateView.as_view(), name='milestone_create'),
    path('milestones/<int:parent_milestone_id>/milestone/create/', views.MilestoneCreateView.as_view(), name='milestone_create_with_parent'),
    path('milestones/<int:pk>/start/', StartMilestoneView.as_view(), name='start_milestone'),
    path('milestones/<int:pk>/complete/', CompleteMilestoneView.as_view(), name='complete_milestone'),
    path('projects/<int:pk>/participants/', project_participants, name='project_participants'),
    path('milestone/<int:pk>/delete/', delete_milestone, name='delete_milestone'),
    path('project/<int:pk>/edit_description/', project_description_update, name='edit_project_description'),
    path('project/<int:pk>/description/', project_description_form, name='project_description_form'),
    path('update_milestone_order/', update_milestone_order, name='update_milestone_order'),
    path('milestone/deny/<int:pk>/', views.DenyMilestoneView.as_view(), name='deny_milestone'),
    path('project/<int:pk>/add_github_url/', views.add_github_url, name='add_github_url'),
    path('thread/<int:pk>/', ThreadDetailView.as_view(), name='thread_detail'),
    path('threads/', ThreadListView.as_view(), name='thread_list'),
    path('projects/<int:pk>/become_owner/', BecomeOwnerView.as_view(), name='become_owner'),
    path('projects/<int:pk>/initiate_payment/<int:participant_id>/', views.initiate_payment, name='initiate_payment'),
    path('payment_request/<int:pk>/update_status/<str:status>/', views.update_payment_status, name='update_payment_status'),
]