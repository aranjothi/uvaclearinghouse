from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages


class NoAutoSignupSocialAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if not sociallogin.is_existing:
            messages.error(
                request,
                "You do not have an account yet. Sign up below to start exploring!"
            )
            raise ImmediateHttpResponse(redirect('signup'))
