import datetime, random, sha

from django import forms
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.simple import redirect_to

from django.contrib.auth import login, logout

from models import UserProfile
from forms import RegistrationForm, LoginForm

CONFIRM_REDIRECT = 'http://' + Site.objects.get(pk=settings.SITE_ID).domain

def register(request):
    if request.user.is_authenticated():
        # They already have an account; don't let them register again
        return render_to_response('sbreg/register.html', {'has_account': True})
    elif request.POST:
        # we got a registration request
        new_data = request.POST.copy()
        form = RegistrationForm(new_data)
        if form.is_valid():
            # Save the user
            new_user = form.create_user(new_data)

            # Build the activation key for their account
            salt = sha.new(str(random.random())).hexdigest()[:5]
            activation_key = sha.new(salt+new_user.username).hexdigest()
            key_expires = datetime.datetime.today() + datetime.timedelta(2)

            # Create and save their profile
            new_profile = UserProfile(user=new_user,
                activation_key=activation_key,
                key_expires=key_expires)
            new_profile.save()

            site_name = Site.objects.get(pk=settings.SITE_ID).domain
            confirm_url = 'http://' + site_name + '/accounts/confirm/' + activation_key
            reply_address = '<nobody@' + site_name.split(':')[0] + '>'

            email_body = ''.join(
                    (
                        'Hi!\n\n    Thanks for signing up with ',
                        site_name,
                        '!\n\nTo activate your account, click the following link within 48 hours:\n\n',
                        confirm_url,
                        '\n\n\nRegards,\nThe ',
                        site_name,
                        ' team.\n'
                    ))
            print email_body

            # Send an email with the confirmation link
            email_subject = 'Your new %s account information' % site_name
            send_mail(email_subject, email_body, reply_address, [new_user.email])

            return render_to_response('sbreg/register.html', {'created': True})
    else:
        # vanilla visit; start the registration process
        form = RegistrationForm()

    return render_to_response('sbreg/register.html', {'form': form})


def confirm(request, activation_key): 
    if request.user.is_authenticated(): 
        return render_to_response('confirm.html', {'has_account': True}) 
    user_profile = get_object_or_404(UserProfile, activation_key=activation_key) 
    if user_profile.key_expires < datetime.datetime.today(): 
        return render_to_response('confirm.html', {'expired': True}) 
    user_account = user_profile.user 
    user_account.is_active = True 
    user_account.save() 
    return render_to_response('sbreg/confirm.html', {'success': True, 'next': CONFIRM_REDIRECT})
