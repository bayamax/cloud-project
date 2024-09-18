from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # ユーザー登録
    path('signup/', views.SignUpView.as_view(), name='signup'),

    # プロジェクトのリスト表示
    path('projects/', views.ProjectListView.as_view(), name='project_list'),

    # プロジェクトの詳細表示
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),

    # プロジェクトの作成
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),

    # ログイン
    path('login/', views.CustomLoginView.as_view(), name='login'),

    # ログアウト
    path('logout/', LogoutView.as_view(), name='logout'),

    # プロジェクトへの参加
    path('projects/join/<int:pk>/', views.ProjectJoinView.as_view(), name='project_join'),

    # アカウントページ
    path('account/', views.AccountView.as_view(), name='account'),
    path('account/<str:username>/', views.AccountView.as_view(), name='account'),

    # ゴールの作成
    path('projects/<int:pk>/goal/create/', views.GoalCreateView.as_view(), name='goal_create'),

    # マイルストーンの作成
    path('goals/<int:goal_id>/milestone/create/', views.MilestoneCreateView.as_view(), name='milestone_create'),
    path('milestones/<int:parent_milestone_id>/milestone/create/', views.MilestoneCreateView.as_view(), name='milestone_create_with_parent'),

    # マイルストーンの操作
    path('milestones/<int:pk>/start/', views.StartMilestoneView.as_view(), name='start_milestone'),
    path('milestones/<int:pk>/complete/', views.CompleteMilestoneView.as_view(), name='complete_milestone'),
    path('milestone/deny/<int:pk>/', views.DenyMilestoneView.as_view(), name='deny_milestone'),
    path('milestone/<int:pk>/delete/', views.delete_milestone, name='delete_milestone'),

    # プロジェクト参加者の表示
    path('projects/<int:pk>/participants/', views.project_participants, name='project_participants'),

    # プロジェクト憲章の編集
    path('project/<int:pk>/edit_description/', views.project_description_update, name='edit_project_description'),
    path('project/<int:pk>/description/', views.project_description_form, name='project_description_form'),

    # マイルストーンの並び替え
    path('update_milestone_order/', views.update_milestone_order, name='update_milestone_order'),

    # GitHub URLの追加
    path('project/<int:pk>/add_github_url/', views.add_github_url, name='add_github_url'),

    # スレッドの詳細表示
    path('thread/<int:pk>/', views.ThreadDetailView.as_view(), name='thread_detail'),
]