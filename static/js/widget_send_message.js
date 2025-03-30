/**
 * widget_send_message.js
 *
 * This module handles the Send Message widget
 * It exports two functions:
 *   - initWidgetSendMessage: Called on initial widget load
 *   - initRestoredWidget: Called on widget restoration (from saved state)
 */

// Initialize widget send message module
export function initWidgetSendMessage(appendWidget, bringWidgetToFront, getCookie, showPopupModal) {
  // load widget html
  fetch('send_message/')
    .then(response => response.text())
    .then(html => {
      var widgetElement = appendWidget(html);

      // close-Button
      var closeButton = widgetElement.querySelector('#closeWidgetSendMessage');
      if (closeButton) {
        closeButton.addEventListener('click', function(e) {
          e.preventDefault();
          widgetElement.remove();
        });
      }

      // Form-Submit
      var form = widgetElement.querySelector('#sendMessageForm');
      if (form) {
        form.addEventListener('submit', function(ev) {
          ev.preventDefault();
          var formData = new FormData(form);
          fetch(form.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
          })
          .then(response => response.json())
          .then(data => {
            // show Popup 
            showPopupModal(data.html);
            form.reset();
            widgetElement.remove();  // Widget close
          })
          .catch(error => console.error('Error sending message:', error));
        });
      }

      // Cancel-Button
      var cancelButton = widgetElement.querySelector('#cancelSendMessage');
      if (cancelButton) {
        cancelButton.addEventListener('click', function(e) {
          e.preventDefault();
          widgetElement.remove();
        });
      }

      // Button zur choose receiver
      var selectRecipientsButton = widgetElement.querySelector('#selectRecipients');
      if (selectRecipientsButton) {
        selectRecipientsButton.addEventListener('click', function(e) {
          e.preventDefault();
          fetch('select_recipients/')
            .then(response => response.text())
            .then(modalHtml => {
              var modalContainer = document.getElementById('modalContainer');
              modalContainer.innerHTML = modalHtml;
              if (typeof initSelectRecipientsFilter === 'function') {
                initSelectRecipientsFilter();
              }
              var modalSelectRecipientsEl = document.getElementById('modalSelectRecipients');
              if (modalSelectRecipientsEl) {
                var modalSelectRecipients = new bootstrap.Modal(modalSelectRecipientsEl);
                modalSelectRecipients.show();
              }
            })
            .catch(error => console.error('Error loading select recipients modal:', error));
        });
      }
    })
    .catch(error => console.error('Error loading widgetSendMessage:', error));
}

export function initRestoredWidget(widgetElement, bringWidgetToFront, showPopupModal) {
  var closeButton = widgetElement.querySelector('#closeWidgetSendMessage');
  if (closeButton) {
    closeButton.addEventListener('click', function(e) {
      e.preventDefault();
      widgetElement.remove();
    });
  }
  
  var form = widgetElement.querySelector('#sendMessageForm');
  if (form) {
    form.addEventListener('submit', function(ev) {
      ev.preventDefault();
      var formData = new FormData(form);
      fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        showPopupModal(data.html);
        form.reset();
        widgetElement.remove();  
      })
      .catch(error => console.error('Error sending message:', error));
    });
  }
  
  var cancelButton = widgetElement.querySelector('#cancelSendMessage');
  if (cancelButton) {
    cancelButton.addEventListener('click', function(e) {
      e.preventDefault();
      widgetElement.remove();
    });
  }
  
  var selectRecipientsButton = widgetElement.querySelector('#selectRecipients');
  if (selectRecipientsButton) {
    selectRecipientsButton.addEventListener('click', function(e) {
      e.preventDefault();
      fetch('select_recipients/')
        .then(response => response.text())
        .then(modalHtml => {
          var modalContainer = document.getElementById('modalContainer');
          modalContainer.innerHTML = modalHtml;
          if (typeof initSelectRecipientsFilter === 'function') {
            initSelectRecipientsFilter();
          }
          var modalSelectRecipientsEl = document.getElementById('modalSelectRecipients');
          if (modalSelectRecipientsEl) {
            var modalSelectRecipients = new bootstrap.Modal(modalSelectRecipientsEl);
            modalSelectRecipients.show();
          }
        })
        .catch(error => console.error('Error loading select recipients modal:', error));
    });
  }
}
