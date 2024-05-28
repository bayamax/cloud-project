from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(required=False, widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(required=False, widget=forms.PasswordInput, label="Password confirmation")

    class Meta:
        model = CustomUser
        fields = ('username', 'email')

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

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

from django import forms
from .models import Project

class ProjectDescriptionForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['description']
 