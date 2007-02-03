from django import newforms as forms
from django.newforms import widgets, ValidationError
from django.newforms.forms import SortedDictFromList

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from models import Category


class PostForm(forms.Form):
    post = forms.CharField(
            label = '',
            widget=forms.Textarea(attrs={
                'rows':'5',
            }),
        )
    private = forms.CharField(
            label="Recipients",
            max_length=150,
            widget=forms.TextInput(),
            required=False,
            )

    def clean_private(self):
        recipients = self.clean_data['private']
        if len(recipients.strip()) < 1:
            return ''
        recipients = recipients.split(',')
        recipients = [x.strip() for x in recipients]
        cleandata = []
        for r in recipients:
            # make sure recipients exist
            try:
                if len(r) > 0:
                    cleandata.append(str(User.objects.get(username=r).id))
            except User.DoesNotExist:
                raise ValidationError(r + " is not a valid user.")

        return ','.join(cleandata)


class ThreadForm(forms.Form):
    category = forms.CharField(widget=forms.Select(
        choices = [(str(x.id), x.label) for x in Category.objects.all()]
        ))
    subject = forms.CharField(max_length=80,
            widget=forms.TextInput(
                attrs={
                    'size': '80',
                })
            )
    post = forms.CharField(widget=forms.Textarea(
            attrs={
                'rows':'5',
                'cols': '80',
            })
        )

    def clean_category(self):
        id = int(self.clean_data['category'])
        return id


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
# vim: ai ts=4 sts=4 et sw=4
