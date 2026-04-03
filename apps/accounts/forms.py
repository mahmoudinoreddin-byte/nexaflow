from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import User


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'})
    )


class SetPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Create a strong password'}),
        validators=[validate_password],
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repeat your password'}),
    )

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get('password1'), cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'avatar', 'language']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'username'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
            'language': forms.Select(choices=[('en', 'English'), ('fr', 'Français'), ('es', 'Español')]),
        }
