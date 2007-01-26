from django import newforms as forms
from django.newforms import widgets, ValidationError

from django.contrib.auth import authenticate
from django.contrib.auth.models import User


class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=30)
    email = forms.EmailField()
    password1 = forms.CharField(label="Password", widget=widgets.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=widgets.PasswordInput)

    def clean_password1(self):
        # TODO: make sure passwords are strong
        return self.clean_data['password1']

    def clean_password2(self):
        scd = self.clean_data
        if scd.get('password1') and scd.get('password2') and scd['password1'] != scd['password2']:
            raise ValidationError('Passwords must match.')
        return self.clean_data['password2']

    def clean_username(self):
        given_username = self.clean_data['username']
        try:
            User.objects.get(username=given_username)
        except User.DoesNotExist:
            return self.clean_data['username']
        raise ValidationError('The username "%s" is already taken.' % given_username)

    def create_user(self, new_data):
        u = User.objects.create_user(
            new_data['username'],
            new_data['email'],
            new_data['password1'])
        u.is_active = False
        u.save()
        return u


class LoginForm(forms.Form):
    username = forms.CharField(max_length=30)
    password = forms.CharField(widget=widgets.PasswordInput)

    def clean_password(self):
        scd = self.clean_data
        self.user = authenticate(username=scd['username'], password=scd['password'])

        if self.user is not None:
            if self.user.is_active:
                return self.clean_data['password']
            else:
                raise ValidationError('Your account has been disabled.')
        else:
            raise ValidationError('Your username or password were incorrect.')
