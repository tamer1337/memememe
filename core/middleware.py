from django.shortcuts import redirect
from django.urls import reverse

class AuthRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Страницы, доступные без авторизации
        open_urls = [
            reverse('login'),  # Используйте именованные URL
            reverse('register'),
            '/admin/',  # Если нужно оставить доступ к админке
        ]
        
        # Проверяем, существует ли атрибут user
        if not hasattr(request, 'user'):
            return self.get_response(request)
            
        if not request.user.is_authenticated and request.path not in open_urls:
            return redirect(f'{reverse("login")}?next={request.path}')
        
        return self.get_response(request)