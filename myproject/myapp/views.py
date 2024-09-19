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
from decimal import Decimal
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from .forms import (
    CustomUserCreationForm, ProjectDescriptionForm, MessageForm,
    GoalForm, MilestoneForm, ThreadForm, ThreadMessageForm, GitHubURLForm
)
from .models import (
    Project, Goal, Milestone, Message, Thread, ThreadMessage
)

User = get_user_model()

# サインアップビュー
class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "signup.html"

# プロジェクトリストビュー（ログイン不要）
class ProjectListView(View):
    def get(self, request):
        projects = Project.objects.all()
        threads = Thread.objects.all().order_by('-created_at')
        thread_form = ThreadForm()
        return render(request, 'project_list.html', {
            'projects': projects,
            'threads': threads,
            'thread_form': thread_form,
        })

    def post(self, request):
        form = ThreadForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect('project_list')

# スレッド詳細ビュー
class ThreadDetailView(View):
    def get(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        messages = thread.messages.all().order_by('-created_at')
        message_form = ThreadMessageForm()
        return render(request, 'thread_detail.html', {
            'thread': thread,
            'messages': messages,
            'message_form': message_form,
        })

    def post(self, request, pk):
        thread = get_object_or_404(Thread, pk=pk)
        form = ThreadMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.thread = thread
            if request.user.is_authenticated:
                message.sender = request.user
            else:
                message.sender = None
            message.save()
        return redirect('thread_detail', pk=pk)

# スレッドリストビュー
class ThreadListView(View):
    def get(self, request):
        threads = Thread.objects.all().order_by('-created_at')
        thread_form = ThreadForm()
        return render(request, 'thread_list.html', {'threads': threads, 'thread_form': thread_form})

    def post(self, request):
        form = ThreadForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect('thread_list')

# プロジェクト詳細ビュー（ログイン不要）
class ProjectDetailView(DetailView):
    model = Project
    template_name = 'project_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        project = self.get_object()
        has_owner = project.owner is not None

        if has_owner and not request.user.is_authenticated:
            return redirect('login')

        context = self.get_context_data(object=project)
        message_form = MessageForm(data=request.POST)
        if message_form.is_valid():
            new_message = message_form.save(commit=False)
            new_message.project = project
            if request.user.is_authenticated:
                new_message.sender = request.user
            else:
                new_message.sender = None
            new_message.save()
            context['message_form'] = MessageForm()
        else:
            context['message_form'] = message_form

        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        user = self.request.user
        is_authenticated = user.is_authenticated
        has_owner = project.owner is not None

        if has_owner:
            is_participant = is_authenticated and user in project.participants.all()
        else:
            is_participant = True

        context['is_participant'] = is_participant
        context['project'] = project

        goals = project.goals.all()
        goals_with_milestones = []

        for goal in goals:
            milestones = goal.milestones.all().order_by('order')
            goals_with_milestones.append({'goal': goal, 'milestones': milestones})

        context['goals_with_milestones'] = goals_with_milestones
        context['message_form'] = MessageForm()
        context['messages'] = project.messages.all().order_by('-created_at')

        total_points = Milestone.objects.filter(goal__project=project).aggregate(Sum('points'))['points__sum'] or 0
        completed_points = Milestone.objects.filter(goal__project=project, status='completed').aggregate(Sum('points'))['points__sum'] or 0
        context['total_points'] = total_points
        context['completed_points'] = completed_points
        if total_points > 0:
            context['progress_percentage'] = int((completed_points / total_points) * 100)
        else:
            context['progress_percentage'] = 0

        return context

# プロジェクト作成ビュー（ログイン不要）
class ProjectCreateView(CreateView):
    model = Project
    fields = ['title', 'description']
    template_name = 'project_form.html'

    def get_initial(self):
        return {'description': 'プロジェクト憲章\n 社会的背景：\n ・\n\n 根本ニーズ：\n ・\n\n 我々はなぜここにいるのか：\n ・\n\n エレベーターピッチ：\n ・　　たい\n ・　　のための\n ・　　というプロダクトは\n ・　　\n ・これは　　を提供します\n ・　　とは違い\n ・　　する機能が備わっている\n\n'}

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.owner = self.request.user
        else:
            form.instance.owner = None
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project_detail', args=[self.object.id])

# カスタムログインビュー
class CustomLoginView(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        return reverse_lazy("project_list")

# プロジェクト参加ビュー（ログイン不要）
class ProjectJoinView(View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if request.user.is_authenticated:
            project.participants.add(request.user)
            if project.owner is None and project.participants.count() == 1:
                project.owner = request.user
                project.save()
        else:
            if project.owner is None:
                pass
        return redirect('project_detail', pk=pk)

# アカウントビュー（ログイン必要）
class AccountView(LoginRequiredMixin, TemplateView):
    template_name = 'account.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        participating_projects = user.participating_projects.all()

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

        total_completed_points = sum(data['completed_points'] for data in projects_data)

        context.update({
            'user': user,
            'projects_data': projects_data,
            'total_completed_points': total_completed_points
        })

        return context

# ゴール作成ビュー（ログイン必要）
class GoalCreateView(CreateView):
    model = Goal
    fields = ['text']
    template_name = 'goal_form.html'

    def dispatch(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=self.kwargs['pk'])
        has_owner = project.owner is not None

        if has_owner and not request.user.is_authenticated:
            return redirect('login')

        if has_owner and request.user not in project.participants.all():
            return HttpResponseForbidden()

        self.project = project
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.project = self.project
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('project_detail', args=[self.project.id])

# マイルストーン作成ビュー（ログイン必要）
class MilestoneCreateView(LoginRequiredMixin, CreateView):
    model = Milestone
    form_class = MilestoneForm
    template_name = 'roadmap_form.html'

    def form_valid(self, form):
        goal = None
        initial_point = Decimal(1)

        goal_id = self.kwargs.get('goal_id')
        if goal_id:
            goal = get_object_or_404(Goal, id=goal_id)
            form.instance.goal = goal
        else:
            parent_milestone_id = self.kwargs.get('parent_milestone_id')
            if parent_milestone_id:
                parent_milestone = get_object_or_404(Milestone, id=parent_milestone_id)
                form.instance.parent_milestone = parent_milestone
                form.instance.goal = parent_milestone.goal
                initial_point = parent_milestone.points
                goal = parent_milestone.goal

        response = super().form_valid(form)

        if goal:
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
@method_decorator(login_required, name='dispatch')
class StartMilestoneView(View):
    def post(self, request, pk):
        milestone = get_object_or_404(Milestone, pk=pk)
        milestone.assigned_to = request.user
        milestone.status = 'in_progress'
        milestone.save()
        return redirect('project_detail', pk=milestone.goal.project.id)

# マイルストーン完了ビュー（ログイン必要）
@method_decorator(login_required, name='dispatch')
class CompleteMilestoneView(View):
    def post(self, request, pk):
        milestone = get_object_or_404(Milestone, pk=pk)
        project = milestone.goal.project
        if request.user == project.owner:
            milestone.status = 'completed'
            milestone.save()
        return redirect('project_detail', pk=project.id)

# マイルストーン否認ビュー（ログイン必要）
@method_decorator(login_required, name='dispatch')
class DenyMilestoneView(View):
    def post(self, request, pk):
        milestone = get_object_or_404(Milestone, pk=pk)
        if milestone.assigned_to == request.user:
            milestone.status = 'not_started'
            milestone.save()
        return redirect('project_detail', pk=milestone.goal.project.id)

# プロジェクト参加者のビュー（ログイン不要）
def project_participants(request, pk):
    project = get_object_or_404(Project, id=pk)
    participants = project.participants.exclude(username__isnull=True).exclude(username='')

    participants_data = []
    for participant in participants:
        completed_milestones = Milestone.objects.filter(
            assigned_to=participant,
            status='completed',
            goal__project=project
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
    project = milestone.goal.project
    has_owner = project.owner is not None

    if has_owner and not request.user.is_authenticated:
        return redirect('login')

    if has_owner and request.user != project.owner:
        return HttpResponseForbidden()

    milestone.delete()
    return redirect('project_detail', pk=project.id)

# プロジェクト説明更新ビュー（ログイン必要）
@login_required
def project_description_form(request, pk):
    project = get_object_or_404(Project, pk=pk)
    initial_data = {
        'description': project.description
    }
    form = ProjectDescriptionForm(initial=initial_data)
    return render(request, 'project_description_form.html', {'form': form, 'project': project})

@login_required
def project_description_update(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.method == 'POST':
        form = ProjectDescriptionForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect(reverse('project_detail', kwargs={'pk': project.pk}))

    return project_description_form(request, pk)

# マイルストーンの順序更新ビュー
def update_milestone_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        project_id = data.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        has_owner = project.owner is not None

        if has_owner and not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'ログインが必要です。'}, status=403)

        if has_owner and request.user != project.owner:
            return JsonResponse({'status': 'error', 'message': '権限がありません。'}, status=403)

        milestones = data.get('milestones', [])
        for idx, milestone_data in enumerate(milestones):
            milestone = Milestone.objects.get(id=milestone_data['id'])
            milestone.order = idx
            milestone.parent_milestone = Milestone.objects.get(id=milestone_data['parent_id']) if milestone_data['parent_id'] else None
            milestone.save()
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': '無効なリクエストです。'}, status=400)

# GitHub URL追加ビュー
def add_github_url(request, pk):
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        form = GitHubURLForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_detail', pk=project.pk)
    else:
        form = GitHubURLForm(instance=project)
    return render(request, 'add_github_url_form.html', {'form': form, 'project': project})