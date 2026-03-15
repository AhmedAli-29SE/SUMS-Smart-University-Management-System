from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class EmailBackend(ModelBackend):
    """Authenticate using email address instead of username."""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Support both 'username' and 'email' keyword args
        email = username or kwargs.get('email')
        if not email or not password:
            return None
        try:
            user = UserModel.objects.get(email__iexact=email.strip())
        except UserModel.DoesNotExist:
            # Run the default password hasher to prevent timing attacks
            UserModel().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
