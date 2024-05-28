from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

@receiver(user_signed_up)
def populate_user_profile(request, user, sociallogin=None, **kwargs):
    if sociallogin:
        if sociallogin.account.provider == 'twitter':
            extra_data = sociallogin.account.extra_data
            user.email = extra_data.get('email', '')
            user.twitter_handle = extra_data.get('screen_name', '')
            if not user.has_usable_password():
                user.set_unusable_password()
            user.save()