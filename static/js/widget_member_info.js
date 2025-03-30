/**
 * widget_member_info.js
 *
 * This module handles the Member Info widget
 * It exports two functions:
 *   - initWidgetMemberInfo: For initial widget loading
 *   - initRestoredWidget: For reinitializing a restored widget
 */

export function initWidgetMemberInfo(appendWidget, bringWidgetToFront, showPopupModal) {
  fetch('member_info/')
    .then(response => response.text())
    .then(html => {
      var widgetElement = appendWidget(html)
      // Close button event handler
      var closeButton = widgetElement.querySelector('#closeWidgetMemberInfo')
      if (closeButton) {
        closeButton.addEventListener('click', function() {
          widgetElement.remove()
        })
      }
      // Cancel button event handler
      var cancelButton = widgetElement.querySelector('#cancelMemberInfo')
      if (cancelButton) {
        cancelButton.addEventListener('click', function(e) {
          e.preventDefault()
          widgetElement.remove()
        })
      }
      // Form submission to update member info
      var form = widgetElement.querySelector('#memberInfoForm')
      if (form) {
        form.addEventListener('submit', function(ev) {
          ev.preventDefault()
          // Create form data from the form element
          var formData = new FormData(form)
          fetch(form.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
          })
          .then(response => response.json())
          .then(data => {
            // Show popup modal with response HTML
            showPopupModal(data.html)
          })
          .catch(error => console.error('Error updating member info:', error))
        })
      }
    })
    .catch(error => console.error('Error loading member info widget:', error))
}

export function initRestoredWidget(widgetElement, bringWidgetToFront, showPopupModal) {
  // Bind event to close restored widget using the close button
  var closeButton = widgetElement.querySelector('#closeWidgetMemberInfo')
  if (closeButton) {
    closeButton.addEventListener('click', function() {
      widgetElement.remove()
    })
  }
  // Bind event to cancel restored widget using the cancel button
  var cancelButton = widgetElement.querySelector('#cancelMemberInfo')
  if (cancelButton) {
    cancelButton.addEventListener('click', function(e) {
      e.preventDefault()
      widgetElement.remove()
    })
  }
  // Bind form submission in restored widget to update member info
  var form = widgetElement.querySelector('#memberInfoForm')
  if (form) {
    form.addEventListener('submit', function(ev) {
      ev.preventDefault()
      // Prepare form data for submission
      var formData = new FormData(form)
      fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        // Display response in a popup modal
        showPopupModal(data.html)
      })
      .catch(error => console.error('Error updating member info:', error))
    })
  }
}
