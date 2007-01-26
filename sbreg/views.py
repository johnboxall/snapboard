import datetime, random, sha

from django import forms
from django.core.mail import send_mail
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.simple import redirect_to

from django.contrib.auth import login, logout

from models import UserProfile
from forms import RegistrationForm, LoginForm

# refactor 'has_account' to 'authenticated'


SITE_NAME = "example.com"
CONFIRM_URL_BASE = "http://example.com/accounts/confirm/"
REPLY_ADDRESS = "nobody@example.com"

CONFIRM_EMAIL_BODY = ''.join(
        (
            'Hello, %s, and thanks for signing up for an ',
            SITE_NAME,
            ' account!\n\nTo activate your account, click this link within 48 hours:\n\n',
            CONFIRM_URL_BASE,
            '%s', # hash
        ))


def register(request):
    if request.user.is_authenticated():
        # They already have an account; don't let them register again
        return render_to_response('register.html', {'has_account': True})
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

            # Send an email with the confirmation link
            email_subject = 'Your new %s account confirmation' % SITE_NAME
            email_body = CONFIRM_EMAIL_BODY % (new_user.username, new_profile.activation_key)
            send_mail(email_subject,
                email_body, REPLY_ADDRESS, [new_user.email])

            return render_to_response('register.html', {'created': True})
    else:
        # vanilla visit; start the registration process
        form = RegistrationForm()

    return render_to_response('register.html', {'form': form})


def signin(request):
    SESS_REF_KEY = 'profiles_signin_referrer'

    if request.user.is_authenticated(): 
        form = None
    elif request.POST:
        form_data = request.POST.copy()
        form = LoginForm(form_data)

        if form.is_valid():
            user = form.user
            login(request, user)
            form = None
            # redirect to referrer of login
            redirect_url = request.session.get(SESS_REF_KEY, '/')
            del request.session[SESS_REF_KEY]
            return redirect_to(request, redirect_url)
    else:
        # clean login request, save the referring page in the session vars
        form = LoginForm()
        referrer = request.META.get('HTTP_REFERER', '/')
        if SESS_REF_KEY not in request.session:
            request.session[SESS_REF_KEY] = referrer

    return render_to_response('login.html',
            {
            'form': form,
            'user': request.user,
            })


def signout(request):
    logout(request)
    referrer = request.META.get('HTTP_REFERER', '/')
    #print request.META
    # Redirect to a success page.
    return redirect_to(request, referrer)


def confirm(request, activation_key): 
    if request.user.is_authenticated(): 
        return render_to_response('confirm.html', {'has_account': True}) 
    user_profile = get_object_or_404(UserProfile, activation_key=activation_key) 
    if user_profile.key_expires < datetime.datetime.today(): 
        return render_to_response('confirm.html', {'expired': True}) 
    user_account = user_profile.user 
    user_account.is_active = True 
    user_account.save() 
    return render_to_response('confirm.html', {'success': True})
