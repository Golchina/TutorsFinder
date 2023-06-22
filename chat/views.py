from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import Conversation, Message, MessageMedia, Blacklist
from account.models import User
from .forms import ConversationFilterForm


def upload_images(request):
    """ View для загрузки изображений при отправке их в сообщении.
        Нужно для того, чтобы не передавать изображения целиком по вебсокету, а передавать только ссылку на них
    """
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('image')
        saved_urls = dict()
        for file in uploaded_files:
            # Сохраняем изображение на диск
            saved_file_name = default_storage.save(file.name, file)
            # Получаем ссылку на изображение
            saved_url = default_storage.url(saved_file_name)
            # Создаем запись в бд со ссылкой на изображение
            media = MessageMedia.objects.create(image=saved_url)
            # Добавляем ссылку в словарь
            saved_urls.update({media.id: media.image.url})
        # Возвращаем словарь со ссылками
        return JsonResponse({'urls': saved_urls})
    else:
        return JsonResponse({'error': 'Invalid request method'})


@login_required(login_url='login')
def chats(request):
    """ View списка чатов. В GET запросе можно указать параметры фильтрации по имени и фамилии """
    conversations = Conversation.objects.filter(participants=request.user)

    # получаем параметры поиска из GET запроса
    full_name = request.GET.get('full_name')
    if full_name:
        # ищем совпадение по имени и фамилии
        # используется iregex, так как icontains неправильно работает с русским языком в sqlite
        conversations = conversations.filter(
            Q(participants__name__iregex=full_name.split()[0]) |
            Q(participants__surname__iregex=full_name.split()[-1]) |
            Q(participants__name__iregex=full_name.split()[-1]) |
            Q(participants__surname__iregex=full_name.split()[0])
        ).distinct()

    # Создаем список с чатами и дополнительными данными о них
    # В список не включаем чаты, в которых нет сообщений
    conversations_data = list()
    for conversation in conversations:
        recipient = conversation.participants.all().exclude(id=request.user.id).first()
        unseen_messages = conversation.messages.filter(seen=False, author=recipient).count()
        last_message = conversation.messages.last()
        if last_message:
            conversations_data.append({'conversation': conversation, 'recipient': recipient, 'last_message': last_message, 'unseen_messages': unseen_messages})
    # Сортируем список чатов по времени последнего сообщения (новые -> старые)
    conversations_data.sort(key=lambda x: x['last_message'].created_at, reverse=True)
    conversations_to_load = 8  # Количество чатов, которое изначально подгружаем на страницу
    form = ConversationFilterForm(request.GET)
    context = {
        'conversations_data': conversations_data[:conversations_to_load],
        'form': form
    }
    return render(request, 'chat/chats_list.html', context)


@login_required(login_url='login')
def chat(request, conversation_id):
    """ View чата. *Сообщения подгружаются в template с помощью javascript """
    # Получаем участников чата
    conversation = get_object_or_404(Conversation, id=conversation_id)
    participants = conversation.participants.all()
    # Запрещаем не участникам чата читать его
    if not participants.filter(id=request.user.id).exists():
        return render(request, 'account/not_authorized.html')
    # Находим получателя сообщений в чате
    recipient = participants.exclude(id=request.user.id).first()
    # Получаем данные о блокировке, чтобы в темплейте отобразить либо не отобразить форму отправки сообщений
    is_blocker = Blacklist.objects.filter(blocker=request.user, blocked_user=recipient)
    is_blocked = Blacklist.objects.filter(blocked_user=request.user, blocker=recipient)
    context = {
        'conversation_id': conversation_id,
        'recipient': recipient,
        'is_blocked': is_blocked,
        'is_blocker': is_blocker
    }
    return render(request, 'chat/chat.html', context)


@login_required(login_url='login')
def create_or_join_chat(request, recipient_id):
    """ Получаем или создаем диалог между двумя юзерами и делаем редирект на /chat/ид_диалога """
    participant_1 = get_object_or_404(User, id=request.user.id)
    participant_2 = get_object_or_404(User, id=recipient_id)
    conversation = Conversation.objects.filter(participants=participant_1).filter(participants=participant_2).first()

    if conversation is None:
        conversation = Conversation.objects.create()
        conversation.participants.add(participant_1, participant_2)

    return redirect(reverse('chat', kwargs={'conversation_id': conversation.id}))


@login_required(login_url='login')
def delete_chat(request, conversation_id):
    """ View удаления чата. Проверяет, есть ли такой чат и является ли пользователь его участником.
        Если условия выполнены, удаляет чат из бд вместе со всеми сообщениями и изображениями
    """
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if not conversation.participants.filter(id=request.user.id).exists():
        return HttpResponseForbidden()

    if request.method == "POST":
        conversation.delete()
        return redirect('chats')
    else:
        participant = conversation.participants.all().exclude(id=request.user.id).first()
        return render(request, "chat/delete_chat.html", {"conversation": conversation, "participant": participant})


@login_required(login_url='login')
def block_user(request, recipient_id):
    """ Добавляет пользователя в черный список = запрещает отсылать сообщения """
    # Проверяем, что существует пользователь, которого хотим заблокировать
    recipient = get_object_or_404(User, id=recipient_id)

    # Получаем объект чата, если его нет, отправляем на 404
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient)
    conversation = conversation.first() if conversation.exists() else None
    if conversation is None:
        raise Http404("Такой чат не найден")

    if request.method == 'POST':
        # Получили POST запрос с подтверждением блокировки
        # Проверяем, есть ли уже такая блокировка
        if not Blacklist.objects.filter(blocker=request.user, blocked_user=recipient).exists():
            # Создаем блокировку
            Blacklist.objects.create(blocker=request.user, blocked_user=recipient)
        # Перенаправляем пользователя
        return redirect(reverse('chat', kwargs={'conversation_id': conversation.id}))

    else:
        # Получили GET запрос, отправляем страницу с формой
        context = {'recipient': recipient, 'type': 'block'}
        return render(request, 'chat/blacklist.html', context)


@login_required(login_url='login')
def unblock_user(request, recipient_id):
    """ Убирает пользователя из черного списка """
    # Проверяем, что существует пользователь, которого хотим разблокировать
    recipient = get_object_or_404(User, id=recipient_id)

    # Получаем объект чата, если его нет, отправляем на 404
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient)
    conversation = conversation.first() if conversation.exists() else None
    if conversation is None:
        raise Http404("Такой чат не найден")

    if request.method == 'POST':
        # Получили POST запрос с подтверждением разблокировки
        # Проверяем, есть ли уже такая блокировка и удаляем её
        block = get_object_or_404(Blacklist, blocker=request.user, blocked_user=recipient)
        block.delete()
        return redirect(reverse('chat', kwargs={'conversation_id': conversation.id}))
    else:
        # Получили GET запрос, отправляем страницу с формой
        context = {'recipient': recipient, 'type': 'unblock'}
        return render(request, 'chat/blacklist.html', context)
