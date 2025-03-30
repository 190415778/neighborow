/**
 * widget_loaned_items.js
 *
 * This module manages the "My Loaned Items" widget.
 * It supports paging via Previous/Next buttons, item return,
 * and condition log functionality. 
 **/

// Utility function to get a cookie value
function getCookie(name) {
  let cookieValue = null
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";")
    for (let cookie of cookies) {
      cookie = cookie.trim()
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

/**
* Displays a custom confirmation modal
*/
function showCustomConfirm(message, onConfirm) {
  const confirmHtml = `
    <div class="modal fade" id="confirmPopupModal" tabindex="-1" aria-labelledby="confirmPopupModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="confirmPopupModalLabel">Confirmation</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            ${message}
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" id="confirmCancel">Cancel</button>
            <button type="button" class="btn btn-danger" id="confirmOk">Confirm</button>
          </div>
        </div>
      </div>
    </div>
  `
  // Inject the confirmation modal HTML into the document body
  document.body.insertAdjacentHTML('beforeend', confirmHtml)
  const confirmModalEl = document.getElementById('confirmPopupModal')
  const confirmModal = new bootstrap.Modal(confirmModalEl)
  confirmModal.show()
  // Bind cancel button event to hide and remove modal
  confirmModalEl.querySelector('#confirmCancel').addEventListener('click', function() {
    confirmModal.hide()
    confirmModalEl.addEventListener('hidden.bs.modal', function () {
      confirmModal.dispose()
      confirmModalEl.remove()
    }, { once: true })
  })
  // Bind confirm button event to execute callback and remove modal
  confirmModalEl.querySelector('#confirmOk').addEventListener('click', function() {
    onConfirm()
    confirmModal.hide()
    confirmModalEl.addEventListener('hidden.bs.modal', function () {
      confirmModal.dispose()
      confirmModalEl.remove()
    }, { once: true })
  })
}

/**
* Initializes the Loaned Items widget by loading its HTML and binding events
*/
export function initWidgetLoanedItems(appendWidget, bringWidgetToFront, getCookie, showPopupModal) {
  fetch("loaned_items/")
    .then(response => response.text())
    .then(html => {
      const widgetElement = appendWidget(html)
      if (!widgetElement) return
      widgetElement.dataset.currentPage = "1"

      // Bind "Show history" checkbox change event using its unique ID
      const showHistoryCheckbox = widgetElement.querySelector("#loaned_items_showHistory")
      if (showHistoryCheckbox) {
        showHistoryCheckbox.addEventListener("change", function() {
          widgetElement.dataset.currentPage = "1"
          loadPage(widgetElement, 1, showPopupModal)
        })
      }

      // Bind close, paging and action buttons, and condition log save listener
      bindCloseButtons(widgetElement)
      attachPagingButtons(widgetElement, showPopupModal)
      bindActionButtons(widgetElement, showPopupModal)
      attachConditionLogSaveListener(showPopupModal)
      updatePagingButtons(widgetElement, false)
      // Bring widget to front if function is provided
      if (typeof bringWidgetToFront === "function") {
        bringWidgetToFront(widgetElement)
      }
    })
    .catch(error => console.error("Error loading widget_loaned_items:", error))
}

/**
* Restores an existing Loaned Items widget by re-binding events
*/
export function initRestoredWidget(widgetElement, bringWidgetToFront, showPopupModal) {
  const showHistoryCheckbox = widgetElement.querySelector("#loaned_items_showHistory")
  if (showHistoryCheckbox) {
    showHistoryCheckbox.addEventListener("change", function() {
      widgetElement.dataset.currentPage = "1"
      loadPage(widgetElement, 1, showPopupModal)
    })
  }
  bindCloseButtons(widgetElement)
  attachPagingButtons(widgetElement, showPopupModal)
  bindActionButtons(widgetElement, showPopupModal)
  attachConditionLogSaveListener(showPopupModal)
  if (typeof bringWidgetToFront === "function") {
    bringWidgetToFront(widgetElement)
  }
}

// Bind close button events to remove the widget
function bindCloseButtons(widgetElement) {
  widgetElement.querySelectorAll("#closeWidgetLoanedItems").forEach(btn => {
    btn.addEventListener("click", function(e) {
      e.preventDefault()
      widgetElement.remove()
    })
  })
}

// Attach paging button events for navigating between pages
function attachPagingButtons(widgetElement, showPopupModal) {
  const prevBtn = widgetElement.querySelector("#prevPage")
  const nextBtn = widgetElement.querySelector("#nextPage")
  if (prevBtn) {
    prevBtn.addEventListener("click", function(e) {
      e.preventDefault()
      let current = parseInt(widgetElement.dataset.currentPage, 10) || 1
      if (current > 1) {
        loadPage(widgetElement, current - 1, showPopupModal)
      }
    })
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", function(e) {
      e.preventDefault()
      let current = parseInt(widgetElement.dataset.currentPage, 10) || 1
      loadPage(widgetElement, current + 1, showPopupModal)
    })
  }
}

// Load a specific page of loaned items based on current settings
function loadPage(widgetElement, page, showPopupModal) {
  const showHistory = widgetElement.querySelector("#loaned_items_showHistory")?.checked ? "on" : "off"
  const url = `loaned_items/?page=${page}&show_history=${showHistory}`
  fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
    .then(response => response.json())
    .then(data => {
      const tbody = widgetElement.querySelector("#loanedItemsTable tbody")
      if (tbody) { tbody.innerHTML = data.html }
      widgetElement.dataset.currentPage = String(page)
      updatePagingButtons(widgetElement, data.has_next)
      bindActionButtons(widgetElement, showPopupModal)
      attachTooltips(widgetElement)
      const header = widgetElement.querySelector("h2")
      if (header && data.total_count !== undefined) {
        header.innerText = `My ${data.total_count} loaned items`
      }
    })
    .catch(error => console.error("Error loading page " + page + ":", error))
}

// Update the disabled state of paging buttons based on current page
function updatePagingButtons(widgetElement, hasNext) {
  const currentPage = parseInt(widgetElement.dataset.currentPage, 10) || 1
  const prevBtn = widgetElement.querySelector("#prevPage")
  const nextBtn = widgetElement.querySelector("#nextPage")
  if (prevBtn) { prevBtn.disabled = currentPage <= 1 }
  if (nextBtn) { nextBtn.disabled = !hasNext }
}

// Attach tooltips to all elements with the tooltip attribute
function attachTooltips(widgetElement) {
  const tooltipEls = [].slice.call(widgetElement.querySelectorAll('[data-bs-toggle="tooltip"]'))
  tooltipEls.forEach(el => new bootstrap.Tooltip(el))
}

// Bind action buttons for marking items as returned and opening condition logs
function bindActionButtons(widgetElement, showPopupModal) {
  // Bind "Mark as Returned" button
  widgetElement.querySelectorAll(".return-button").forEach(function(button) {
    if (button.dataset.eventBound === "true") return
    button.dataset.eventBound = "true"
    if (button.disabled) return
    button.addEventListener("click", function(e) {
      e.preventDefault()
      const row = button.closest("tr")
      const transactionId = row.getAttribute("data-transaction-id")
      const label = row.getAttribute("data-label")
      const borrowerNickname = row.getAttribute("data-borrower-nickname")
      const borrowerFlat = row.getAttribute("data-borrower-flat")
      const confirmationMessage = `Do you want to mark item ${label} as returned by borrower ${borrowerNickname} (${borrowerFlat})?`
      showCustomConfirm(confirmationMessage, function() {
        fetch(`return_item_loaned/${transactionId}/`, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken")
          }
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              let current = parseInt(widgetElement.dataset.currentPage, 10) || 1
              loadPage(widgetElement, current, showPopupModal)
            }
            if (data.html) { showPopupModal(data.html) }
          })
          .catch(error => {
            console.error("Error marking as returned:", error)
            showPopupModal("<div class='modal-body'>An unexpected error occurred.</div>")
          })
      })
    })
  })

  // Bind Condition Log buttons to open condition log modal
  widgetElement.querySelectorAll(".condition-log-button").forEach(function(button) {
    if (button.dataset.eventBound === "true") return
    button.dataset.eventBound = "true"
    button.addEventListener("click", function(e) {
      e.preventDefault()
      const row = button.closest("tr")
      const transactionId = row.getAttribute("data-transaction-id")
      const modalEl = document.getElementById("loaned_items_conditionLogModal")
      if (!modalEl) {
        console.error("Condition Log Modal not found.")
        return
      }
      document.getElementById("loaned_items_conditionLogTransactionId").value = transactionId
      ["before", "after"].forEach(logType => {
        fetch(`condition_log/${transactionId}/?log_type=${logType}`, {
          headers: { "X-Requested-With": "XMLHttpRequest" }
        })
          .then(response => response.json())
          .then(data => {
            const labelEl = document.getElementById(`loaned_items_${logType}Label`)
            const descEl = document.getElementById(`loaned_items_${logType}Description`)
            const previewEl = document.getElementById(`loaned_items_${logType}ImagesPreview`)
            if (data.success && data.data) {
              labelEl.value = data.data.label || ""
              descEl.value = data.data.description || ""
              updateImagesPreview(previewEl, data.data.images)
              const metaEl = document.getElementById(`loaned_items_conditionLogMeta${(logType === "before" ? "Before" : "After")}`)
              if (metaEl) {
                metaEl.innerText = `Created: ${data.data.created} by ${data.data.created_by} | Last Modified: ${data.data.modified} by ${data.data.modified_by}`
              }
            } else {
              labelEl.value = ""
              descEl.value = ""
              previewEl.innerHTML = ""
              const metaEl = document.getElementById(`loaned_items_conditionLogMeta${(logType === "before" ? "Before" : "After")}`)
              if (metaEl) { metaEl.innerText = "" }
            }
          })
          .catch(error => console.error(`Error loading ${logType}-condition log:`, error))
      })
      // Reset condition log forms before showing modal
      document.getElementById("loaned_items_conditionLogFormBefore").reset()
      document.getElementById("loaned_items_conditionLogFormAfter").reset()
      new bootstrap.Modal(modalEl).show()
    })
  })
}

// Attach a listener to the save button for the condition log
function attachConditionLogSaveListener(showPopupModal) {
  const saveBtn = document.getElementById("loaned_items_saveConditionLog")
  if (saveBtn && saveBtn.dataset.listenerAttached !== "true") {
    saveBtn.dataset.listenerAttached = "true"
    saveBtn.addEventListener("click", function() {
      const activeTab = document.querySelector("#loaned_items_conditionLogTabContent .tab-pane.active")
      let form = null
      if (activeTab.id === "loaned_items_beforeLog") {
        form = document.getElementById("loaned_items_conditionLogFormBefore")
      } else if (activeTab.id === "loaned_items_afterLog") {
        form = document.getElementById("loaned_items_conditionLogFormAfter")
      } else {
        console.error("No active tab found in Condition Log Modal.")
        return
      }
      const transactionId = document.getElementById("loaned_items_conditionLogTransactionId").value
      const url = `condition_log/${transactionId}/`
      const formData = new FormData(form)
      fetch(url, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCookie("csrftoken")
        },
        body: formData
      })
        .then(response => response.json())
        .then(data => {
          const modal = bootstrap.Modal.getInstance(document.getElementById("loaned_items_conditionLogModal"))
          if (data.success) { modal.hide() }
          if (data.html) { showPopupModal(data.html) }
        })
        .catch(error => {
          console.error("Error saving condition log:", error)
          showPopupModal("<div class='modal-body'>An unexpected error occurred.</div>")
        })
    })
  }
}

// Update the images preview in the condition log modal with the provided images
function updateImagesPreview(container, images) {
  container.innerHTML = ""
  if (images && images.length > 0) {
    images.forEach(image => {
      const imgEl = document.createElement("img")
      imgEl.src = image.url
      imgEl.alt = image.caption || ""
      imgEl.style.width = "100px"
      imgEl.style.marginRight = "5px"
      imgEl.style.cursor = "pointer"
      // Bind click event to open the image in a modal with details
      imgEl.addEventListener("click", function() {
        const modalImage = document.getElementById("loaned_items_conditionModalImage")
        if (modalImage) { modalImage.src = image.url }
        const modalTitle = document.getElementById("loaned_items_conditionImageModalLabel")
        if (modalTitle) { modalTitle.textContent = (image.caption && image.caption.trim() !== "") ? image.caption : "Image Details" }
        const metaContainer = document.getElementById("loaned_items_conditionModalMeta")
        if (metaContainer) { metaContainer.innerText = `Created: ${image.created} by ${image.created_by} | Last Modified: ${image.modified} by ${image.modified_by}` }
        const modalEl = document.getElementById("loaned_items_conditionImageModal")
        if (modalEl) { new bootstrap.Modal(modalEl).show() }
      })
      container.appendChild(imgEl)
    })
  } else {
    // Show fallback text if no images are available
    container.textContent = "No images available."
  }
}
