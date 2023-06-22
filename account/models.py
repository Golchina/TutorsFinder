from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


GENDERS = [('', 'Не выбрано'), ("m", "Мужской"), ("f", "Женский")]


class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, surname, birthday, gender, password, **other_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, surname=surname, birthday=birthday,
                          gender=gender, **other_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, name, surname, birthday, gender, password, **other_fields):
        other_fields.setdefault('is_staff', True)
        return self.create_user(email, name, surname, birthday, gender, password, **other_fields)


class City(models.Model):

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    @staticmethod
    def get_cities_list():
        return list(City.objects.all().values_list('name', flat=True))


class User(AbstractBaseUser):
    email = models.EmailField('Почта', max_length=80, unique=True)
    name = models.CharField('Имя', max_length=50)
    surname = models.CharField('Фамилия', max_length=50)
    birthday = models.DateField('Дата рождения')
    gender = models.CharField('Пол', max_length=50, choices=GENDERS, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    profile_image = models.ImageField('Фото профиля', default="profile.png", null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    # Поле, по которому будет осуществляться вход
    USERNAME_FIELD = 'email'

    # Поля для создания админа
    REQUIRED_FIELDS = ['name', 'surname', 'birthday', 'gender']

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def __str__(self):
        return self.email

