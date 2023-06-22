import base64
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models
from django.apps import apps


class EncryptedMessageField(models.BinaryField):
    """ Кастомное поле с шифрованием и дешифрованием сообщения """
    description = "Зашифрованное сообщение"

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 500
        kwargs['blank'] = True
        kwargs['null'] = True
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs["max_length"]
        del kwargs["blank"]
        del kwargs["null"]
        return name, path, args, kwargs

    def get_prep_value(self, value):
        return self.encrypt_data(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return self.decrypt_data(value)

    def to_python(self, value):
        if isinstance(value, apps.get_model('chat.Message')):
            return value
        if value is None:
            return value
        return self.decrypt_data(value)

    @staticmethod
    def encrypt_data(value):
        if not value:
            return None
        key = base64.urlsafe_b64encode(bytes(settings.SECRET_KEY[:32], 'utf-8'))
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(base64.urlsafe_b64encode(bytes(value, 'utf-8')))
        return encrypted_data

    @staticmethod
    def decrypt_data(value):
        if not value:
            return None
        key = base64.urlsafe_b64encode(bytes(settings.SECRET_KEY[:32], 'utf-8'))
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(value)
        return base64.urlsafe_b64decode(decrypted_data).decode('utf-8')
