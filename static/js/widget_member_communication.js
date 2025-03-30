/**
 * widget_member_communication.js
 *
 * This module handles the Member Communication widget
 * It exports two functions:
 *   - initWidgetMemberCommunication: For initial widget loading
 *   - initRestoredWidget: For reinitializing a restored widget
 */

export function initWidgetMemberCommunication(appendWidget, bringWidgetToFront, showPopupModal) {
  // Retrieve widget HTML from server
  fetch('member_communication/')
    .then(response => response.text())
    .then(html => {
      var widgetElement = appendWidget(html)
      // Bind close button event to remove widget
      var closeButton = widgetElement.querySelector('#closeWidgetMemberCommunication')
      if (closeButton) {
        closeButton.addEventListener('click', function() {
          widgetElement.remove()
        })
      }
      // Bind form submit event to save communications
      var form = widgetElement.querySelector('#memberCommunicationForm')
      if (form) {
        form.addEventListener('submit', function(ev) {
          ev.preventDefault()
          var formData = new FormData(form)
          fetch(form.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
          })
            .then(response => response.json())
            .then(data => {
              // Show popup modal with response content
              showPopupModal(data.html)
            })
            .catch(error => console.error('Error saving communications:', error))
        })
      }
      // Initialize communication widget features
      initCommunicationWidget(widgetElement)
    })
    .catch(error => console.error('Error loading member communication widget:', error))
}

export function initRestoredWidget(widgetElement, bringWidgetToFront, showPopupModal) {
  // Bind close button event in restored widget
  var closeButton = widgetElement.querySelector('#closeWidgetMemberCommunication')
  if (closeButton) {
    closeButton.addEventListener('click', function() {
      widgetElement.remove()
    })
  }
  // Bind form submit event in restored widget to save communications
  var form = widgetElement.querySelector('#memberCommunicationForm')
  if (form) {
    form.addEventListener('submit', function(ev) {
      ev.preventDefault()
      var formData = new FormData(form)
      fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        body: formData
      })
        .then(response => response.json())
        .then(data => {
          // Show popup modal with response content
          showPopupModal(data.html)
        })
        .catch(error => console.error('Error saving communications:', error))
    })
  }
  // Initialize communication widget features in restored widget
  initCommunicationWidget(widgetElement)
}

/**
* initCommunicationWidget
* Internal function to bind event listeners for adding new rows
* deleting rows and validating input in the Member Communication widget
*/
function initCommunicationWidget(widgetElement) {
  var rowCounterInput = widgetElement.querySelector('#rowCounter')
  if (!rowCounterInput) return
  var rowCounter = parseInt(rowCounterInput.value, 10) || 0
  var addRowButton = widgetElement.querySelector('#addCommunicationRow')
  if (addRowButton) {
    addRowButton.addEventListener('click', function(e) {
      e.preventDefault()
      rowCounter++
      rowCounterInput.value = rowCounter
      var newRow = document.createElement('tr')
      newRow.innerHTML = `
        <td>
          <input type="hidden" name="comm_id_${rowCounter}" value="">
        </td>
        <td>
          <select name="channel_${rowCounter}" class="form-control">
            <option value="">-- Select Channel --</option>
            <option value="1">email</option>
            <option value="2">text messages</option>
            <option value="3">WhatsApp</option>
          </select>
        </td>
        <td>
          <input type="text" name="identification_${rowCounter}" value="" class="form-control">
        </td>
        <td>
          <input type="checkbox" name="is_active_${rowCounter}">
        </td>
        <td>
          <button type="button" class="btn btn-danger delete-row-btn">Delete</button>
          <input type="hidden" name="delete_${rowCounter}" value="0">
        </td>
      `
      // Append the new row to the table body for new rows
      var newRowsTbody = widgetElement.querySelector('#newRows')
      if (newRowsTbody) {
        newRowsTbody.appendChild(newRow)
      }
    })
  }
  var communicationTable = widgetElement.querySelector('#communicationTable')
  if (communicationTable) {
    // Delegate click event for delete row button in the communication table
    communicationTable.addEventListener('click', function(e) {
      if (e.target && e.target.classList.contains('delete-row-btn')) {
        var row = e.target.closest('tr')
        var commIdInput = row.querySelector('input[name^="comm_id_"]')
        if (commIdInput && commIdInput.value) {
          var deleteInput = row.querySelector('input[name^="delete_"]')
          if (deleteInput) {
            deleteInput.value = "1"
          }
          // Hide the row if it has an existing communication id
          row.style.display = "none"
        } else {
          // Remove the row if it is newly added
          row.remove()
        }
      }
    })
  }
  if (widgetElement.querySelector('#memberCommunicationForm')) {
    // Validate communication rows on form submission
    widgetElement.querySelector('#memberCommunicationForm').addEventListener('submit', function(e) {
      var errors = []
      for (var i = 1; i <= rowCounter; i++) {
        var deleteInput = widgetElement.querySelector('input[name="delete_' + i + '"]')
        if (deleteInput && deleteInput.value === "1") continue
        var channelElem = widgetElement.querySelector('select[name="channel_' + i + '"]')
        var identElem = widgetElement.querySelector('input[name="identification_' + i + '"]')
        if (channelElem && identElem) {
          var channel = channelElem.value.trim()
          var ident = identElem.value.trim()
          if (!channel || !ident) {
            errors.push("Row " + i + ": Channel and Identification are mandatory.")
            continue
          }
          if (channel === "1") {
            var emailRegex = /^[\w\.-]+@[\w\.-]+\.\w+$/
            if (!emailRegex.test(ident)) {
              errors.push("Row " + i + ": Invalid email address.")
            }
          }
          if (channel === "2") {
            var phoneRegex = /^\+?\d{7,15}$/
            if (!phoneRegex.test(ident)) {
              errors.push("Row " + i + ": Invalid phone number.")
            }
          }
        }
      }
      if (errors.length > 0) {
        e.preventDefault()
        alert(errors.join("\n"))
      }
    })
  }
  // Bind cancel button event to remove widget
  var cancelButton = widgetElement.querySelector('#cancelCommunication')
  if (cancelButton) {
    cancelButton.addEventListener('click', function() {
      widgetElement.remove()
    })
  }
}
