from django import forms
from django.core.exceptions import ValidationError
from django_select2.forms import Select2MultipleWidget

from account.models import City, GENDERS
from catalogue.models import Ad, Subject, AD_CREATOR_ROLE


class AdFilterForm(forms.Form):
    SORT_BY = [("", "Дате публикации (новые -> старые)"),
               ("created_at_asc", "Дате публикации (старые -> новые)"),
               ("price_asc", "Цене (дешевые -> дорогие)"),
               ("price_desc", "Цене (дорогие -> дешевые)"),
               ("experience_desc", "Опыту (больше -> меньше)"),
               ("experience_asc", "Опыту (меньше -> больше)"),
               ("age_desc", "Возрасту (старше -> младше)"),
               ("age_asc", "Возрасту (младше -> старше)")]

    gender = forms.ChoiceField(choices=GENDERS, required=False, label='Пол', widget=forms.Select(attrs={'class': 'form-control'}))
    creator_role = forms.ChoiceField(choices=AD_CREATOR_ROLE, required=False, label='Кого ищете', widget=forms.Select(attrs={'class': 'form-control'}))
    subject = forms.CharField(required=False, max_length=100, label='Предмет', widget=forms.TextInput(attrs={'name': "subject", 'type': "text", 'list': "subjectlist", 'placeholder': "Введите предмет", 'class': "form-control"}))
    city = forms.CharField(required=False, max_length=100, label='Город', widget=forms.TextInput(attrs={'name': "city", 'type': "text", 'list': "citylist", 'placeholder': "Введите город", 'class': "form-control"}))
    sort_by = forms.ChoiceField(choices=SORT_BY, required=False, label='Сортировать по', widget=forms.Select(attrs={'class': 'form-control'}))


class AdForm(forms.ModelForm):
    city = forms.CharField(required=False, max_length=100, label='Город', widget=forms.TextInput(attrs={'name': "city", 'type': "text", 'list': "citylist", 'placeholder': "Введите город", 'class': "form-control"}))
    subject = forms.ModelMultipleChoiceField(queryset=Subject.objects.all(), label="Предмет(ы)", widget=Select2MultipleWidget(attrs={'name': "subject", 'type': "text", 'list': "subjectlist", 'placeholder': "Введите предмет", 'class': "form-control"}))
    class Meta:
        model = Ad
        fields = ["title", "description", "price", "subject", "experience", "city", "creator_role"]
        widgets = {
            "title": forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Заголовок'}),
            "description": forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Описание'}),
            "price": forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Цена (рублей в час)'}),
            "experience": forms.Select(attrs={'class': 'form-control', 'placeholder': 'Опыт'}),
            "creator_role": forms.Select(attrs={'class': 'form-control', 'placeholder': 'Вы Репетитор или Ученик?'}),
        }

    def clean_city(self):
        city = self.cleaned_data['city']
        if city:
            all_cities = City.get_cities_list()
            for db_city in all_cities:
                if db_city.lower() == city.lower():
                    return City.objects.get(name=db_city)
            raise ValidationError('Укажите город из списка или оставьте поле пустым')
        else:
            return None
