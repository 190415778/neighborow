/**
 * widget_messaging_outbox.js
 *
 * This module handles the Messages Outbox widget
 * It exports two functions:
 *   - initWidgetMessagingOutbox: For initial widget loading
 *   - initRestoredWidget: For reinitializing a restored widget
 */
export function initWidgetMessagingOutbox(appendWidget, bringWidgetToFront, showPopupModal) {
  // Fetch widget HTML from server
  fetch('messages_outbox/')
    .then(response => response.text())
    .then(html => {
      var widgetElement = appendWidget(html)
      // Bind top close button event to remove widget
      var topCloseButton = widgetElement.querySelector('#closeWidgetMessagesOutbox')
      if (topCloseButton) {
        topCloseButton.addEventListener('click', function() {
          widgetElement.remove()
        })
      }
      // Bind secondary close button event to remove widget
      var closeButton = widgetElement.querySelector('#closeMessagesOutbox')
      if (closeButton) {
        closeButton.addEventListener('click', function() {
          widgetElement.remove()
        })
      }
      // Bind click event on message list to display selected message body
      var messageList = widgetElement.querySelector('#messageList')
      var messageBodyDisplay = widgetElement.querySelector('#messageBodyDisplay')
      if (messageList && messageBodyDisplay) {
        messageList.addEventListener('click', function(e) {
          var row = e.target.closest('tr')
          if (row && row.dataset.messageId) {
            Array.from(messageList.getElementsByTagName('tr')).forEach(function(r) {
              r.classList.remove('table-active')
            })
            row.classList.add('table-active')
            // Clean and format message body before display
            var cleanBody = row.dataset.body.replace(/\\u002D\s*/g, '')
            cleanBody = cleanBody.replace(/\\u000A/g, "\n")
            cleanBody = cleanBody.replace(/\\u000D/g, "\r")
            messageBodyDisplay.value = cleanBody
          }
        })
      }
      // Implement infinite scroll to load additional messages
      var messageListContainer = widgetElement.querySelector('#messageListContainer')
      var currentPage = 1
      var loading = false
      if (messageListContainer) {
        messageListContainer.addEventListener('scroll', function() {
          if (loading) return
          if (messageListContainer.scrollTop + messageListContainer.clientHeight >= messageListContainer.scrollHeight - 10) {
            loading = true
            fetch('messages_outbox/?page=' + (currentPage + 1), {
              headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
              .then(response => response.json())
              .then(data => {
                if (data.html) {
                  messageList.insertAdjacentHTML('beforeend', data.html)
                  currentPage++
                  if (!data.has_next) {
                    messageListContainer.removeEventListener('scroll', arguments.callee)
                  }
                }
                loading = false
              })
              .catch(error => {
                console.error('Error loading more outbox messages:', error)
                loading = false
              })
          }
        })
      }
      // Periodically refresh outbox messages when scroll is at top
      setInterval(function refreshMessagesOutbox() {
        var container = widgetElement.querySelector('#messageListContainer')
        if (!container) return
        if (container.scrollTop > 0) return
        fetch('messages_outbox/?page=1', {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
          .then(response => response.json())
          .then(data => {
            if (data.html) {
              widgetElement.querySelector('#messageList').innerHTML = data.html
              currentPage = 1
            }
          })
          .catch(error => {
            console.error('Error refreshing outbox messages:', error)
            showPopupModal('<div>Error refreshing outbox messages: ' + error + '</div>')
          })
      }, 30000)
    })
    .catch(error => console.error('Error loading messaging outbox widget:', error))
}

export function initRestoredWidget(widgetElement, bringWidgetToFront, showPopupModal) {
  // Bind top close button event for restored widget to remove widget
  var topCloseButton = widgetElement.querySelector('#closeWidgetMessagesOutbox')
  if (topCloseButton) {
    topCloseButton.addEventListener('click', function() {
      widgetElement.remove()
    })
  }
  // Bind secondary close button event for restored widget to remove widget
  var closeButton = widgetElement.querySelector('#closeMessagesOutbox')
  if (closeButton) {
    closeButton.addEventListener('click', function() {
      widgetElement.remove()
    })
  }
  // Bind click event on message list in restored widget to display selected message body
  var messageList = widgetElement.querySelector('#messageList')
  var messageBodyDisplay = widgetElement.querySelector('#messageBodyDisplay')
  if (messageList && messageBodyDisplay) {
    messageList.addEventListener('click', function(e) {
      var row = e.target.closest('tr')
      if (row && row.dataset.messageId) {
        Array.from(messageList.getElementsByTagName('tr')).forEach(function(r) {
          r.classList.remove('table-active')
        })
        row.classList.add('table-active')
        // Clean and format message body before display
        var cleanBody = row.dataset.body.replace(/\\u002D\s*/g, '')
        cleanBody = cleanBody.replace(/\\u000A/g, "\n")
        cleanBody = cleanBody.replace(/\\u000D/g, "\r")
        messageBodyDisplay.value = cleanBody
      }
    })
  }
  // Implement infinite scroll to load additional messages in restored widget
  var messageListContainer = widgetElement.querySelector('#messageListContainer')
  var currentPage = 1
  var loading = false
  if (messageListContainer) {
    messageListContainer.addEventListener('scroll', function() {
      if (loading) return
      if (messageListContainer.scrollTop + messageListContainer.clientHeight >= messageListContainer.scrollHeight - 10) {
        loading = true
        fetch('messages_outbox/?page=' + (currentPage + 1), {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
          .then(response => response.json())
          .then(data => {
            if (data.html) {
              messageList.insertAdjacentHTML('beforeend', data.html)
              currentPage++
              if (!data.has_next) {
                messageListContainer.removeEventListener('scroll', arguments.callee)
              }
            }
            loading = false
          })
          .catch(error => {
            console.error('Error loading more outbox messages:', error)
            loading = false
          })
      }
    })
  }
  // Periodically refresh outbox messages in restored widget when scroll is at top
  setInterval(function refreshMessagesOutbox() {
    var container = widgetElement.querySelector('#messageListContainer')
    if (!container) return
    if (container.scrollTop > 0) return
    fetch('messages_outbox/?page=1', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
      .then(response => response.json())
      .then(data => {
        if (data.html) {
          widgetElement.querySelector('#messageList').innerHTML = data.html
          currentPage = 1
        }
      })
      .catch(error => {
        console.error('Error refreshing outbox messages:', error)
        showPopupModal('<div>Error refreshing outbox messages: ' + error + '</div>')
      })
  }, 30000)
}
