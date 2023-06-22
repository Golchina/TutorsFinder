import os
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from account.models import User
from tutorsfinder.settings import MEDIA_ROOT
from .fields import EncryptedMessageField


class Blacklist(models.Model):
    """ Таблица, которая отражает блокировку пользователя от отправления сообщений другому пользователю """
    blocker = models.ForeignKey(User, related_name='blocker', on_delete=models.CASCADE)
    blocked_user = models.ForeignKey(User, related_name='blocked_user', on_delete=models.CASCADE)

    class Meta:
        unique_together = ['blocker', 'blocked_user']


class Conversation(models.Model):
    """ Таблица диалога """
    created_at = models.DateTimeField(auto_now_add=True)
    participants = models.ManyToManyField(User, related_name='conversations')


class Message(models.Model):
    """ Таблица сообщения. Сообщение может содержать текст (content), одно или несколько изображений (fk message в MessageMedia),
        либо и то, и другое"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = EncryptedMessageField()
    seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.author.email} - {self.content}'


class MessageMedia(models.Model):
    """ Таблица со ссылками на отправленные в чат изображения """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, related_name='media')
    image = models.ImageField()


@receiver(post_delete, sender=MessageMedia)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """ Удаляем файлы фото при удалении MessageMedia """
    if instance.image:
        if os.path.isfile(MEDIA_ROOT + instance.image.url):
            os.remove(MEDIA_ROOT + instance.image.url)
