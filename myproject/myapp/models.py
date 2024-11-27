from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from decimal import Decimal

class CustomUser(AbstractUser):
    bio = models.TextField(max_length=500, blank=True)
    github_username = models.CharField(max_length=255, blank=True, null=True)
    paypay_id = models.CharField(max_length=255, blank=True, null=True)

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
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,  # オーナーが削除された場合はNULLに設定
        null=True,
        blank=True,
        related_name='owned_projects'  # リバース関係を明確にする
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='participating_projects'
    )
    github_url = models.CharField(max_length=200, blank=True, null=True)
    total_investment = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return self.title

class Goal(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='goals')
    text = models.TextField()

    def __str__(self):
        return self.text

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
    points = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    manual_points = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    auto_points = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    order = models.IntegerField(default=0)

    def is_leaf(self):
        return not self.child_milestones.exists()

    def __str__(self):
        return self.text

class Message(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        null=True,
        blank=True
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sender_username = self.sender.username if self.sender else "Anonymous"
        return f'Message from {sender_username} on {self.project.title}: {self.text[:50]}'

class Thread(models.Model):
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ThreadMessage(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sender_name = self.sender.username if self.sender else "Anonymous"
        return f'Message in {self.thread.title} from {sender_name}: {self.text[:50]}'

class PaymentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', '手続き中'),
        ('completed', '手続き完了'),
        ('failed', '手続き失敗'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_requests_sent')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'PaymentRequest from {self.participant.username} to {self.owner.username}'