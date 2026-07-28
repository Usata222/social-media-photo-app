from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Profile


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('photo', 'bio', 'location', 'website')


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegistartionForm(forms.ModelForm):

    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(
        label='Confirm password', widget=forms.PasswordInput)
    agree_to_terms = forms.BooleanField(
        label='I agree to the Terms of Use and Privacy Policy',
        required=True,
        error_messages={'required': 'You must agree to the Terms of Use and Privacy Policy to register.'},
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name')

    def clean_password(self):
        password = self.cleaned_data.get('password')
        # Runs AUTH_PASSWORD_VALIDATORS (min length 8 + letters-and-numbers rule)
        validate_password(password)
        return password

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError('Passwords do not match')
        return password2
