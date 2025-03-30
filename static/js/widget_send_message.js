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
  // Load widget HTML from server
  fetch('send_message/')
    .then(response => response.text())
    .then(html => {
      var widgetElement = appendWidget(html);
      // Attach event handler for closing the widget
      var closeButton = widgetElement.querySelector('#closeWidgetSendMessage');
      if (closeButton) {
        closeButton.addEventListener('click', function(e) {
          e.preventDefault();
          widgetElement.remove();
        });
      }
      // Attach event handler for form submission
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
            // Show popup modal with server response
            showPopupModal(data.html);
            form.reset();
          })
          .catch(error => console.error('Error sending message:', error));
        });
      }
      // Attach event handler for cancel action
      var cancelButton = widgetElement.querySelector('#cancelSendMessage');
      if (cancelButton) {
        cancelButton.addEventListener('click', function(e) {
          e.preventDefault();
          widgetElement.remove();
        });
      }
      // Attach event handler for select recipients button
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

// Initialize restored widget with re-bound event handlers
export function initRestoredWidget(widgetElement, bringWidgetToFront, showPopupModal) {
  // Re-bind event handlers as in initWidgetSendMessage
  var closeButton = widgetElement.querySelector('#closeWidgetSendMessage');
  if (closeButton) {
    closeButton.addEventListener('click', function(e) {
      e.preventDefault();
      widgetElement.remove();
    });
  }
  // Attach event handler for form submission in restored widget
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
        // Show popup modal with server response
        showPopupModal(data.html);
        form.reset();
      })
      .catch(error => console.error('Error sending message:', error));
    });
  }
  // Attach event handler for cancel action in restored widget
  var cancelButton = widgetElement.querySelector('#cancelSendMessage');
  if (cancelButton) {
    cancelButton.addEventListener('click', function(e) {
      e.preventDefault();
      widgetElement.remove();
    });
  }
  // Attach event handler for select recipients button in restored widget
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
