def save_github_username(strategy, details, user=None, *args, **kwargs):
    if user:
        user.github_username = details.get('username')
        user.save()