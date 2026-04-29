from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


class StrongPasswordValidator:
    """
    Custom password validator to ensure strong passwords with:
    - Minimum length of 6 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    
    def validate(self, password, user=None):
        if len(password) < 6:
            raise ValidationError(
                _("Password must be at least 6 characters long."),
                code='password_too_short',
            )
        
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Password must contain at least one uppercase letter."),
                code='password_no_upper',
            )
        
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter."),
                code='password_no_lower',
            )
        
        if not re.search(r'\d', password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code='password_no_digit',
            )
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                _("Password must contain at least one special character."),
                code='password_no_special',
            )
    
    def get_help_text(self):
        return _(
            "Your password must be at least 6 characters long, "
            "contain at least one uppercase letter, one lowercase letter, "
            "one digit, and one special character."
        )
