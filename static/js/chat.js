// Количество отображенных сообщений в чате на данный момент
let receivedMessagesNumber = 0
// Сколько сообщений подгружать за раз (должно совпадать с messages_to_fetch в ChatConsumer)
let messagesPerFetch = 10

const conversationId = JSON.parse(document.getElementById('conversation_id').textContent);
const userId = JSON.parse(document.getElementById('user_id').textContent);
// Cоздаем вебсокет
const chatSocket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/chat/'
    + conversationId
    + '/'
);

// Прогружаем первые 10 сообщений
chatSocket.onopen = function(e) {
    chatSocket.send(JSON.stringify({
        'command': 'fetch_content',
        'initiator': userId,
        'receivedMessagesNumber': receivedMessagesNumber
    }));
}

// Получаем ответы от вебсокета
chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    let createdAt = formatCreatedAt(data.createdAt)
    if (data.command === 'send_message'){
        // Добавляем новое сообщение на страницу
        let appendType = 'append'
        appendMessage(data, appendType)
        receivedMessagesNumber += 1
    } else if (data.command === 'fetch_content' && data.newContent.length > 0) {
        // Подгружаем старые сообщения при пролистывании вверх
        let appendType = 'prepend'
        receivedMessagesNumber += messagesPerFetch
        // Сохраняем позицию сообщений на экране
        let messagesDiv = document.getElementById('messages_list');
        let prevScrollHeight = messagesDiv.scrollHeight;
        // Добавляем сообщения на страницу
        data.newContent.forEach(element => appendMessage(element, appendType))
        // Возвращаемся к сохранённой позиции
        let newScrollHeight = messagesDiv.scrollHeight;
        let scrollTop = messagesDiv.scrollTop + (newScrollHeight - prevScrollHeight);
        messagesDiv.scrollTop = scrollTop;
    } else if (data.command === 'delete_message') {
        // Удаляем сообщение
        removeMessageFromDom(data.messageId)
    } else if (data.command === 'mark_message_seen'){
        // Отмечаем сообщения как прочитанные
        let row = document.querySelector(`[data-messageId="${data.messageId}"]`);
        if (row){
            row.dataset.isseen = 'true';
            if (row.dataset.authorid == userId){
                // Меняем одиночную галочку на двойную
                let notSeen = row.querySelector('.message-not-seen')
                notSeen.style.display = 'none'
                let seen = row.querySelector('.message-seen')
                seen.style.display = 'inline'
                console.log('changed style', data.messageId)
            } else {
              setTimeout(function() {
                $(".message-content").removeClass("border border-primary");
              }, 3000);
            }
        }
    }
};

// Закрытие соединения
chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

// Предпросмотр изображений перед отправкой
let imageInput = document.querySelector('#image-input');
let imagePreview = document.querySelector('#image-preview');
let uploadedImages = [];
// Проверяем, заблокирована ли отправка сообщений = imageInput не будет на экране
if (imageInput){
    // Слушаем изменение imageInput
    imageInput.addEventListener('change', function(event) {
      let files = event.target.files;
      // Добавляем загруженные изображения на экран и в список uploadedImages
      for (let i = 0; i < files.length; i++) {
        let file = files[i];
        let reader = new FileReader();

        reader.addEventListener('load', function(event) {
          const imageUrl = event.target.result;
          const imageElement = createImageElement(file, imageUrl);
          uploadedImages.push(file);
          document.querySelector('#image-preview').appendChild(imageElement);
        });

        reader.readAsDataURL(file);
      }
    });

    // Добавление выбранного изображения на экран под чатом
    function createImageElement(file, imageUrl) {
      const containerElement = document.createElement('div');
      const imageElement = document.createElement('img');
      const removeButton = document.createElement('button');
      const removeLabel = document.createElement('label');
      const removeIcon = document.createElement('i');

      containerElement.classList.add('image-container');
      containerElement.classList.add('ml-2');
      imageElement.src = imageUrl;
      imageElement.style.width = '50px'
      removeButton.style.display = 'none';
      removeButton.id = 'remove-button'
      removeLabel.htmlFor = 'remove-button'
      removeLabel.appendChild(removeIcon)
      removeIcon.classList.add('remove-icon', 'fas', 'fa-times');
      removeButton.addEventListener('click', function() {
        const index = uploadedImages.findIndex(function(item) {
          return item.name === file.name;
        });
        if (index !== -1) {
          uploadedImages.splice(index, 1);
          containerElement.remove();
        }
      });

      containerElement.appendChild(imageElement);
      containerElement.appendChild(removeButton);
      containerElement.appendChild(removeLabel);
      return containerElement;
    }

    // Отправка сообщения при нажатии enter
    document.querySelector('#message_input').addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
          document.querySelector('#send_message').click();
        }
    });

    // Отправка сообщения при нажатии на кнопку отправить
    document.querySelector('#message-form').addEventListener('submit', function(e) {
      // Предотвращаем дефолтную отправку формы после нажатия кнопки submit
      e.preventDefault();
      // Получаем инпут сообщения
      let messageInputDom = document.querySelector('#message_input');
      // Получаем текст сообщения
      let message = messageInputDom.value;

      let formData = new FormData($(this)[0]);
      // Обрабатываем отправку сообщения с изображениями
      if (uploadedImages.length > 0){
          sendMessageWithImages(message, userId, uploadedImages, formData)
      }
      // Обрабатываем отправку непустого сообщения без изображений
      else if (message.trim().length > 0) {
        // Отправляем запрос по вебсокету
        chatSocket.send(JSON.stringify({
        'command': 'send_message',
        'message': message,
        'authorId': userId,
        }));
      }
      // После отправки сообщения очищаем форму
      messageInputDom.value = '';
      uploadedImages.length = 0

    });

    // Загружаем изображения на сервер с помощью ajax, потом передаем их url по вебсокету
    function sendMessageWithImages(message, userId, images, formData){
      // Добавляем изображения в formData
      for (let i = 0; i < images.length; i++) {
        formData.append('image', images[i]);
      }
      // url, по которому вызывается view загрузки изображений
      let uploadFileUrl = 'http://' + window.location.host + '/chats/upload_images/';

      // Устанавливаем csrf токен
      let csrftoken = getCookie('csrftoken');
      $.ajaxSetup({
        headers: { "X-CSRFToken": csrftoken }
      });
      // ajax запрос, который загружает изображение(я) на сервер и возвращает словарь {id: url}
      // затем в случае успешной загрузки отправляет запрос по вебсокету с текстом сообщения и словарём изображений
      $.ajax({
        url: uploadFileUrl,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
                  var urls = response.urls;
                    chatSocket.send(JSON.stringify({
                        'command': 'send_message',
                        'message': message,
                        'authorId': userId,
                        'images': urls
                    }));
                    let imgPreview = document.querySelector('#image-preview')
                    imgPreview.innerHTML = ''
                    document.querySelector('#message-form').reset();
        },
        error: function(xhr, status, error) {
          console.log(error);
        }
      });
    }

    // Emoji
    const emojis = [
      "😀", "😁", "😂", "🤣", "😃", "😄", "😅", "😆", "😉", "😊", "😋", "😎", "😍", "😘", "😜", "😝", "🤑", "🤗", "🤔", "🤐", "🤢", "🤮", "🤯", "😷", "🤒", "🤕", "😵", "🥳", "🥺", "🤩", "🤪", "🤬", "🥴", "🥵", "🥶"
    ];
    // Создаем и наполняем элемент с emoji
    const emojiPopup = document.getElementById("emoji-popup");
    const emojiContainer = emojiPopup.querySelector("div");
    for (let emoji of emojis) {
      const button = document.createElement("button");
      button.innerHTML = emoji;
      button.style.fontFamily = "Segoe UI Emoji";
      button.style.fontSize = "1.5em";
      button.style.backgroundColor =  "white";
      button.style.border = "none";
      button.type = "button"
      // По клику на emoji добавляем его в конец сообщения и закрываем список emoji
      button.addEventListener("click", function(e) {
        e.preventDefault()
        const input = document.getElementById("message_input");
        input.value += emoji;
        emojiPopup.style.display = "none";
      });
      emojiContainer.appendChild(button);
    }

    // Открытие и закрытие списка emoji по клику на значок в чате
    document.getElementById("emoji-btn").addEventListener("click", function() {
      if (emojiPopup.style.display == "block")
        emojiPopup.style.display = "none";
      else
        emojiPopup.style.display = "block";
    });

    // Убираем список emoji при клике на страницу
    document.addEventListener("click", function(event) {
      const isClickInsideEmojiPopup = emojiPopup.contains(event.target);
      const isClickInsideEmojiButton = event.target.id === "emoji-btn";
      if (!isClickInsideEmojiPopup && !isClickInsideEmojiButton) {
        emojiPopup.style.display = "none";
      }
    });
}

// Удаление сообщений
document.addEventListener("DOMContentLoaded", function() {
  const messageTable = document.querySelector(".message-table");

    // Появление кнопки удалить при наведении
  messageTable.addEventListener("mouseover", function(event) {
    const target = event.target;
    if (target.parentNode.classList.contains("message-row") || target.classList.contains("message-row")) {
      const deleteMessage = target.querySelector(".delete-message");
      deleteMessage.style.display = "inline-block";
    }
    // Удаление кнопки удалить
    target.addEventListener("mouseleave", function(event) {
    const target = event.target;
    if (target.parentNode.classList.contains("message-row") || target.classList.contains("message-row")) {
      const deleteMessage = target.querySelector(".delete-message");
      deleteMessage.style.display = "none";
    }
    });
  });

  messageTable.addEventListener("click", function(event) {
    const target = event.target;

    // Нажатие на кнопку удалить
    if (target.classList.contains("delete-message")) {
      const row = target.closest(".message-row");
      const confirmDelete = row.querySelector(".confirm-delete");
      const cancelDelete = row.querySelector(".cancel-delete");

      target.style.display = "none";
      confirmDelete.style.display = "inline-block";
      cancelDelete.style.display = "inline-block";
    // Нажатие на отмену удаления
    } else if (target.classList.contains("cancel-delete")) {
      const row = target.closest(".message-row");
      const deleteMessage = row.querySelector(".delete-message");
      const confirmDelete = row.querySelector(".confirm-delete");
      const cancelDelete = row.querySelector(".cancel-delete");

      confirmDelete.style.display = "none";
      cancelDelete.style.display = "none";
      deleteMessage.style.display = "inline-block";
    // Нажатие на подтверждение удаления
    } else if (target.classList.contains("confirm-delete")) {
      const row = target.closest(".message-row");
      removeMessage(row); //assuming that removeMessage() is defined elsewhere
    }
  });
});

// Отправляем сообщение об удалении
function removeMessage(row){
    let messageId = row.dataset.messageid
    chatSocket.send(JSON.stringify({
        'command': 'delete_message',
        'messageId': messageId
        }));
}

// Удаляем сообщение со страницы
function removeMessageFromDom(messageId){
    row = document.querySelector(`[data-messageId="${messageId}"]`);
    row.remove()
}

// Добавление сообщения на страницу в начало или в конец диалога
function appendMessage(messageData, appendType) {
    let messages_list = $('#messages_list')

    let messageElement = ``
    let imageElements = ``
    let messageBlock
    // Настраиваем элемент прочитано ли сообщение
    let seenElement
    if (messageData.isSeen){
        seenElement = `
          <i class="fa fa-check message-not-seen" style="display: none;"></i>
          <i class="fa fa-check-double message-seen" style=""></i>
        `
    } else {
        seenElement = `
          <i class="fa fa-check message-not-seen" style=""></i>
          <i class="fa fa-check-double message-seen" style="display: none;"></i>
        `
    }

    // Настраиваем элемент сообщения в зависимости от того, отправили мы его или получили
    if (messageData.authorId == userId){
        // Элемент текста сообщения, если оно не пустое
        if (messageData.message && messageData.message.trim()){
            messageElement = `<p class="small p-2 me-3 mb-1 bg-primary text-white ml-auto" style="border-radius: 10px; word-wrap: break-word; word-break: break-word;">${messageData.message}</p>`
        }
        // Элемент изображений
        if (messageData.images){
            let imageBaseLink = 'http://' + window.location.host
            for (const [key, value] of Object.entries(messageData.images)) {
                imageElements +=
                    `<p class="small p-2 ms-3 mb-1 bg-primary text-white"
                        style="border-radius: 10px; word-wrap: break-word; word-break: break-word;">
                     <a href="${imageBaseLink}${value}" class="">
                        <img width="200" src="${imageBaseLink}${value}" alt="Image">
                     </a>
                     </p>`
            }
        }
        // Основной элемент сообщения, в который встраиваются остальные элементы
        messageBlock = `
              <div data-messageId="${messageData.messageId}" data-authorId="${messageData.authorId}" data-isSeen="${messageData.isSeen}" class="message-row d-flex flex-row justify-content-end">
                <div class="d-flex flex-column">
                  ${messageElement}
                  ${imageElements}
                  <p class="small me-3 mb-3 rounded-3 text-muted ml-auto">
                      <i class="fa fa-trash delete-message" style="display: none;"></i>
                      <i class="fa fa-check confirm-delete" style="display: none;"></i>
                      <i class="fa fa-times cancel-delete" style="display: none;"></i>
                      ${formatCreatedAt(messageData.createdAt)}
                      ${seenElement}
                  </p>

                </div>
                <img src="${messageData.authorProfileImage}"
                  alt="Фото профиля" class="rounded-circle ml-2" style="object-fit: cover; width: 45px; height: 45px;">
              </div>
        `
    } else {
        // Элемент прочитано/не прочитано
        let unseenClass
        if (messageData.isSeen)
            unseenClass = ''
        else if (messageData.command != 'send_message')
            unseenClass = 'border border-primary'
        // Элемент текста сообщения, если оно не пустое
        if (messageData.message && messageData.message.trim()){
            messageElement = `<p class="message-content small p-2 ms-3 mb-1 mr-auto ${unseenClass}" style="background-color: #f5f6f7; border-radius: 10px; word-wrap: break-word; word-break: break-word;">${messageData.message}</p>`
        }
        // Элемент изображений
        if (messageData.images){
            let imageBaseLink = 'http://' + window.location.host
            for (const [key, value] of Object.entries(messageData.images)) {
                imageElements +=
                    `<p class="message-content small p-2 ms-3 mb-1 ${unseenClass}"
                        style="border-radius: 10px; word-wrap: break-word; word-break: break-word; background-color: #f5f6f7;">
                     <a href="${imageBaseLink}${value}" class="">
                        <img width="200" src="${imageBaseLink}${value}" alt="Image">
                     </a>
                     </p>`
            }
        }
        // Основной элемент сообщения, в который встраиваются остальные элементы
        messageBlock = `
              <div data-messageId="${messageData.messageId}" data-authorId="${messageData.authorId}" data-isSeen="${messageData.isSeen}" class="message-row d-flex flex-row justify-content-start">
                <img src="${messageData.authorProfileImage}"
                  alt="Фото профиля" class="rounded-circle mr-2" style="object-fit: cover; width: 45px; height: 45px;">
                <div class="d-flex flex-column">
                  ${messageElement}
                  ${imageElements}
                  <p class="small ms-3 mb-3 rounded-3 text-muted float-end">
                      <i class="fa fa-trash delete-message" style="display: none;"></i>
                      <i class="fa fa-check confirm-delete" style="display: none;"></i>
                      <i class="fa fa-times cancel-delete" style="display: none;"></i>
                      ${formatCreatedAt(messageData.createdAt)}</p>
                </div>
              </div>
        `
    }
    // Добавляем элемент сообщения в конец или в начало чата
    if (appendType === 'append') {
        // Смотрим, пролистаны ли сообщения полностью вниз
        let myDiv = document.getElementById('messages_list');
        let toScroll = myDiv.scrollTop + myDiv.clientHeight >= myDiv.scrollHeight;
        // Прикрепляем новое сообщение
        messages_list.append($(messageBlock));
        // Пролистываем сообщения вниз, если они до этого были пролистаны вниз
        if (toScroll){
        myDiv.scrollTop = myDiv.scrollHeight;
        }
    } else
        messages_list.prepend($(messageBlock));
}


// Пролистываем сообщения вниз при загрузке страницы
window.onload = function() {
    var myDiv = document.getElementById('messages_list');
    myDiv.scrollTop = myDiv.scrollHeight;
};


// Подгружаем сообщения при пролистывании страницы
let content = document.getElementById("messages_list");
function handleScroll() {
    if (content.scrollTop == 0) {
        chatSocket.send(JSON.stringify({
            'command': 'fetch_content',
            'initiator': userId,
            'receivedMessagesNumber': receivedMessagesNumber
        }));
    }
}
content.addEventListener("scroll", handleScroll);


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


// Отмечаем прочитанные сообщения
function messageSeen(messageId) {
  let messageRow = document.querySelector(`[data-messageId="${messageId}"]`);
  if (messageRow.dataset.isseen === 'false' && (messageRow.dataset.authorid != userId)) {
    console.log('seen')
    chatSocket.send(JSON.stringify({
        'command': 'mark_message_seen',
        'messageId': messageId
    }));
  }
}


// Ждем, пока сообщение будет на экране, чтобы отметить его как прочитанное
const messageTable = document.querySelector('#messages_list');
const observer = new IntersectionObserver(function(entries) {
  entries.forEach(function(entry) {
    if (entry.isIntersecting) {
      const messageRow = entry.target;
      messageSeen(messageRow.dataset.messageid);
      observer.unobserve(messageRow);
    }
  });
});

const mutationObserver = new MutationObserver(function(mutations) {
  mutations.forEach(function(mutation) {
    if (mutation.addedNodes) {
      mutation.addedNodes.forEach(function(node) {
        if (node.classList && node.classList.contains('message-row')) {
          observer.observe(node);
        }
      });
    }
  });
});

const observerConfig = { childList: true, subtree: true };
mutationObserver.observe(messageTable, observerConfig);


// Функция для получения cookie. Нужна, чтобы достать csrf токен и использовать его при отправке фото через ajax
function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}