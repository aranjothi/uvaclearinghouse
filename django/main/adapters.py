from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


class NoAutoSignupSocialAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if not sociallogin.is_existing:
            if not request.session.get('pending_exec_codes'):
                messages.error(
                    request,
                    "You do not have an account yet. Sign up below to start exploring!"
                )
                raise ImmediateHttpResponse(redirect('signup'))

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        was_signing_up = bool(request.session.get('pending_exec_codes'))
        if was_signing_up:
            messages.error(request, 'Sign up with Google failed. Please try again.')
            raise ImmediateHttpResponse(redirect('signup'))
        messages.error(request, 'Login with Google failed. Please try again.')
        raise ImmediateHttpResponse(redirect('login'))

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        exec_codes = request.session.pop('pending_exec_codes', [])
        if exec_codes:
            from .models import Club, Membership
            for code in exec_codes:
                club = Club.objects.filter(executive_code=code).first()
                if club:
                    Membership.objects.get_or_create(
                        user=user, club=club,
                        defaults={'role': Membership.EXECUTIVE}
                    )
        return user
