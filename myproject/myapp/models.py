from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    bio = models.TextField(max_length=500, blank=True)
    github_username = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if not self.password:
            self.set_unusable_password()
        super().save(*args, **kwargs)

class Project(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='participating_projects')
    github_url = models.CharField(max_length=200, blank=True, null=True)

from django.db import models

class Goal(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='goals')
    text = models.TextField()
    # 他のフィールド...


from django.db import models
from django.conf import settings

class Milestone(models.Model):
    goal = models.ForeignKey('Goal', related_name='milestones', on_delete=models.CASCADE)
    parent_milestone = models.ForeignKey('self', related_name='child_milestones', on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='assigned_milestones',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('not_started', 'Not Started'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed')
        ],
        default='not_started'
    )
    points = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    num_children = models.IntegerField(default=0)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.text

class Message(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message from {self.sender.username} on {self.project.title}: {self.text[:50]}'