from django import forms


class ConversationFilterForm(forms.Form):
    full_name = forms.CharField(required=False, label='Поиск', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Поиск по имени и фамилии'}))
