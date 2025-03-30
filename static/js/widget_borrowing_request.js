/**
 * widget_borrowing_request.js
 *
 * This module handles the "Borrowing Request" widget
 * It exports two functions:
 *   - initWidgetBorrowingRequest: For initial widget loading
 *   - initRestoredWidget: For reinitializing a restored widget
 */

export function initWidgetBorrowingRequest(appendWidget, bringWidgetToFront, showPopupModal) {
  // Fetch the widget HTML from the server
  fetch('borrowing_request/')
    .then(response => response.text())
    .then(html => {
      var widgetElement = appendWidget(html);
      // Close button - binds click event to close the widget
      var closeButton = widgetElement.querySelector('#closeWidgetBorrowingRequest');
      if (closeButton) {
        closeButton.addEventListener('click', function(e) {
          e.preventDefault();
          widgetElement.remove();
        });
      }
      // Set user's timezone - automatically set timezone field based on user's browser settings
      var tzField = widgetElement.querySelector('#userTimeZone');
      if (tzField) {
        tzField.value = Intl.DateTimeFormat().resolvedOptions().timeZone;
      }
      // Form submission - handles sending the borrowing request via AJAX
      var form = widgetElement.querySelector('#borrowingForm');
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
            // Display the server response in a popup modal
            showPopupModal(data.html);
            form.reset();
          })
          .catch(error => console.error('Error sending borrowing request:', error));
        });
      }
      // Cancel button - binds click event to cancel and close the widget
      var cancelButton = widgetElement.querySelector('#cancelBorrowingRequest');
      if (cancelButton) {
        cancelButton.addEventListener('click', function(e) {
          e.preventDefault();
          widgetElement.remove();
        });
      }
      // "Select Recipients" button - binds click event to open the recipient selection modal
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
    .catch(error => console.error('Error loading borrowing request widget:', error));
}

export function initRestoredWidget(widgetElement, bringWidgetToFront, showPopupModal) {
  // Bind close button event to close the restored widget
  var closeButton = widgetElement.querySelector('#closeWidgetBorrowingRequest');
  if (closeButton) {
    closeButton.addEventListener('click', function(e) {
      e.preventDefault();
      widgetElement.remove();
    });
  }
  // Set user's timezone for the restored widget
  var tzField = widgetElement.querySelector('#userTimeZone');
  if (tzField) {
    tzField.value = Intl.DateTimeFormat().resolvedOptions().timeZone;
  }
  // Bind form submission event for the restored widget to send borrowing request via AJAX
  var form = widgetElement.querySelector('#borrowingForm');
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
        // Show response modal and reset form after submission
        showPopupModal(data.html);
        form.reset();
      })
      .catch(error => console.error('Error sending borrowing request:', error));
    });
  }
  // Bind cancel button event to close the restored widget
  var cancelButton = widgetElement.querySelector('#cancelBorrowingRequest');
  if (cancelButton) {
    cancelButton.addEventListener('click', function(e) {
      e.preventDefault();
      widgetElement.remove();
    });
  }
  // Bind "Select Recipients" button for the restored widget to open the recipient selection modal
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
