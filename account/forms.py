import django.contrib.auth.forms
from django.core.exceptions import ValidationError
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, City


class CustomPasswordChangeForm(django.contrib.auth.forms.PasswordChangeForm):
    old_password = forms.CharField(max_length=16, label='Старый пароль', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите свой старый пароль'}))
    new_password1 = forms.CharField(max_length=16, label='Новый пароль', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль минимум из 8 символов'}))
    new_password2 = forms.CharField(max_length=16, label='Повтор нового пароля', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'}))

    class Meta:
        model = User
        field = ['password']


class DateInput(forms.DateInput):
    input_type = 'date'


class EditUserForm(forms.ModelForm):
    city = forms.CharField(max_length=100, label='Город', widget=forms.TextInput(attrs={'name': "city", 'type': "text", 'list': "citylist", 'placeholder': "Введите город", 'class': "form-control"}))

    class Meta:
        model = User
        fields = ["profile_image", "name", "surname", "birthday", "city"]
        widgets = {
            "name": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            "surname": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            "birthday": DateInput(format='%Y-%m-%d', attrs={'class': 'form-control'}),
            "profile_image": forms.FileInput(),
        }

    def clean_city(self):
        city = self.cleaned_data['city']
        all_cities = City.get_cities_list()
        for db_city in all_cities:
            if db_city.lower() == city.lower():
                return City.objects.get(name=db_city)
        raise ValidationError("Выберите город из списка")


class RegistrationForm(UserCreationForm):
    password1 = forms.CharField(max_length=16, label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль минимум из 8 символов'}))
    password2 = forms.CharField(max_length=16, label='Повтор пароля', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите пароль'}))
    city = forms.CharField(max_length=100, label='Город', widget=forms.TextInput(attrs={'name': "city", 'type': "text", 'list': "citylist", 'placeholder': "Введите город", 'class': "form-control"}), required=False)

    class Meta:
        model = User
        fields = ["name", "surname", "birthday", "gender", "city", "email", "password1", "password2"]
        widgets = {
            "name": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            "surname": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            "birthday": DateInput(attrs={'class': 'form-control', 'placeholder': 'Дата рождения'}),
            "gender": forms.Select(attrs={'class': 'form-control', 'placeholder': 'Пол'}),
            "email": forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Почта'}),
        }

    def clean_city(self):
        city = self.cleaned_data['city']
        if city:
            all_cities = City.get_cities_list()
            for db_city in all_cities:
                if db_city.lower() == city.lower():
                    return City.objects.get(name=db_city)
            raise ValidationError("Выберите город из списка")
        else:
            return None


class LogInForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "password"]
        labels = {"password": "Пароль"}
        widgets = {
            "email": forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Почта'}),
            "password": forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'})
        }