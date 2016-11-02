from django.core.exceptions import PermissionDenied


def superuser_required(func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return func(request, *args, **kwargs)
    return wrapper


def domain_celery_task(func):
    def wrap(*args, **kwargs):
        from accounts.models import User
        from crum import set_current_user

        task = args[0]
        args = args[1:]

        if task.request.headers and task.request.headers.get('current_user_id'):

            set_current_user(None) # Clear on celery
            try:
                current_user = User.objects.get(id=task.request.headers['current_user_id'])
                set_current_user(current_user)
            except User.DoesNotExist:
                pass

        return func(*args, **kwargs)

    wrap.__doc__ = func.__doc__
    wrap.__name__ = func.__name__
    return wrap