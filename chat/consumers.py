import json

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.db.models import Q
from django.shortcuts import get_object_or_404

from account.models import User
from chat.models import Message, MessageMedia, Conversation, Blacklist


class ChatConsumer(WebsocketConsumer):
    """ Consumer для страницы чата. Обрабатывает подключение, отключение, новые сообщения, удаление сообщений,
        загрузку более старых сообщений при скролле чата вверх, прочитано/не прочитано ли сообщение
        При подключении создаются названия 3 групп: группа данного чата, группа списка сообщений данного пользователя и
        группа списка сообщений собеседника данного чата.
    """
    def connect(self):
        """ При подключении к вебсокету получаем нужные в дальнейшем объекты и названия групп.
            Добавляем пользователя в группу чата
        """
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.user = self.scope['user']
        self.conversation = Conversation.objects.get(id=self.conversation_id)
        participants = self.conversation.participants.all()
        self.recipient = participants.exclude(id=self.user.id).first()

        self.conversation_group_name = 'chat_' + self.conversation_id
        self.our_chats_list_group_name = 'chats_list_' + str(self.user.id)
        self.recipient_chats_list_group_name = 'chats_list_' + str(self.recipient.id)
        # Присоединяемся к группе
        async_to_sync(self.channel_layer.group_add)(
            self.conversation_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Выходим из группы
        async_to_sync(self.channel_layer.group_discard)(
            self.conversation_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        """ Метод, в который приходят сообщения от вебсокета """
        text_data_json = json.loads(text_data)
        command = text_data_json.get('command')
        # Определяем, какая команда пришла в сообщении
        if command == 'send_message':
            # Проверяем, находится ли пользователь в черном списке
            if Blacklist.objects.filter(Q(blocker=self.user, blocked_user=self.recipient) |
                                        Q(blocked_user=self.user, blocker=self.recipient)).exists():
                return None
            # Получаем содержимое сообщения
            message = text_data_json.get('message')
            author_id = text_data_json.get('authorId')
            images = text_data_json.get('images')
            # Сохраняем сообщение в базу данных
            msg_obj = self.save_and_get_message(author_id, message, images)
            message_created_at = msg_obj.created_at.strftime('%m/%d/%y %H:%M:%S')
            # Отправляем сообщение на страницу чата
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_group_name,
                {
                    'type': 'chat_message',
                    'messageId': msg_obj.id,
                    'message': message,
                    'authorId': author_id,
                    'createdAt': message_created_at,
                    'authorProfileImage': self.user.profile_image.url,
                    'recipientProfileImage': self.recipient.profile_image.url,
                    'images': images,
                    'isSeen': msg_obj.seen
                }
            )
            # Отправляем сообщение на страницу списка чатов нам и собеседнику в ChatsListConsumer
            data = {
                'type': 'chats_list_message',
                'messageId': msg_obj.id,
                'message': message,
                'authorId': author_id,
                'authorName': msg_obj.author.name,
                'authorSurname': msg_obj.author.surname,
                'authorProfileImage': msg_obj.author.profile_image.url,
                'recipientId': self.recipient.id,
                'recipientName': self.recipient.name,
                'recipientSurname': self.recipient.surname,
                'recipientProfileImage': self.recipient.profile_image.url,
                'createdAt': message_created_at,
                'conversationId': self.conversation_id,
                'isSeen': msg_obj.seen,
            }
            async_to_sync(self.channel_layer.group_send)(
                self.our_chats_list_group_name,
                data
            )
            async_to_sync(self.channel_layer.group_send)(
                self.recipient_chats_list_group_name,
                data
            )
        elif command == 'fetch_content':
            # Подгружаем более старые сообщения
            async_to_sync(self.channel_layer.group_send)(
                self.conversation_group_name,
                {
                    'type': 'fetch_content',
                    'initiator': text_data_json.get('initiator'),
                    'receivedMessagesNumber': text_data_json.get('receivedMessagesNumber')
                }
            )
        elif command == 'delete_message':
            # Удаляем сообщение
            message_to_delete_id = text_data_json.get('messageId')
            user = self.scope['user']
            if self.delete_message(user, message_to_delete_id):
                # Отправляем информацию об удалении на страницу чата
                async_to_sync(self.channel_layer.group_send)(
                    self.conversation_group_name,
                    {
                        'type': 'chat_message_delete',
                        'messageId': message_to_delete_id,
                    }
                )
                # Отправляем информацию об удалении на страницу списка чатов нам и собеседнику в ChatsListConsumer
                async_to_sync(self.channel_layer.group_send)(
                    self.our_chats_list_group_name,
                    {
                        'type': 'chat_message_delete',
                        'messageId': message_to_delete_id,
                    }
                )
                async_to_sync(self.channel_layer.group_send)(
                    self.recipient_chats_list_group_name,
                    {
                        'type': 'chat_message_delete',
                        'messageId': message_to_delete_id,
                    }
                )
        elif command == 'mark_message_seen':
            # Отмечаем, что сообщение прочитано
            message_id = text_data_json.get('messageId')
            message = Message.objects.filter(id=message_id)
            if message.exists():
                message = message.first()
                message.seen = True
                message.save()
                # Отправляем информацию о прочтении в диалог
                async_to_sync(self.channel_layer.group_send)(
                    self.conversation_group_name,
                    {
                        'type': 'mark_message_seen',
                        'messageId': message_id,
                    }
                )
        else:
            print('Неизвестная команда')

    def mark_message_seen(self, event):
        """ Отправляет ответ вебсокету о том, что сообщение в чате было прочитано """
        self.send(text_data=json.dumps({
            'command': 'mark_message_seen',
            'messageId': event['messageId'],
        }))

    def delete_message(self, user, message_to_delete_id):
        """ Удаляет сообщение из бд по заданному id """
        qs = Message.objects.filter(id=message_to_delete_id, conversation__participants=user)
        if qs.exists():
            qs.first().delete()
            return True
        return False

    def fetch_content(self, event):
        """ Подгружает сообщения на странице при скролле чата вверх """
        received_messages_number = event['receivedMessagesNumber']
        # отправляем более старые сообщения тому, кто отправил запрос fetch_content
        if event['initiator'] == self.user.id:
            new_content = self.get_new_content(received_messages_number)
            self.send(text_data=json.dumps({
                'command': 'fetch_content',
                'newContent': new_content
            }))

    def get_new_content(self, received_messages_number):
        """ Создает и возвращает список сообщений messages_list. """
        conversation = get_object_or_404(Conversation, id=self.conversation_id)
        # Количество сообщений, которое подгружаем за раз. Должно совпадать с messagesPerFetch в chat.js
        messages_to_fetch = 10
        messages = Message.objects.filter(conversation=conversation).order_by('-id')[received_messages_number:received_messages_number+messages_to_fetch]
        messages_list = list()
        for message in messages:
            # Создаем словарь с изображениями в данном сообщении
            images = dict()
            image_objects = MessageMedia.objects.filter(message=message)
            for image_obj in image_objects:
                images.update({image_obj.id: image_obj.image.url})
            # Добавляем словарь с данными о сообщении в список сообщений
            messages_list.append({
                'messageId': message.id,
                'message': message.content,
                'authorId': message.author.id,
                'authorProfileImage': message.author.profile_image.url,
                'recipientProfileImage': self.recipient.profile_image.url,
                'createdAt': message.created_at.strftime('%m/%d/%y %H:%M:%S'),
                'images': images,
                'isSeen': message.seen
            })
        return messages_list

    def chat_message(self, event):
        """ Отправляет ответ вебсокету с данными нового сообщения """
        self.send(text_data=json.dumps({
            'command': 'send_message',
            'messageId': event['messageId'],
            'message': event['message'],
            'authorId': event['authorId'],
            'createdAt': event['createdAt'],
            'authorProfileImage': event['authorProfileImage'],
            'recipientProfileImage': event['recipientProfileImage'],
            'images': event['images'],
            'isSeen': event['isSeen']
        }))

    def chat_message_delete(self, event):
        """ Отправляет ответ вебсокету о том, что сообщение было удалено """
        self.send(text_data=json.dumps({
            'command': 'delete_message',
            'messageId': event['messageId'],
        }))

    def save_and_get_message(self, author_id, message, images):
        """ Добавляет новое сообщение в бд и возвращает его экземпляр """
        conversation = get_object_or_404(Conversation, id=self.conversation_id)
        author = get_object_or_404(User, id=author_id)
        message = Message.objects.create(
            conversation=conversation,
            author=author,
            content=message,
            seen=False
        )
        if images:
            for image_id, image_url in images.items():
                message_media = MessageMedia.objects.get(id=image_id)
                message_media.message = message
                message_media.save()
        return message


class ChatsListConsumer(WebsocketConsumer):
    def connect(self):
        """ При подключении к вебсокету получаем id пользователя, создаем название группы и добавляем пользователя в неё """
        # Получаем id пользователя
        self.user_id = str(self.scope['user'].id)
        # Создаем название группы
        self.chats_list_group_name = 'chats_list_' + self.user_id
        # Присоединяемся к группе
        async_to_sync(self.channel_layer.group_add)(
            self.chats_list_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Выходим из группы
        async_to_sync(self.channel_layer.group_discard)(
            self.chats_list_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        """ Метод, в который приходят сообщения от вебсокета. Используется только для подгрузки чатов при скролле
            страницы списка чатов вниз
        """
        text_data_json = json.loads(text_data)
        command = text_data_json.get('command')
        self.user = self.scope['user']
        self.chats_list_group_name = 'chats_list_' + str(self.user.id)
        if command == 'fetch_content':
            # Подгружаем более старые диалоги
            async_to_sync(self.channel_layer.group_send)(
                self.chats_list_group_name,
                {
                    'type': 'fetch_content',
                    'conversationIds': text_data_json.get('conversationIds')
                }
            )

    def fetch_content(self, event):
        """ Получает новые чаты при скролле страницы списка чатов вниз и отправляет ответ
            вебсокету со списком новых чатов
        """
        conversation_ids = event['conversationIds']
        new_conversations = self.get_new_conversations(conversation_ids)
        self.send(text_data=json.dumps({
            'command': 'fetch_content',
            'newConversations': new_conversations
        }))

    def get_new_conversations(self, conversation_ids):
        """ Создает и возвращает список чатов conversations_list. """
        conversations_to_fetch = 10  # Количество чатов, которое подгружается за один запрос
        user = self.scope['user']
        new_conversations = Conversation.objects.filter(participants=user).exclude(id__in=conversation_ids)
        conversations_list = list()
        for conversation in new_conversations:
            # Пропускаем диалоги без сообщений
            if not conversation.messages.all():
                continue
            # Получаем собеседника в данном чате и объект последнего сообщения
            participants = conversation.participants.all()
            recipient = participants.exclude(id=user.id).first()
            msg_obj = conversation.messages.all().last()
            # Добавляем данные о чате в список чатов
            conversations_list.append({
                'messageId': msg_obj.id,
                'message': msg_obj.content,
                'authorId': msg_obj.author.id,
                'authorName': msg_obj.author.name,
                'authorSurname': msg_obj.author.surname,
                'authorProfileImage': msg_obj.author.profile_image.url,
                'recipientId': recipient.id,
                'recipientName': recipient.name,
                'recipientSurname': recipient.surname,
                'recipientProfileImage': recipient.profile_image.url,
                'createdAt': msg_obj.created_at.strftime('%m/%d/%y %H:%M:%S'),
                'conversationId': conversation.id,
                'unseenMessages': conversation.messages.filter(seen=False).exclude(author=user).count()
            })
        return conversations_list[:conversations_to_fetch]

    def chats_list_message(self, event):
        """ Отправляет ответ вебсокету с информацией о чате и новом сообщении, чтобы обновить список чатов на странице
            списка чатов
        """
        conversation = Conversation.objects.get(id=event['conversationId'])
        unseen_messages = conversation.messages.filter(seen=False).exclude(author=self.scope['user']).count()
        self.send(text_data=json.dumps({
            'command': 'send_message',
            'messageId': event['messageId'],
            'message': event['message'],
            'authorId': event['authorId'],
            'authorName': event['authorName'],
            'authorSurname': event['authorSurname'],
            'recipientId': event['recipientId'],
            'recipientName': event['recipientName'],
            'recipientSurname': event['recipientSurname'],
            'recipientProfileImage': event['recipientProfileImage'],
            'authorProfileImage': event['authorProfileImage'],
            'createdAt': event['createdAt'],
            'conversationId': event['conversationId'],
            'unseenMessages': unseen_messages
        }))

    def chat_message_delete(self, event):
        """ Отправляет ответ вебсокету о том, что сообщение было удалено """
        self.send(text_data=json.dumps({
            'command': 'delete_message',
            'messageId': event['messageId'],
        }))

