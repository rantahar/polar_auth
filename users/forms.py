from django import forms
from django.contrib.auth.forms import UserCreationForm

from users.models import User


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['email']


class ConsentForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['consent']
