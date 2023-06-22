from django.db import models

from account.models import User, City


AD_CREATOR_ROLE = [("", "Не выбрано"), ("t", "Репетитор"), ("s", "Ученик")]


class Experience(models.Model):
    years = models.CharField(max_length=10)

    def __str__(self):
        return self.years


class Subject(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    @staticmethod
    def get_subjects_list():
        return list(Subject.objects.all().values_list('name', flat=True))


class Ad(models.Model):
    creator = models.ForeignKey(User, verbose_name='Автор', on_delete=models.CASCADE)
    creator_role = models.CharField('Кто вы?', max_length=50, choices=AD_CREATOR_ROLE, default="t")
    created_at = models.DateTimeField('Дата публикации', auto_now_add=True)
    title = models.CharField('Заголовок', max_length=100)
    description = models.CharField('Описание', max_length=500)
    price = models.IntegerField('Цена', null=True, blank=True)
    subject = models.ManyToManyField(Subject, verbose_name='Предмет')
    experience = models.ForeignKey(Experience, verbose_name='Опыт', on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, verbose_name='Город', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title