from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views import generic, View
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.db import transaction
from .forms import CustomUserCreationForm, ProjectDescriptionForm, MessageForm, GoalForm, MilestoneForm
from .models import Project, Goal, Milestone, Message
from decimal import Decimal

User = get_user_model()

# サインアップビュー
class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "signup.html"

# プロジェクトリストビュー（ログイン不要）
class ProjectListView(ListView):
    model = Project
    template_name = "project_list.html"

# プロジェクト詳細ビュー（ログイン不要）
class ProjectDetailView(DetailView):
    model = Project
    template_name = 'project_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_participant'] = self.request.user in self.object.participants.all() if self.request.user.is_authenticated else False
        
        # 既存のゴールとマイルストーンをコンテキストに追加
        goals_with_milestones = []
        for goal in self.object.goals.all():
            milestones = goal.milestones.filter(parent_milestone__isnull=True)
            goals_with_milestones.append({'goal': goal, 'milestones': milestones})
        context['goals_with_milestones'] = goals_with_milestones

        # チャットメッセージとフォームをコンテキストに追加
        if self.request.user.is_authenticated:
            context['message_form'] = MessageForm()
            context['messages'] = Message.objects.filter(project=self.object).order_by('-created_at')
        
        return context

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()  # プロジェクトオブジェクトを取得
        context = self.get_context_data(object=self.object)
        
        # メッセージフォームの処理
        message_form = MessageForm(data=request.POST)
        if message_form.is_valid():
            new_message = message_form.save(commit=False)
            new_message.project = self.object
            new_message.sender = request.user
            new_message.save()
            context['message_form'] = MessageForm()  # 次のメッセージ用にメッセージフォームをクリア
        else:
            context['message_form'] = message_form
        
        return self.render_to_response(context)

# プロジェクト作成ビュー（ログイン必要）
class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    fields = ['title', 'description']
    template_name = 'project_form.html'
    
    def get_initial(self):
        # 初期値を設定
        return {'description': 'プロジェクト憲章\n 社会的背景：\n ・\n\n 根本ニーズ：\n ・\n\n 我々はなぜここにいるのか：\n ・\n\n エレベーターピッチ：\n ・　　たい\n ・　　のための\n ・　　というプロダクトは\n ・　　\n ・これは　　を提供します\n ・　　とは違い\n ・　　する機能が備わっている\n\n'}

    def form_valid(self, form):
        # 現在のユーザーをオーナーとして設定
        form.instance.owner = self.request.user
        # フォームの内容を保存して、オブジェクトを作成
        return super().form_valid(form)

    def get_success_url(self):
        # 新しいプロジェクトの詳細ページにリダイレクト
        return reverse('project_detail', args=[self.object.id])

# カスタムログインビュー
class CustomLoginView(LoginView):
    template_name = 'login.html'
    def get_success_url(self):
        return reverse_lazy("project_list")  # 'project_list'はProjectListViewに設定されたURLの名前

# プロジェクト参加ビュー（ログイン必要）
class ProjectJoinView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        project.participants.add(request.user)
        return redirect('project_detail', pk=pk)

# アカウントビュー（ログイン必要）
class AccountView(LoginRequiredMixin, TemplateView):
    template_name = 'account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # ユーザーが参加しているプロジェクトを取得
        participating_projects = user.participating_projects.all()

        # 各プロジェクトについて達成マイルストーンのポイントを集計
        projects_data = []
        for project in participating_projects:
            completed_points = Milestone.objects.filter(
                goal__project=project,
                status='completed',
                assigned_to=user
            ).aggregate(Sum('points'))['points__sum'] or 0

            projects_data.append({
                'project': project,
                'completed_points': completed_points
            })

        # ユーザーが達成した全マイルストーンのポイントの合計
        total_completed_points = sum(data['completed_points'] for data in projects_data)

        context.update({
            'user': user,
            'projects_data': projects_data,
            'total_completed_points': total_completed_points
        })

        return context

# ゴール作成ビュー（ログイン必要）
class GoalCreateView(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'goal_form.html'

    def form_valid(self, form):
        project_id = self.kwargs['pk']
        project = get_object_or_404(Project, id=project_id)
        form.instance.project = project  # ゴールにプロジェクトを紐付け
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project_detail', kwargs={'pk': self.kwargs['pk']})

# マイルストーン作成ビュー（ログイン必要）
class MilestoneCreateView(LoginRequiredMixin, CreateView):
    model = Milestone
    form_class = MilestoneForm
    template_name = 'roadmap_form.html'

    def form_valid(self, form):
        goal = None  # 初期値をNoneに設定しておく
        initial_point = Decimal(1)  # ゴールのポイントは1とする
        
        goal_id = self.kwargs.get('goal_id')
        if goal_id:
            goal = get_object_or_404(Goal, id=goal_id)
            form.instance.goal = goal
        else:
            # goal_idがない場合は、親マイルストーンからゴールを設定
            parent_milestone_id = self.kwargs.get('parent_milestone_id')
            if parent_milestone_id:
                parent_milestone = get_object_or_404(Milestone, id=parent_milestone_id)
                form.instance.parent_milestone = parent_milestone
                form.instance.goal = parent_milestone.goal
                initial_point = parent_milestone.points
                goal = parent_milestone.goal  # goalを親マイルストーンのゴールに設定

        response = super().form_valid(form)
        
        if goal:  # goalが確実に設定されていることを確認
            self.update_all_milestone_points(goal)
        
        return response

    def update_all_milestone_points(self, goal):
        all_milestones = Milestone.objects.filter(goal=goal)
        num_children = all_milestones.filter(parent_milestone__isnull=True).count()
        points_per_child = Decimal(1) / num_children if num_children else Decimal(1)

        for milestone in all_milestones:
            if milestone.parent_milestone is None:
                milestone.points = points_per_child
            else:
                num_siblings = milestone.parent_milestone.child_milestones.count()
                milestone.points = milestone.parent_milestone.points / num_siblings
            milestone.save()

    def get_success_url(self):
        # 適切なリダイレクト先を設定
        return reverse('project_detail', kwargs={'pk': self.object.goal.project.id})

# マイルストーン更新ビュー（ログイン必要）
class MilestoneUpdateView(LoginRequiredMixin, UpdateView):
    model = Milestone
    fields = ['goal', 'parent_milestone', 'text', 'assigned_to', 'status']

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.recalculate_points()
        return response

# マイルストーン開始ビュー（ログイン必要）
class StartMilestoneView(LoginRequiredMixin, View):
    def post(self, request, pk):
        milestone = get_object_or_404(Milestone, pk=pk)
        milestone.assigned_to = request.user
        milestone.status = 'in_progress'
        milestone.save()
        return redirect('project_detail', pk=milestone.goal.project.id)

# マイルストーン完了ビュー（ログイン必要）
class CompleteMilestoneView(LoginRequiredMixin, View):
    def post(self, request, pk):
        milestone = get_object_or_404(Milestone, pk=pk)
        if milestone.assigned_to == request.user:
            milestone.status = 'completed'
            milestone.save()
        return redirect('project_detail', pk=milestone.goal.project.id)

# プロジェクト参加者のビュー（ログイン不要）
def project_participants(request, pk):
    project = get_object_or_404(Project, id=pk)
    participants = project.participants.all()

    # 各参加者の達成マイルストーンポイントを計算
    participants_data = []
    for participant in participants:
        completed_milestones = Milestone.objects.filter(
            assigned_to=participant, 
            status='completed',
            goal__project=project  # この行を追加して、マイルストーンがこのプロジェクトに属していることを保証
        )
        total_points = completed_milestones.aggregate(Sum('points'))['points__sum'] or 0
        participants_data.append({
            'participant': participant,
            'completed_milestones_points': total_points
        })

    context = {
        'project': project,
        'participants_data': participants_data
    }
    return render(request, 'project_participants.html', context)

# マイルストーン削除ビュー（ログイン必要）
@login_required
def delete_milestone(request, pk):
    milestone = get_object_or_404(Milestone, pk=pk)
    project = milestone.goal.project  # プロジェクトオブジェクトを保存

    if request.user not in project.participants.all():
        # ユーザーがプロジェクトの参加者でなければリダイレクト
        return redirect('project_detail', pk=project.pk)

    if request.method == 'POST':
        with transaction.atomic():
            # マイルストーンを削除
            milestone.delete()

            # ポイント再計算処理
            all_milestones = Milestone.objects.filter(goal=milestone.goal)
            if all_milestones.exists():
                num_children = all_milestones.filter(parent_milestone__isnull=True).count()
                points_per_child = Decimal('1.0') / num_children if num_children else Decimal('1.0')
                for ms in all_milestones:
                    if ms.parent_milestone is None:
                        ms.points = points_per_child
                    else:
                        num_siblings = ms.parent_milestone.child_milestones.count()
                        ms.points = ms.parent_milestone.points / num_siblings if num_siblings else Decimal('0.0')
                    ms.save()

        return redirect('project_detail', pk=project.pk)

    # POSTでない場合は削除確認ページを表示
    return render(request, 'milestone_confirm_delete.html', {'milestone': milestone})

# プロジェクト説明更新ビュー（ログイン必要）
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Project
from django.urls import reverse_lazy

class ProjectDescriptionUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    fields = ['description']
    template_name = 'project_description_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = self.get_form()
        context['form'].fields['description'].initial = self.object.description
        return context

    def get_success_url(self):
        return reverse_lazy('project_detail', kwargs={'pk': self.object.pk})