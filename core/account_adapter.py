from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import PermissionDenied


class NoNewUsersAccountAdapter(DefaultAccountAdapter):

    # def authenticate(self, request, **kwargs):
    #     username = kwargs.get('username')
    #     password = kwargs.get('password')
    #     user = super().authenticate(request, username=username, password=password)
    #     if user and not user.is_staff:
    #         raise PermissionDenied("You are not allowed to login.")
    #
    #     return user

    def is_open_for_signup(self, request):
        """
        Checks whether or not the site is open for signups.

        Next to simply returning True/False you can also intervene the
        regular flow by raising an ImmediateHttpResponse

        (Comment reproduced from the overridden method.)
        """
        return False