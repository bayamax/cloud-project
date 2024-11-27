from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Project, Goal, Milestone, Message, Thread, ThreadMessage

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')  # 必要に応じて他のフィールドを追加

class PayPayIDForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['paypay_id']
        widgets = {
            'paypay_id': forms.TextInput(attrs={'placeholder': 'PayPay IDを入力してください'})
        }

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'total_investment']  # `total_investment` を追加
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'total_investment': forms.NumberInput(attrs={'step': '1000'}),
        }

class ProjectDescriptionForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['description']

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['text']

class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['text']

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'メッセージを入力'}),
        }

class GitHubURLForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['github_url']
        widgets = {
            'github_url': forms.URLInput(attrs={'placeholder': 'https://github.com/owner/repo'})
        }

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['title']

class ThreadMessageForm(forms.ModelForm):
    class Meta:
        model = ThreadMessage
        fields = ['text']

class SetRewardForm(forms.Form):
    reward_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label='報酬額（参考値）',
        widget=forms.NumberInput(attrs={'step': '100'})
    )