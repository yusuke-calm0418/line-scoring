from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import UserRegistrationForm, LoginForm
from django.contrib.auth.views import LoginView
from django.views import View
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .models import CustomUser
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse

class CustomLoginView(LoginView):
    template_name = 'scoring/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse('dashboard')

class CustomRegisterView(View):
    def get(self, request):
        form = UserRegistrationForm()
        return render(request, 'scoring/register.html', {'form': form})

    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'アカウントを有効にしてください。'
            message = render_to_string('scoring/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'protocol': 'http',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            return redirect('email_verification_sent')
        return render(request, 'scoring/register.html', {'form': form})

User = get_user_model()

def activate(request, uidb64, token):
    print('Activation function called')  # デバッグメッセージ
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        print(f'User found: {user.email}')  # デバッグメッセージ
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
        print(f'Error: {e}')  # デバッグメッセージ
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'アカウントが有効化されました。')
        print('Account activated')  # デバッグメッセージ
        return redirect('activation_complete')
    else:
        messages.error(request, 'アクティベーションリンクが無効です。')
        print('Invalid activation link')  # デバッグメッセージ
        return redirect('login')
