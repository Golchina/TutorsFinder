from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.utils import timezone

from account.models import User, City
from .forms import AdForm, AdFilterForm
from .models import Ad, Subject
from account.services import get_current_age


def catalogue(request):
    """ View страницы с объявлениями. В GET параметрах может принимать данные для фильтрации и сортировки выдачи объявлений.
        После фильтрации и сортировки объявления передаются в пагинатор, количество объявлений на странице
        можно изменять с помощью переменной ads_per_page
    """
    ads = Ad.objects.all()
    cities = City.get_cities_list()
    subjects = Subject.get_subjects_list()

    # получаем параметры фильтрации из GET запроса
    creator_role = request.GET.get('creator_role')
    subject = request.GET.get('subject')
    city = request.GET.get('city')
    gender = request.GET.get('gender')
    sort_by = request.GET.get('sort_by')

    # фильтруем данные по заданным параметрам
    if creator_role:
        ads = ads.filter(creator_role=creator_role)
    if subject:
        ads = ads.filter(subject__name=subject)
    if city:
        ads = ads.filter(city__name=city)
    if gender:
        ads = ads.filter(creator__gender=gender)
    # сортируем данные по заданному параметру
    if sort_by:
        if sort_by == 'created_at_asc':
            ads = ads.order_by('created_at')
        if sort_by == 'price_desc':
            ads = ads.filter(price__isnull=False).order_by('-price')
        if sort_by == 'price_asc':
            ads = ads.filter(price__isnull=False).order_by('price')
        if sort_by == 'experience_asc':
            ads = ads.filter(experience__isnull=False).order_by('experience')
        if sort_by == 'experience_desc':
            ads = ads.filter(experience__isnull=False).order_by('-experience')
        if sort_by == 'age_desc':
            ads = ads.filter(creator__birthday__isnull=False).order_by('creator__birthday')
        if sort_by == 'age_asc':
            ads = ads.filter(creator__birthday__isnull=False).order_by('-creator__birthday')

    # отправляем данные в пагинатор
    ads_per_page = 3
    p = Paginator(ads, ads_per_page)
    page = request.GET.get('page')
    ads = p.get_page(page)

    # форма фильтрации
    form = AdFilterForm(request.GET)

    return render(request, 'catalogue/catalogue.html', {'ads': ads, 'form': form, 'cities': cities, 'subjects': subjects})


@login_required(login_url='login')
def delete_ad(request, ad_id):
    """ View для удаления объявлений. Проверяет, есть ли объявление с переданным ad_id и является ли отправитель
        запроса его создателем. Если требования соблюдены, удаляет объявление из базы данных и перенаправляет на профиль
        пользователя
    """
    ad = get_object_or_404(Ad, id=ad_id)

    if ad.creator != request.user:
        return HttpResponseForbidden()

    if request.method == "POST":
        ad.delete()
        return redirect(reverse('profile', kwargs={'user_id': request.user.id}))
    else:
        return render(request, "catalogue/delete_ad.html", {"ad": ad})


@login_required(login_url='login')
def create_ad(request):
    """ View для создания объявлений """
    cities = City.get_cities_list()
    subjects = Subject.get_subjects_list()
    if request.method == "POST":
        form = AdForm(request.POST)
        if form.is_valid():
            # добавляем автора объявления
            ad = form.save(commit=False)
            ad.creator = request.user
            ad.save()
            # добавляем предметы объявления
            for subject in form.cleaned_data['subject']:
                ad.subject.add(subject)
            return redirect(reverse('ad', kwargs={'ad_id': ad.id}))
    else:
        form = AdForm()
    return render(request, "catalogue/ad_form.html", {"form": form, "cities": cities, "subjects": subjects})


@login_required(login_url='login')
def edit_ad(request, ad_id):
    """ View для редактирования объявлений. Проверяет, есть ли объявление с переданным ad_id и является ли отправитель
        запроса его создателем. Если требования соблюдены, проверяет отправленную форму с новыми данными на правильность
        и сохраняет данные в бд
    """
    ad = get_object_or_404(Ad, id=ad_id)

    if ad.creator != request.user:
        return HttpResponseForbidden()

    cities = City.get_cities_list()
    subjects = Subject.get_subjects_list()

    if request.method == "POST":
        form = AdForm(request.POST, instance=ad)
        if form.is_valid():
            ad.save()
            # добавляем предметы объявления
            for subject in form.cleaned_data['subject']:
                ad.subject.add(subject)
            return redirect(reverse('ad', kwargs={'ad_id': ad.id}))
    else:
        form = AdForm(instance=ad, initial={'city': ad.city.name if ad.city else None, 'subject': ad.subject.name if ad.subject else None})
    return render(request, "catalogue/ad_form.html", {"form": form, "cities": cities, "subjects": subjects})


def ad(request, ad_id):
    """ View страницы объявления """
    ad = get_object_or_404(Ad, id=ad_id)
    ad_creator_age = get_current_age(ad.creator.birthday)
    return render(request, 'catalogue/ad.html', {'ad': ad, 'creator_age': ad_creator_age})


def index(request):
    return render(request, 'catalogue/index.html')


def about(request):
    return render(request, 'catalogue/about.html')


