/**
 * widget_borrowed_items.js
 *
 * This module manages the "My Borrowed Items" widget.
 * It supports paging via Previous/Next buttons, item return,
 * and condition log functionality.
 */

// Get cookie by name
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Displays a custom confirmation modal with the given message.
 * Calls onConfirm() if the user confirms.
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
  `;
  // Insert confirmation modal HTML into the document body
  document.body.insertAdjacentHTML('beforeend', confirmHtml);
  const confirmModalEl = document.getElementById('confirmPopupModal');
  const confirmModal = new bootstrap.Modal(confirmModalEl);
  confirmModal.show();
  // Bind Cancel button to hide and remove the modal
  confirmModalEl.querySelector('#confirmCancel').addEventListener('click', function() {
    confirmModal.hide();
    confirmModalEl.addEventListener('hidden.bs.modal', function () {
      confirmModal.dispose();
      confirmModalEl.remove();
    }, { once: true });
  });
  // Bind Confirm button to execute callback, then hide and remove the modal
  confirmModalEl.querySelector('#confirmOk').addEventListener('click', function() {
    onConfirm();
    confirmModal.hide();
    confirmModalEl.addEventListener('hidden.bs.modal', function () {
      confirmModal.dispose();
      confirmModalEl.remove();
    }, { once: true });
  });
}

/**
 * Initializes the Borrowed Items widget for the first time.
 */
export function initWidgetBorrowedItems(appendWidget, bringWidgetToFront, getCookie, showPopupModal) {
  fetch("borrowed_items/")
    .then(response => response.text())
    .then(html => {
      const widgetElement = appendWidget(html);
      if (!widgetElement) return;

      // Set current page to 1
      widgetElement.dataset.currentPage = "1";

      // Bind "Show history" checkbox to reload page 1 on change
      const showHistoryCheckbox = widgetElement.querySelector("#showHistory");
      if (showHistoryCheckbox) {
        showHistoryCheckbox.addEventListener("change", function() {
          widgetElement.dataset.currentPage = "1";
          loadPage(widgetElement, 1, showPopupModal);
        });
      }

      // Bind Close buttons to remove the widget
      bindCloseButtons(widgetElement);

      // Bind paging (Previous/Next) buttons to navigate pages
      attachPagingButtons(widgetElement, showPopupModal);

      // Bind action buttons (Return and Condition Log) for item actions
      bindActionButtons(widgetElement, showPopupModal);

      // Bind Condition Log Save listener for log updates
      attachConditionLogSaveListener(showPopupModal);

      // Update paging buttons (disable previous on page 1)
      updatePagingButtons(widgetElement, false);

      // Bring widget to the front if function provided
      if (typeof bringWidgetToFront === "function") {
        bringWidgetToFront(widgetElement);
      }
    })
    .catch(error => console.error("Error loading widget_borrowed_items:", error));
}

/**
 * Restores an existing Borrowed Items widget.
 */
export function initRestoredWidget(widgetElement, bringWidgetToFront, showPopupModal) {

  // Bind "Show history" checkbox change event after widget restoration
  const showHistoryCheckbox = widgetElement.querySelector("#showHistory");
  if (showHistoryCheckbox) {
    showHistoryCheckbox.addEventListener("change", function() {
      widgetElement.dataset.currentPage = "1";
      loadPage(widgetElement, 1, showPopupModal);
    });
  }

  // Re-bind all required events for the restored widget
  bindCloseButtons(widgetElement);
  attachPagingButtons(widgetElement, showPopupModal);
  bindActionButtons(widgetElement, showPopupModal);
  attachConditionLogSaveListener(showPopupModal);

  // Bring restored widget to the front if function provided
  if (typeof bringWidgetToFront === "function") {
    bringWidgetToFront(widgetElement);
  }
}

// ========== Helper Functions ==========

// Bind close buttons to remove the widget
function bindCloseButtons(widgetElement) {
  widgetElement.querySelectorAll("#closeWidgetBorrowedItems").forEach(btn => {
    btn.addEventListener("click", function(e) {
      e.preventDefault();
      widgetElement.remove();
    });
  });
}

// Attach paging buttons for Previous and Next navigation
function attachPagingButtons(widgetElement, showPopupModal) {
  const prevBtn = widgetElement.querySelector("#prevPage");
  const nextBtn = widgetElement.querySelector("#nextPage");
  if (prevBtn) {
    prevBtn.addEventListener("click", function(e) {
      e.preventDefault();
      let current = parseInt(widgetElement.dataset.currentPage, 10) || 1;
      if (current > 1) {
        loadPage(widgetElement, current - 1, showPopupModal);
      }
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", function(e) {
      e.preventDefault();
      let current = parseInt(widgetElement.dataset.currentPage, 10) || 1;
      loadPage(widgetElement, current + 1, showPopupModal);
    });
  }
}

// Load a specific page of borrowed items via AJAX
function loadPage(widgetElement, page, showPopupModal) {
  const showHistory = widgetElement.querySelector("#showHistory")?.checked ? "on" : "off";
  const url = `borrowed_items/?page=${page}&show_history=${showHistory}`;
  fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
    .then(response => response.json())
    .then(data => {
      const tbody = widgetElement.querySelector("#borrowedItemsTable tbody");
      if (tbody) {
        tbody.innerHTML = data.html;
      }
      widgetElement.dataset.currentPage = String(page);
      updatePagingButtons(widgetElement, data.has_next);
      bindActionButtons(widgetElement, showPopupModal);
      attachTooltips(widgetElement);
      const header = widgetElement.querySelector("h2");
      if (header && data.total_count !== undefined) {
        header.innerText = `My ${data.total_count} borrowed items`;
      }
    })
    .catch(error => console.error("Error loading page " + page + ":", error));
}

// Update paging button states based on current page and next page availability
function updatePagingButtons(widgetElement, hasNext) {
  const currentPage = parseInt(widgetElement.dataset.currentPage, 10) || 1;
  const prevBtn = widgetElement.querySelector("#prevPage");
  const nextBtn = widgetElement.querySelector("#nextPage");
  if (prevBtn) { prevBtn.disabled = currentPage <= 1; }
  if (nextBtn) { nextBtn.disabled = !hasNext; }
}

// Attach tooltips to elements with tooltip attributes
function attachTooltips(widgetElement) {
  const tooltipEls = [].slice.call(widgetElement.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));
}

// Bind action buttons for returning items and opening condition log modal
function bindActionButtons(widgetElement, showPopupModal) {
  // Bind Return buttons with custom confirmation modal
  widgetElement.querySelectorAll(".return-button").forEach(function(button) {
    if (button.dataset.eventBound === "true") return;
    button.dataset.eventBound = "true";
    if (button.disabled) return;
    button.addEventListener("click", function(e) {
      e.preventDefault();
      const row = button.closest("tr");
      const transactionId = row.getAttribute("data-transaction-id");
      const label = row.getAttribute("data-label");
      const lenderNickname = row.getAttribute("data-lender-nickname");
      const lenderFlat = row.getAttribute("data-lender-flat");
      let confirmationMessage = `Do you want to return item ${label} to lender ${lenderNickname} (${lenderFlat})?`;
      // Use custom confirmation modal to confirm item return
      showCustomConfirm(confirmationMessage, function() {
        fetch(`return_item/${transactionId}/`, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken")
          }
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              let current = parseInt(widgetElement.dataset.currentPage, 10) || 1;
              loadPage(widgetElement, current, showPopupModal);
            }
            if (data.html) { showPopupModal(data.html); }
          })
          .catch(error => {
            console.error("Error returning item:", error);
            showPopupModal("<div class='modal-body'>An unexpected error occurred.</div>");
          });
      });
    });
  });

  // Bind Condition Log buttons to load and display log details
  widgetElement.querySelectorAll(".condition-log-button").forEach(function(button) {
    if (button.dataset.eventBound === "true") return;
    button.dataset.eventBound = "true";
    button.addEventListener("click", function(e) {
      e.preventDefault();
      const row = button.closest("tr");
      const transactionId = row.getAttribute("data-transaction-id");
      const modalEl = document.getElementById("conditionLogModal");
      if (!modalEl) {
        console.error("Condition Log Modal not found.");
        return;
      }
      // Set the transaction ID in the condition log modal
      document.getElementById("conditionLogTransactionId").value = transactionId;
      // Load both "before" and "after" condition logs
      ["before", "after"].forEach(logType => {
        fetch(`condition_log/${transactionId}/?log_type=${logType}`, {
          headers: { "X-Requested-With": "XMLHttpRequest" }
        })
          .then(response => response.json())
          .then(data => {
            const labelEl = document.getElementById(`${logType}Label`);
            const descEl = document.getElementById(`${logType}Description`);
            const previewEl = document.getElementById(`${logType}ImagesPreview`);
            if (data.success && data.data) {
              labelEl.value = data.data.label || "";
              descEl.value = data.data.description || "";
              updateImagesPreview(previewEl, data.data.images);
              // Update meta info for the condition log tab
              const metaEl = document.getElementById(`conditionLogMeta${(logType === "before" ? "Before" : "After")}`);
              if (metaEl) {
                metaEl.innerText = `Created: ${data.data.created} by ${data.data.created_by} | Last Modified: ${data.data.modified} by ${data.data.modified_by}`;
              }
            } else {
              labelEl.value = "";
              descEl.value = "";
              previewEl.innerHTML = "";
              const metaEl = document.getElementById(`conditionLogMeta${(logType === "before" ? "Before" : "After")}`);
              if (metaEl) {
                metaEl.innerText = "";
              }
            }
          })
          .catch(error => console.error(`Error loading ${logType}-condition log:`, error));
      });
      // Reset condition log forms before showing modal
      document.getElementById("conditionLogFormBefore").reset();
      document.getElementById("conditionLogFormAfter").reset();
      new bootstrap.Modal(modalEl).show();
    });
  });
}

// Attach Condition Log Save listener for saving log details
function attachConditionLogSaveListener(showPopupModal) {
  const saveBtn = document.getElementById("saveConditionLog");
  if (saveBtn && saveBtn.dataset.listenerAttached !== "true") {
    saveBtn.dataset.listenerAttached = "true";
    saveBtn.addEventListener("click", function() {
      const activeTab = document.querySelector("#conditionLogTabContent .tab-pane.active");
      let form = null;
      if (activeTab.id === "beforeLog") {
        form = document.getElementById("conditionLogFormBefore");
      } else if (activeTab.id === "afterLog") {
        form = document.getElementById("conditionLogFormAfter");
      } else {
        console.error("No active tab found in Condition Log Modal.");
        return;
      }
      const transactionId = document.getElementById("conditionLogTransactionId").value;
      const url = `condition_log/${transactionId}/`;
      const formData = new FormData(form);
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
          const modal = bootstrap.Modal.getInstance(document.getElementById("conditionLogModal"));
          if (data.success) {
            modal.hide();
          }
          if (data.html) { showPopupModal(data.html); }
        })
        .catch(error => {
          console.error("Error saving condition log:", error);
          showPopupModal("<div class='modal-body'>An unexpected error occurred.</div>");
        });
    });
  }
}

// Updated binding for updateImagesPreview to include meta info update for condition images
function updateImagesPreview(container, images) {
  container.innerHTML = "";
  if (images && images.length > 0) {
    images.forEach(image => {
      const imgEl = document.createElement("img");
      imgEl.src = image.url;
      imgEl.alt = image.caption || "";
      imgEl.style.width = "100px";
      imgEl.style.marginRight = "5px";
      imgEl.style.cursor = "pointer";
      // Add click event to open the condition image preview modal
      imgEl.addEventListener("click", function() {
        // Set the modal image source
        const modalImage = document.getElementById("conditionModalImage");
        if (modalImage) {
          modalImage.src = image.url;
        }
        // Update the modal title based on the image caption
        const modalTitle = document.getElementById("conditionImageModalLabel");
        if (modalTitle) {
          modalTitle.textContent = (image.caption && image.caption.trim() !== "") ? image.caption : "Image Details";
        }
        // Update the meta info in the modal with created/modified data
        const metaContainer = document.getElementById("conditionModalMeta");
        if (metaContainer) {
          metaContainer.innerText = `Created: ${image.created} by ${image.created_by} | Last Modified: ${image.modified} by ${image.modified_by}`;
        }
        // Show the condition image modal
        const modalEl = document.getElementById("conditionImageModal");
        if (modalEl) {
          new bootstrap.Modal(modalEl).show();
        }
      });
      container.appendChild(imgEl);
    });
  } else {
    // Fallback text if no images available
    container.textContent = "No images available.";
  }
}
