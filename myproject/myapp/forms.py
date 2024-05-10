from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')  # 必要に応じて他のフィールドを追加

from django.forms import ModelForm
from .models import Project

class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'participants']  # 'owner' フィールドは通常、ビュー内で設定
        
from django import forms
from .models import Goal, Milestone

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['text']

from django import forms
from .models import Milestone

from django import forms
from .models import Milestone

class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['text']

    def __init__(self, *args, **kwargs):
        super(MilestoneForm, self).__init__(*args, **kwargs)
        if 'initial' in kwargs and 'parent_milestone' in kwargs['initial']:
            # URLからparent_milestoneが提供された場合、フォームから隠す
            self.fields['parent_milestone'].widget = forms.HiddenInput()

from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'メッセージを入力'}),
        }

from django.forms import ModelForm
from .models import Project

class ProjectDescriptionForm(ModelForm):
    class Meta:
        model = Project
        fields = ['description']
