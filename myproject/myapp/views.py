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
from .utils import recalculate_milestone_points
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
# views.py

from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Sum
from django.http import HttpResponseForbidden
from .models import Project, Message, Goal, Milestone
from .forms import MessageForm

# views.py

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'project_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        user = self.request.user

        context['is_participant'] = user.is_authenticated and user in project.participants.all()
        context['is_owner'] = user.is_authenticated and project.owner == user
        context['project_owner'] = project.owner.username if project.owner else 'unknown'

        # マイルストーンのポイント再計算
        for goal in project.goals.all():
            recalculate_milestone_points(goal)

        # ゴールとマイルストーンの取得
        goals_with_milestones = []
        for goal in project.goals.all():
            milestones = goal.milestones.filter(parent_milestone__isnull=True).order_by('order')
            goals_with_milestones.append({'goal': goal, 'milestones': milestones})
        context['goals_with_milestones'] = goals_with_milestones

        # メッセージフォームとメッセージ一覧
        context['message_form'] = MessageForm()
        context['messages'] = project.messages.order_by('-created_at')

        # その他のコンテキストデータ
        total_completed_points = Milestone.objects.filter(
            goal__project=project,
            child_milestones__isnull=True,
            status='completed'
        ).aggregate(total_points=Sum('points'))['total_points'] or 0
        context['total_completed_points'] = total_completed_points
        
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        project = self.object
        user = request.user

        # メッセージフォームの処理
        message_form = MessageForm(request.POST)
        if message_form.is_valid():
            new_message = message_form.save(commit=False)
            new_message.project = project
            new_message.sender = user if user.is_authenticated else None
            new_message.save()
            return redirect('project_detail', pk=project.pk)
        else:
            # フォームが無効な場合、再度レンダリング
            context = self.get_context_data()
            context['message_form'] = message_form
            return self.render_to_response(context)

        return context

# プロジェクト作成ビュー（ログイン不要）
# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import generic, View
from django.views.generic.edit import CreateView
from django.contrib.auth import get_user_model
from .models import Project
from .forms import ProjectForm  # 必要に応じてフォームをインポート

User = get_user_model()

class ProjectCreateView(CreateView):
    model = Project
    fields = ['title', 'description']
    template_name = 'project_form.html'

    def get_initial(self):
        # 初期値を設定
        return {
            'description': (
                'プロジェクト憲章\n'
                '社会的背景：\n・\n\n'
                '根本ニーズ：\n・\n\n'
                '我々はなぜここにいるのか：\n・\n\n'
                'エレベーターピッチ：\n'
                '・　　たい\n'
                '・　　のための\n'
                '・　　というプロダクトは\n'
                '・　　\n'
                '・これは　　を提供します\n'
                '・　　とは違い\n'
                '・　　する機能が備わっている\n\n'
            )
        }

    def form_valid(self, form):
        if self.request.user.is_authenticated:
            form.instance.owner = self.request.user
        else:
            form.instance.owner = None  # オーナーがないプロジェクト
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
class AccountView(LoginRequiredMixin, View):
    template_name = 'account.html'

    def get(self, request, username=None):
        if username:
            # 他のユーザーのアカウントページ
            user = get_object_or_404(User, username=username)
            editable = False
        else:
            # 自分のアカウントページ
            user = request.user
            editable = True

        form = ProfileForm(instance=user) if editable else None

        participating_projects = user.participating_projects.all()
        total_completed_points = Milestone.objects.filter(
            assigned_to=user, status='completed'
        ).aggregate(total_points=Sum('points'))['total_points'] or 0

        context = {
            'user_profile': user,
            'form': form,
            'participating_projects': participating_projects,
            'total_completed_points': total_completed_points,
            'editable': editable,
        }
        return render(request, self.template_name, context)

    def post(self, request, username=None):
        if username and username != request.user.username:
            return HttpResponseForbidden()

        user = request.user
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('account')

        participating_projects = user.participating_projects.all()
        total_completed_points = Milestone.objects.filter(
            assigned_to=user, status='completed'
        ).aggregate(total_points=Sum('points'))['total_points'] or 0

        context = {
            'user_profile': user,
            'form': form,
            'participating_projects': participating_projects,
            'total_completed_points': total_completed_points,
            'editable': True,
        }
        return render(request, self.template_name, context)

# ゴール作成ビュー（ログイン必要）
# views.py

from django.views.generic.edit import CreateView
from django.http import HttpResponseForbidden
from .models import Goal

class GoalCreateView(View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        
        # オーナーがいる場合、ログインユーザーのみがゴールを設定可能
        if project.owner is not None:
            if not request.user.is_authenticated or request.user != project.owner:
                return HttpResponseForbidden("このプロジェクトにはゴールを設定できません。")
        
        form = GoalForm(request.POST)
        if form.is_valid():
            form.instance.project = project
            form.save()
            return redirect('project_detail', pk=pk)
        return render(request, 'goal_form.html', {'form': form, 'project': project})

# マイルストーン作成ビュー（ログイン必要）
# views.py

from django.views import View
from .forms import MilestoneForm

# views.py

from django.http import HttpResponseBadRequest

# views.py

class MilestoneCreateView(CreateView):
    model = Milestone
    form_class = MilestoneForm
    template_name = 'roadmap_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.goal = None
        self.parent_milestone = None

        goal_id = self.kwargs.get('goal_id')
        parent_milestone_id = self.kwargs.get('parent_milestone_id')

        if goal_id:
            self.goal = get_object_or_404(Goal, id=goal_id)
            self.project = self.goal.project
        elif parent_milestone_id:
            self.parent_milestone = get_object_or_404(Milestone, id=parent_milestone_id)
            self.goal = self.parent_milestone.goal
            self.project = self.goal.project
        else:
            return HttpResponseBadRequest("Parent not specified.")

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.project.owner is None:
            return super().get(request, *args, **kwargs)
        elif request.user.is_authenticated and request.user in self.project.participants.all():
            return super().get(request, *args, **kwargs)
        else:
            return redirect('project_detail', pk=self.project.pk)

    def post(self, request, *args, **kwargs):
        if self.project.owner is None:
            return super().post(request, *args, **kwargs)
        elif request.user.is_authenticated and request.user in self.project.participants.all():
            return super().post(request, *args, **kwargs)
        else:
            return redirect('project_detail', pk=self.project.pk)

    def form_valid(self, form):
        form.instance.goal = self.goal
        form.instance.parent_milestone = self.parent_milestone
        response = super().form_valid(form)
        recalculate_milestone_points(self.goal)
        return response

    def get_success_url(self):
        return reverse('project_detail', kwargs={'pk': self.project.pk})


# マイルストーン開始ビュー（ログイン必要）
class StartMilestoneView(View):
    def post(self, request, pk):
        milestone = get_object_or_404(Milestone, pk=pk)
        project = milestone.goal.project

        if project.owner is None:
            # オーナーがいないプロジェクトでは、匿名ユーザーも操作不可（着手はユーザーが必要）
            return redirect('project_detail', pk=project.pk)
        elif request.user.is_authenticated:
            milestone.assigned_to = request.user
            milestone.status = 'in_progress'
            milestone.save()
            return redirect('project_detail', pk=project.pk)
        else:
            return redirect('login')


# マイルストーン完了ビュー（ログイン必要）
class CompleteMilestoneView(View):
    def post(self, request, pk):
        milestone = get_object_or_404(Milestone, pk=pk)
        project = milestone.goal.project

        if project.owner is None:
            # オーナーがいないプロジェクトでは、完了操作はできない（オーナーがいないため）
            return redirect('project_detail', pk=project.pk)
        elif request.user.is_authenticated and request.user == project.owner:
            milestone.status = 'completed'
            milestone.save()
            return redirect('project_detail', pk=project.pk)
        else:
            return redirect('project_detail', pk=project.pk)

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
# views.py

def delete_milestone(request, pk):
    milestone = get_object_or_404(Milestone, pk=pk)
    project = milestone.goal.project

    if project.owner is None:
        # オーナーがいないプロジェクトでは、匿名ユーザーも削除を許可
        pass
    elif request.user.is_authenticated and request.user in project.participants.all():
        # プロジェクト参加者であれば削除を許可
        pass
    else:
        # それ以外のユーザーは削除を許可しない
        return redirect('project_detail', pk=project.pk)

    if request.method == 'POST':
        goal = milestone.goal  # 削除前にゴールを取得
        with transaction.atomic():
            milestone.delete()
            recalculate_milestone_points(goal)
        return redirect('project_detail', pk=project.pk)
    else:
        # 削除確認ページを表示する場合
        return render(request, 'milestone_confirm_delete.html', {'milestone': milestone})


# プロジェクト説明更新ビュー（ログイン必要）
@login_required
def project_description_form(request, pk):
    project = get_object_or_404(Project, pk=pk)
    initial_data = {
        'description': project.description
    }
    form = ProjectDescriptionForm(initial=initial_data)
    return render(request, 'project_description_form.html', {'form': form, 'project': project})

# views.py

def project_description_update(request, pk):
    project = get_object_or_404(Project, pk=pk)
    has_owner = project.owner is not None

    if has_owner and not request.user.is_authenticated:
        return redirect('login')

    if has_owner and request.user != project.owner:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = ProjectDescriptionForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect(reverse('project_detail', kwargs={'pk': project.pk}))
    else:
        initial_data = {'description': project.description}
        form = ProjectDescriptionForm(initial=initial_data)

    return render(request, 'project_description_form.html', {'form': form, 'project': project})
    

# マイルストーンの順序更新ビュー
import json
from django.http import JsonResponse
def update_milestone_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order = data.get('order', [])
        if not order:
            return JsonResponse({'status': 'error', 'message': 'No order data provided.'}, status=400)
        
        first_milestone = Milestone.objects.get(id=order[0]['id'])
        project = first_milestone.goal.project

        if project.owner is None:
            # オーナーがいないプロジェクトでは、匿名ユーザーも並び替えを許可
            pass
        elif request.user.is_authenticated and request.user in project.participants.all():
            # プロジェクト参加者であれば並び替えを許可
            pass
        else:
            return JsonResponse({'status': 'error', 'message': '無効なリクエストです。'}, status=400)

        with transaction.atomic():
            for item in order:
                milestone = Milestone.objects.get(id=item['id'])
                milestone.order = item['order']
                milestone.parent_milestone_id = item['parent_id'] if item['parent_id'] else None
                milestone.save()
            # ポイント再計算処理
            goal_ids = set()
            for item in order:
                milestone = Milestone.objects.get(id=item['id'])
                goal_ids.add(milestone.goal.id)

            for goal_id in goal_ids:
                goal = Goal.objects.get(id=goal_id)
                recalculate_milestone_points(goal)

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
    
    # views.py

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

class BecomeOwnerView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        
        if project.owner is not None:
            return HttpResponseForbidden("このプロジェクトには既にオーナーが存在します。")
        
        project.owner = request.user
        project.save()
        return redirect('project_detail', pk=pk)  


class MilestoneUpdateView(UpdateView):
    model = Milestone
    form_class = MilestoneForm
    template_name = 'milestone_form.html'

    def get_success_url(self):
        return reverse('project_detail', kwargs={'pk': self.object.goal.project.pk})

    def dispatch(self, request, *args, **kwargs):
        milestone = self.get_object()
        project = milestone.goal.project

        if project.owner is None or (request.user.is_authenticated and request.user in project.participants.all()):
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect('project_detail', pk=project.pk)

class ProjectDeleteRequestView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        if request.user in project.participants.all():
            ProjectDeleteRequest.objects.get_or_create(project=project, user=request.user)
            # 全員がリクエストしたかチェック
            total_participants = project.participants.count()
            total_requests = ProjectDeleteRequest.objects.filter(project=project).count()
            if total_participants == total_requests:
                project.delete()
                return redirect('project_list')
        return redirect('project_detail', pk=pk)