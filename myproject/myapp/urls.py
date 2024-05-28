from django.urls import path, include
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from . import views
from .views import (
    CustomLoginView, SignUpView, ProjectJoinView, AccountView,
    GoalCreateView, MilestoneCreateView, StartMilestoneView,
    CompleteMilestoneView, project_participants, delete_milestone,
    ProjectDescriptionUpdateView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # 追加

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

    # マイルストーンの開始
    path('milestones/<int:pk>/start/', StartMilestoneView.as_view(), name='start_milestone'),

    # マイルストーンの完了
    path('milestones/<int:pk>/complete/', CompleteMilestoneView.as_view(), name='complete_milestone'),

    # プロジェクトの参加者リスト
    path('projects/<int:pk>/participants/', project_participants, name='project_participants'),

    # マイルストーンの削除
    path('milestone/<int:pk>/delete/', delete_milestone, name='delete_milestone'),

    # プロジェクトの説明の編集
    path('project/<int:pk>/edit_description/', ProjectDescriptionUpdateView.as_view(), name='edit_project_description'),
]