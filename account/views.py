from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse

from catalogue.models import Ad, User
from .forms import RegistrationForm, LogInForm, EditUserForm, CustomPasswordChangeForm
from .models import City

from .services import get_user_data


@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменён')
            return redirect('change_password')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'account/change_password.html', {'form': form})


@login_required(login_url='login')
def edit_profile(request):
    """ View для редактирования данных профиля пользователя """
    cities = City.get_cities_list()
    if request.method == "POST":
        form = EditUserForm(request.POST, request.FILES,  instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(reverse('profile', kwargs={'user_id': request.user.id}))
    else:
        if request.user.city:
            initial = {'city': request.user.city.name}
        else:
            initial = None
        form = EditUserForm(instance=request.user, initial=initial)
    return render(request, "account/edit_profile.html", {"form": form, "cities": cities})


@login_required(login_url='login')
def profile(request, user_id):
    """ View страницы профиля. В context передает данные пользователя и объявления, которые он выкладывал.
        Объявления передаются с использованием пагинации, количество объявлений на одной странице можно настроить
        через переменную ads_per_page.
    """
    try:
        user = User.objects.get(id=user_id)
    except ObjectDoesNotExist:
        return render(request, 'account/404.html')

    user_data = get_user_data(user)
    user_ads = Ad.objects.all().filter(creator=user)
    ads_per_page = 3
    p = Paginator(user_ads, ads_per_page)
    page = request.GET.get('page')
    ads = p.get_page(page)
    return render(request, 'account/profile.html', context={'user_data': user_data, 'ads': ads})


@login_required(login_url='login')
def log_out(request):
    logout(request)
    return redirect('login')


def register(request):
    cities = City.get_cities_list()
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Аккаунт успешно создан')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, "account/sign_up.html", {"form": form, "cities": cities})


def log_in(request):
    if request.method == "POST":
        form = LogInForm()
        email = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect(reverse('profile', kwargs={'user_id': request.user.id}))
        else:
            messages.warning(request, 'Почта или пароль введены неверно')
    else:
        form = LogInForm()
    return render(request, "account/login.html", {"form": form})