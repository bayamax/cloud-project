from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import (
    CustomLoginView, SignUpView, ProjectJoinView, AccountView,
    GoalCreateView, MilestoneCreateView, StartMilestoneView,
    CompleteMilestoneView, project_participants, delete_milestone,
    project_description_update, project_description_form,
    update_milestone_order, ThreadListView, ThreadDetailView,
    BecomeOwnerView
)

urlpatterns = [
    # ユーザー登録
    path('signup/', SignUpView.as_view(), name='signup'),

    # プロジェクトのリスト表示
    path('projects/', views.ProjectListView.as_view(), name='project_list'),

    # プロジェクトの詳細表示
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),

    # プロジェクトの作成
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),

    # ログイン
    path('login/', CustomLoginView.as_view(), name='login'),

    # ログアウト
    path('logout/', LogoutView.as_view(), name='logout'),

    # プロジェクトへの参加
    path('projects/join/<int:pk>/', ProjectJoinView.as_view(), name='project_join'),

    # アカウントページ
    path('account/', AccountView.as_view(), name='account'),
    path('account/<str:username>/', AccountView.as_view(), name='account'),

    # ゴールの作成（プロジェクトIDを指定）
    path('projects/<int:pk>/goal/create/', GoalCreateView.as_view(), name='goal_create'),

    # マイルストーンの作成（ゴールIDを指定）
    path('goals/<int:goal_id>/milestone/create/', MilestoneCreateView.as_view(), name='milestone_create'),

    # 子マイルストーンの作成（親マイルストーンIDを指定）
    path('milestones/<int:parent_milestone_id>/milestone/create/', MilestoneCreateView.as_view(), name='milestone_create_with_parent'),
    
    path('milestones/<int:pk>/start/', StartMilestoneView.as_view(), name='start_milestone'),
    
    path('milestones/<int:pk>/complete/', CompleteMilestoneView.as_view(), name='complete_milestone'),
    
    path('projects/<int:pk>/participants/', project_participants, name='project_participants'),
    
    path('milestone/<int:pk>/delete/', delete_milestone, name='delete_milestone'),
    
    # プロジェクト説明更新ビュー
    path('project/<int:pk>/edit_description/', project_description_update, name='edit_project_description'),
    path('project/<int:pk>/description/', project_description_form, name='project_description_form'),
    
    # マイルストーンの並び替え
    path('update_milestone_order/', update_milestone_order, name='update_milestone_order'),
    
    # マイルストーン拒否ビュー
    path('milestone/deny/<int:pk>/', views.DenyMilestoneView.as_view(), name='deny_milestone'),
    
    # GitHub URLの追加
    path('project/<int:pk>/add_github_url/', views.add_github_url, name='add_github_url'),
    
    # スレッド関連
    path('thread/<int:pk>/', ThreadDetailView.as_view(), name='thread_detail'),
    path('threads/', ThreadListView.as_view(), name='thread_list'),

    # オーナーになる機能の追加
    path('projects/<int:pk>/become_owner/', BecomeOwnerView.as_view(), name='become_owner'),
]