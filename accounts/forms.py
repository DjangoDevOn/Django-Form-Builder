from django.contrib.auth.forms import UserChangeForm
from django import forms
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.forms import UserCreationForm

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254)

    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2',
            'manager_id',
            ]
 