from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class UserApprovalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.userprofile.is_approved:
            if not request.path.startswith('/users/'):
                messages.warning(request, "Your account is not approved yet.")
                return redirect('users:profile')
        
        response = self.get_response(request)
        return response