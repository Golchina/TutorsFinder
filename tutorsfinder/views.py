from django.shortcuts import render


def notfound(request, exception):
    """ Кастомная страница ошибки 404. Работает только при DEBUG = False и настроенном ALLOWED_HOSTS """
    return render(request, 'account/404.html', status=404)