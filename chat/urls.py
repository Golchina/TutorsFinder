from django.urls import path
from chat.views import chat, delete_chat, create_or_join_chat, chats, upload_images, block_user, unblock_user


urlpatterns = [
    path('chat/<int:conversation_id>/', chat, name='chat'),
    path('delete/chat/<int:conversation_id>/', delete_chat, name='delete_chat'),
    path('create-or-join-chat/<int:recipient_id>/', create_or_join_chat, name='create_or_join_chat'),
    path('', chats, name='chats'),
    path('upload_images/', upload_images, name='upload_images'),
    path('block/<int:recipient_id>/', block_user, name='block_user'),
    path('unblock/<int:recipient_id>/', unblock_user, name='unblock_user')
]
