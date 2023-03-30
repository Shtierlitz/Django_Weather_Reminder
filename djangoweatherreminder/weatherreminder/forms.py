from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from weatherreminder.models import User


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label='User Name', widget=forms.TextInput(
        attrs={'type': "text", 'id': "form3Example1cg", 'class': "form-control form-control-lg"}))
    password1 = forms.CharField(label='Password',
                                widget=forms.PasswordInput(attrs={'type': "password", 'id': "form3Example4cg",
                                                                  'class': "form-control form-control-lg"}))
    password2 = forms.CharField(label='Repeat password',
                                widget=forms.PasswordInput(attrs={'type': "password", 'id': "form3Example4cg",
                                                                  'class': "form-control form-control-lg"}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(
        attrs={'type': "email", 'id': "form3Example3cg", 'class': "form-control form-control-lg"}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='User name', widget=forms.TextInput(
        attrs={'type': "text", 'id': "form3Example1cg", 'class': "form-control form-control-lg"}))
    password = forms.CharField(label='Password',
                               widget=forms.PasswordInput(attrs={'type': "password", 'id': "form3Example4cg",
                                                                 'class': "form-control form-control-lg"}))


class ChangeProfileForm(forms.ModelForm):
    username = forms.CharField(label='User name', widget=forms.TextInput(
        attrs={'type': "text", 'id': "form3Example1cg", 'class': "form-control form-control-lg"}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(
        attrs={'type': "email", 'id': "form3Example3cg", 'class': "form-control form-control-lg"}))

    class Meta:
        model = User
        fields = ['username', 'email']
