const userId = JSON.parse(document.getElementById('user_id').textContent);
let conversations = document.querySelector('.conversation')

// Создаем вебсокет
const chatSocket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/chats/'
);


// Получаем ответы от вебсокета
chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.command == 'send_message'){
        // Обновляем диалог на странице, когда пришло новое сообщение
        updateMessage(data, 'newMessage')
    } else if (data.command == 'delete_message'){
        // Обновляем диалог на странице, когда удалилось последнее сообщение в диалоге
        removeMessageIfLast(data.messageId)
    } else if (data.command == 'fetch_content') {
        // Подгружаем новые диалоги
        data.newConversations.forEach(conversation => conversation.createdAt = formatCreatedAt(conversation.createdAt))
        data.newConversations.forEach(conversation => updateMessage(conversation, 'oldMessage'))
    }
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};


// Обновляем диалог на экране
function updateMessage(messageData, updateType) {
    let messageRow = document.querySelector('[data-conversation-id="' + messageData.conversationId + '"]');
    if (messageData.message.trim().length == 0)
        messageData.message = 'Изображение'
    // Создаем элемент с количеством непрочитанных сообщений
    let unseenMessagesElement = ''
    if (messageData.unseenMessages > 0)
        unseenMessagesElement = `<span class="badge bg-danger rounded-pill float-end text-white">${messageData.unseenMessages}</span>`

    if (messageRow){
        // Заменяем текст сообщения
        if (messageData.authorId == userId){
            messageRow.querySelector('p').innerText = messageData.message
            messageRow.querySelector('p').insertAdjacentHTML( 'afterbegin', '<span class="font-weight-light">Вы: </span>' );
        } else
            messageRow.querySelector('p').innerText = messageData.message
        messageRow.querySelector('p').dataset.messageid = messageData.messageId
        // Заменяем дату
        let messageDate = messageRow.querySelector('.messageDate')
        console.log(messageData.createdAt)
        messageDate.innerText = formatCreatedAt(messageData.createdAt)
        // Добавляем количество непрочитанных сообщений
        messageRow.querySelector('.unseen-messages').innerHTML = unseenMessagesElement
        // Помещаем в начало страницы
        let pop = $('[data-conversation-id="' + messageData.conversationId + '"]');
        let parent = pop.parent();
        pop.detach();
        parent.prepend(pop);
    } else {
        // Создаем новый диалог
        let messages_list = document.querySelector('.card-body')
        let message_element

        if (messageData.authorId != userId){
            message_element = `
                <div class="row conversation" data-conversation-id="${messageData.conversationId}">
                  <div class="col">
                    <a href="/chats/chat/${messageData.conversationId}/" class="text-dark" style="">
                      <div class="row border-bottom py-3">
                        <div class="col-1">
                          <img src="${messageData.authorProfileImage}"
                               alt="avatar" class="rounded-circle" style="object-fit: cover; width: 45px; height: 45px;">
                        </div>
                        <div class="col-9">
                          <div class="row">
                            <div class="col-11">
                              <h5>${messageData.authorName} ${messageData.authorSurname}</h5>
                            </div>
                            <div class="unseen-messages col-1 d-flex align-items-start justify-content-end">
                                ${unseenMessagesElement}
                            </div>
                          </div>
                          <div class="row">
                            <div class="col">
                              <p data-messageId="${messageData.messageId}">${messageData.message}</p>
                            </div>
                          </div>
                        </div>
                        <div class="col-2">
                            <span class="messageDate">${messageData.createdAt}</span>
                        </div>
                      </div>
                    </a>
                  </div>
                </div>
            `
        } else {
            message_element = `
                <div class="row conversation" data-conversation-id="${messageData.conversationId}">
                  <div class="col">
                    <a href="/chats/chat/${messageData.conversationId}/" class="text-dark" style="">
                      <div class="row border-bottom py-3">
                        <div class="col-1">
                          <img src="${messageData.recipientProfileImage}"
                               alt="avatar" class="rounded-circle" style="object-fit: cover; width: 45px; height: 45px;">
                        </div>
                        <div class="col-9">
                          <div class="row">
                            <div class="col-11">
                              <h5>${messageData.recipientName} ${messageData.recipientSurname}</h5>
                            </div>
                            <div class="unseen-messages col-1 d-flex align-items-start justify-content-end">
                                ${unseenMessagesElement}
                            </div>
                          </div>
                          <div class="row">
                            <div class="col">
                              <p data-messageId="${messageData.messageId}">${messageData.message}</p>
                            </div>
                          </div>
                        </div>
                        <div class="col-2">
                            <span class="messageDate">${messageData.createdAt}</span>
                        </div>
                      </div>
                    </a>
                  </div>
                </div>
            `

        }
        // Добавляем диалог либо в начало списка диалогов, либо в конец
        if (updateType === 'newMessage')
            messages_list.insertAdjacentHTML('afterbegin', message_element);
        else if (updateType === 'oldMessage')
            messages_list.insertAdjacentHTML('beforeend', message_element);
        // Удаляем надпись: У вас нет сообщений
        noMessages = document.querySelector('.no-messages')
        if (noMessages)
            noMessages.remove()

    }
}

// Форматируем дату сообщения
function formatCreatedAt(createdAtStr){
    let options = {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: 'numeric',
      minute: 'numeric',
    };
    let createdAt = new Date(Date.parse(createdAtStr)).toLocaleString("ru", options).replace('в ', '');
    return createdAt
}

// Удаляем сообщение со страницы, если оно последнее в диалоге
function removeMessageIfLast(messageId){
    messageToRemove = document.querySelector(`[data-messageId="${messageId}"]`)
    if (messageToRemove)
        messageToRemove.innerText = ''
        messageToRemove.insertAdjacentHTML( 'afterbegin', '<span class="font-weight-light font-italic">Удалено</span>' );
}

// Подгружаем сообщения при пролистывании страницы
function handleScroll() {
    if ((window.innerHeight + window.pageYOffset) >= document.documentElement.scrollHeight) {
        let conversationIds = getConversationIds()
        chatSocket.send(JSON.stringify({
            'command': 'fetch_content',
            'conversationIds': conversationIds
        }));
    }
}
document.addEventListener("scroll", handleScroll);

// Получаем id диалогов находящихся на странице
function getConversationIds(){
    let conversationIds = []
    let conversations = document.querySelectorAll('.conversation')
    conversations.forEach(conversation => conversationIds.push(conversation.dataset.conversationId))
    return conversationIds

}