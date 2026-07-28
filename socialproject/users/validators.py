import re
from django.core.exceptions import ValidationError


class AlphanumericPasswordValidator:
    """
    Requires the password to contain at least one letter and one digit.
    This is the only content rule on top of minimum length - intentionally
    not checking against common passwords or user attributes, since the
    spec here is "must be 8 characters, must combine numbers and letters",
    nothing stricter.
    """

    def validate(self, password, user=None):
        if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            raise ValidationError(
                'Password must contain both letters and numbers.',
                code='password_no_letters_or_numbers',
            )

    def get_help_text(self):
        return 'Your password must contain both letters and numbers.'
