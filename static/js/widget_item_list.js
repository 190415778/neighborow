/**
 * widget_item_list.js
 *
 * This module manages the "Items available for Loan" widget
 * It exports two functions:
 *   - initWidgetItemList: For initial widget loading
 *   - initRestoredWidget: For reinitializing a restored widget
 */


/**
 * Helper function to read a cookie by name
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      let cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Helper function to safely set the inner text of an element
 */
function setInnerTextSafe(parent, selector, value) {
  const elem = parent.querySelector(selector);
  if (elem) {
    elem.innerText = value;
  } else {
    console.error("Element " + selector + " not found in modal.");
  }
}

/**
 * Helper function to clear button text and set fixed dimensions
 */
function fixButtonAppearance(button) {
  while (button.firstChild) {
    button.removeChild(button.firstChild);
  }
  button.style.width = "32px";
  button.style.height = "32px";
}

/**
 * Binds click events for all send-message buttons
 */
function bindSendMessageButtons(widgetElement, bringWidgetToFront) {
  widgetElement.querySelectorAll(".send-message-button").forEach(function(button) {
    if (button.dataset.eventBound === "true") return;
    button.dataset.eventBound = "true";
    button.addEventListener("click", function(e) {
      e.preventDefault();
      const row = e.target.closest("tr");
      if (row) {
        const itemId = row.getAttribute("data-item-id");
        const recipientMemberId = row.getAttribute("data-member-id");
        const label = row.getAttribute("data-label");
        let subjectText = "Borrowing request for " + itemId + " " + label;
        if (subjectText.length > 150) {
          subjectText = subjectText.substring(0, 150);
        }
        const senderId = row.getAttribute("data-sender-id");
        const senderNickname = row.getAttribute("data-sender-nickname");
        const senderFlat = row.getAttribute("data-sender-flat");
        const modalId = "replyModal_ItemList";
        const modalEl = document.getElementById(modalId);
        if (!modalEl) {
          console.error("Modal with ID " + modalId + " not found in the DOM.");
          return;
        }
        setInnerTextSafe(modalEl, "#replyTitleDisplay_" + modalId, subjectText);
        const replyReceiverInput = modalEl.querySelector("#replyReceiverId_" + modalId);
        if (replyReceiverInput) replyReceiverInput.value = recipientMemberId;
        const replySenderInput = modalEl.querySelector("#replySenderId_" + modalId);
        if (replySenderInput) replySenderInput.value = senderId;
        setInnerTextSafe(modalEl, "#replySenderNicknameDisplay_" + modalId, senderNickname);
        setInnerTextSafe(modalEl, "#replySenderFlatDisplay_" + modalId, senderFlat);
        const replyText = modalEl.querySelector("#replyText_" + modalId);
        if (replyText) replyText.value = "";
        const modalInstance = new bootstrap.Modal(modalEl);
        modalInstance.show();
        const sendReplyButton = modalEl.querySelector("#sendReply_" + modalId);
        if (sendReplyButton) {
          sendReplyButton.onclick = () => {
            const form = modalEl.querySelector("#replyForm_" + modalId);
            const formData = new FormData(form);
            fetch("send_reply/", {
              method: "POST",
              headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken")
              },
              body: formData
            })
              .then(response => response.json())
              .then(data => {
                if (data.success) {
                  modalInstance.hide();
                } else {
                  console.error("Error sending reply:", data.error);
                }
              })
              .catch(error => console.error("Error sending reply:", error));
          };
        } else {
          console.error("Send Reply button not found in modal with ID " + modalId);
        }
        modalEl.addEventListener("hidden.bs.modal", () => {
          bringWidgetToFront(widgetElement);
        }, { once: true });
      }
    });
  });
}

/**
 * Global variable to hold the current item images and index
 */
var itemImageModal = null;

/**
 * Binds click events to all images with class "item-image"
 */
function bindItemImageClick(widgetElement) {
  widgetElement.querySelectorAll("img.item-image").forEach(function(img) {
    if (img.dataset.imageClickBound === "true") return;
    img.dataset.imageClickBound = "true";
    img.addEventListener("click", function() {
      var itemId = img.getAttribute("data-item-id");
      fetch("item_images/" + itemId + "/")
        .then(response => response.json())
        .then(data => {
          var images = data.images;
          if (!images || images.length === 0) {
            images = [{ url: img.src, caption: img.alt }];
          }
          window.currentItemImages = images;
          window.currentImageIndex = 0;
          window.currentItemLabel = data.label || "";
          window.currentItemDescription = data.description || "";
          showImageModal();
        })
        .catch(error => console.error("Error fetching images:", error));
    });
  });
}

/**
 * Binds next and previous button events in the modal
 */
function bindModalNavigation(widgetElement) {
  var modalEl = document.getElementById("imageModal");
  if (!modalEl) return;
  var nextBtn = modalEl.querySelector("#nextImage");
  var prevBtn = modalEl.querySelector("#prevImage");
  if (nextBtn && nextBtn.dataset.eventBound !== "true") {
    nextBtn.dataset.eventBound = "true";
    nextBtn.addEventListener("click", function() {
      if (window.currentItemImages && window.currentItemImages.length > 0) {
        window.currentImageIndex = (window.currentImageIndex + 1) % window.currentItemImages.length;
        showImageModal();
      }
    });
  }
  if (prevBtn && prevBtn.dataset.eventBound !== "true") {
    prevBtn.dataset.eventBound = "true";
    prevBtn.addEventListener("click", function() {
      if (window.currentItemImages && window.currentItemImages.length > 0) {
        window.currentImageIndex = (window.currentImageIndex - 1 + window.currentItemImages.length) % window.currentItemImages.length;
        showImageModal();
      }
    });
  }
}

/**
 * Updates the modal content (image, caption, label and description) and show the modal
 */
function showImageModal() {
  var modalEl = document.getElementById("imageModal");
  var modalImage = document.getElementById("modalImage");
  var modalCaption = document.getElementById("modalCaption");
  var modalLabel = document.getElementById("modalLabel");
  var modalDescription = document.getElementById("modalDescription");

  if (window.currentItemImages && window.currentItemImages.length > 0) {
    var currentData = window.currentItemImages[window.currentImageIndex];
    modalImage.src = currentData.url;
    modalImage.alt = currentData.caption;
    modalCaption.textContent = currentData.caption;
  }
  if (modalLabel) {
    modalLabel.textContent = window.currentItemLabel || "";
  }
  if (modalDescription) {
    modalDescription.textContent = window.currentItemDescription || "";
  }
  var modalInstance = bootstrap.Modal.getInstance(modalEl);
  if (!modalInstance) {
    modalInstance = new bootstrap.Modal(modalEl);
  }
  modalInstance.show();
}

/**
 * Initializes the Item List Widget
 */
export function initWidgetItemList(appendWidget, bringWidgetToFront) {
  fetch("item_list/")
    .then(response => response.text())
    .then(html => {
      const widgetElement = appendWidget(html);

      const closeButton = widgetElement.querySelector("#closeWidgetItemList");
      if (closeButton) {
        closeButton.addEventListener("click", function(e) {
          e.preventDefault();
          widgetElement.remove();
        });
      }
      const secondaryCloseButton = widgetElement.querySelector("#closeItemListWidget");
      if (secondaryCloseButton) {
        secondaryCloseButton.addEventListener("click", function(e) {
          e.preventDefault();
          widgetElement.remove();
        });
      }

      const searchButton = widgetElement.querySelector("#itemSearchButton");
      if (searchButton) {
        searchButton.addEventListener("click", function(e) {
          e.preventDefault();
          const searchInput = widgetElement.querySelector("#itemSearchInput").value;
          fetch("item_list/?q=" + encodeURIComponent(searchInput))
            .then(response => response.json())
            .then(data => {
              const tbody = widgetElement.querySelector("#itemListTable tbody");
              if (tbody) {
                tbody.innerHTML = data.html;
                tbody.querySelectorAll(".borrow-button").forEach(function(button) {
                  button.setAttribute("data-bs-toggle", "tooltip");
                  button.setAttribute("data-bs-container", "body");
                  button.setAttribute("title", "Borrow");
                  fixButtonAppearance(button);
                });
                tbody.querySelectorAll(".send-message-button").forEach(function(button) {
                  button.setAttribute("data-bs-toggle", "tooltip");
                  button.setAttribute("data-bs-container", "body");
                  button.setAttribute("title", "Send Message");
                  fixButtonAppearance(button);
                });
                const tooltipTriggerList = [].slice.call(tbody.querySelectorAll('[data-bs-toggle="tooltip"]'));
                tooltipTriggerList.forEach(function(tooltipTriggerEl) {
                  new bootstrap.Tooltip(tooltipTriggerEl);
                });
                //  Also bind the Borrow-Buttons
                bindBorrowButtons(widgetElement, bringWidgetToFront);
                // Also bind the Next/Previous Buttons in the Modal
                bindModalNavigation(widgetElement);
              }
              const container = widgetElement.querySelector("#itemListTableContainer");
              if (container) {
                container.dataset.hasNext = data.has_next ? "true" : "false";
                container.dataset.nextPage = data.next_page;
              }
            })
            .catch(error => console.error("Error searching items:", error));
        });
      }

      // Bind the Borrow-Buttons initially
      bindBorrowButtons(widgetElement, bringWidgetToFront);
      bindSendMessageButtons(widgetElement, bringWidgetToFront);
      bindItemImageClick(widgetElement);
      bindModalNavigation(widgetElement);

      const tooltipTriggerList = [].slice.call(widgetElement.querySelectorAll('[data-bs-toggle="tooltip"]'));
      tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
      });

      const container = widgetElement.querySelector("#itemListTableContainer");
      if (container) {
        // Scroll event listener for loading more items when reaching the bottom
        container.addEventListener("scroll", function() {
          console.log("Scroll event triggered in Item Manager.");
          console.log("scrollTop:", container.scrollTop, "clientHeight:", container.clientHeight, "scrollHeight:", container.scrollHeight);

          if (container.scrollTop + container.clientHeight >= container.scrollHeight - 25) {
            if (container.dataset.loading !== "true" && container.dataset.hasNext === "true") {
              container.dataset.loading = "true";
              const nextPage = container.dataset.nextPage || 2;
              const searchInputValue = widgetElement.querySelector("#itemSearchInput").value;
              let url = "item_list/?page=" + nextPage;
              if (searchInputValue) {
                url += "&q=" + encodeURIComponent(searchInputValue);
              }
              fetch(url)
                .then(response => response.json())
                .then(data => {
                  const tbody = widgetElement.querySelector("#itemListTable tbody");
                  tbody.insertAdjacentHTML('beforeend', data.html);
                  
                  // Reinitialize tooltips and rebind events on new rows:
                  tbody.querySelectorAll(".borrow-button").forEach(function(button) {
                    button.setAttribute("data-bs-toggle", "tooltip");
                    button.setAttribute("data-bs-container", "body");
                    button.setAttribute("title", "Borrow");

                    fixButtonAppearance(button);
                  });
                  tbody.querySelectorAll(".send-message-button").forEach(function(button) {
                    button.setAttribute("data-bs-toggle", "tooltip");
                    button.setAttribute("data-bs-container", "body");
                    button.setAttribute("title", "Send Message");

                    fixButtonAppearance(button);
                  });
                  const newTooltips = [].slice.call(tbody.querySelectorAll('[data-bs-toggle="tooltip"]'));
                  newTooltips.forEach(function(el) {
                    new bootstrap.Tooltip(el);
                  });
                  // Bind borrow, send-message, image click and modal navigation events for new rows.
                  bindBorrowButtons(widgetElement, bringWidgetToFront);
                  bindSendMessageButtons(widgetElement, bringWidgetToFront);
                  bindItemImageClick(widgetElement);
                  bindModalNavigation(widgetElement);
                  container.dataset.hasNext = data.has_next ? "true" : "false";
                  container.dataset.nextPage = data.next_page;
                  container.dataset.loading = "false";
                })
                .catch(error => {
                  console.error("Error loading next page:", error);
                  container.dataset.loading = "false";
                });
            }
          }
        });
      }
    })
    .catch(error => console.error("Error loading widget_item_list:", error));
}

/**
 * Reinitializes a restored Item List Widget
 */
export function initRestoredWidget(widgetElement, bringWidgetToFront) {
  // Bind the widget's close button
  const closeButton = widgetElement.querySelector("#closeWidgetItemList");
  if (closeButton) {
    closeButton.addEventListener("click", function(e) {
      e.preventDefault();
      widgetElement.remove();
    });
  }

  // Bind the search button to perform the search via JSON
  const searchButton = widgetElement.querySelector("#itemSearchButton");
  if (searchButton) {
    searchButton.addEventListener("click", function(e) {
      e.preventDefault();
      const searchInput = widgetElement.querySelector("#itemSearchInput").value;
      fetch("item_list_search/?q=" + encodeURIComponent(searchInput))
        .then(response => response.json())
        .then(data => {
          const tbody = widgetElement.querySelector("#itemListTable tbody");
          if (tbody) {
            tbody.innerHTML = data.html;
            // Re-bind events after search
            bindSendMessageButtons(widgetElement, bringWidgetToFront);
            bindItemImageClick(widgetElement);
            bindModalNavigation(widgetElement);
            bindBorrowButtons(widgetElement, bringWidgetToFront);
          }
        })
        .catch(error => console.error("Error searching items:", error));
    });
  }

  // Rebind initial events for send-message, image click, modal navigation and borrow buttons
  bindSendMessageButtons(widgetElement, bringWidgetToFront);
  bindItemImageClick(widgetElement);
  bindModalNavigation(widgetElement);
  bindBorrowButtons(widgetElement, bringWidgetToFront);

  // Bind scroll event for loading more items when reaching the bottom
  const container = widgetElement.querySelector("#itemListTableContainer");
  if (container) {
    container.addEventListener("scroll", function() {
      if (container.scrollTop + container.clientHeight >= container.scrollHeight - 20) {
        if (container.dataset.loading !== "true" && container.dataset.hasNext === "true") {
          container.dataset.loading = "true";
          const nextPage = container.dataset.nextPage || 2;
          const searchInputValue = widgetElement.querySelector("#itemSearchInput").value;
          let url = "item_list/?page=" + nextPage;
          if (searchInputValue) {
            url += "&q=" + encodeURIComponent(searchInputValue);
          }
          fetch(url)
            .then(response => response.json())
            .then(data => {
              const tbody = widgetElement.querySelector("#itemListTable tbody");
              tbody.insertAdjacentHTML('beforeend', data.html);
              // Reinitialize tooltips and rebind events for new rows
              tbody.querySelectorAll(".borrow-button").forEach(function(button) {
                button.setAttribute("data-bs-toggle", "tooltip");
                button.setAttribute("data-bs-container", "body");
                button.setAttribute("title", "Borrow");
                fixButtonAppearance(button);
              });
              tbody.querySelectorAll(".send-message-button").forEach(function(button) {
                button.setAttribute("data-bs-toggle", "tooltip");
                button.setAttribute("data-bs-container", "body");
                button.setAttribute("title", "Send Message");
                fixButtonAppearance(button);
              });
              const newTooltips = [].slice.call(tbody.querySelectorAll('[data-bs-toggle="tooltip"]'));
              newTooltips.forEach(function(el) {
                new bootstrap.Tooltip(el);
              });
              // Rebind events for newly added rows
              bindBorrowButtons(widgetElement, bringWidgetToFront);
              bindSendMessageButtons(widgetElement, bringWidgetToFront);
              bindItemImageClick(widgetElement);
              bindModalNavigation(widgetElement);
              container.dataset.hasNext = data.has_next ? "true" : "false";
              container.dataset.nextPage = data.next_page;
              container.dataset.loading = "false";
            })
            .catch(error => {
              console.error("Error loading next page:", error);
              container.dataset.loading = "false";
            });
        }
      }
    });
  }

  // Bring the restored widget to the front
  if (typeof bringWidgetToFront === "function") {
    bringWidgetToFront(widgetElement);
  }

  // Rebind reply modal event for send reply if the reply modal exists
  const replyModal = document.getElementById("replyModal_ItemList");
  if (replyModal) {
    const sendReplyButton = replyModal.querySelector("[id^='sendReply_']");
    if (sendReplyButton) {
      sendReplyButton.onclick = function() {
        const form = replyModal.querySelector("form");
        const formData = new FormData(form);
        fetch("send_reply/", {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken")
          },
          body: formData
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              const modalInstance = bootstrap.Modal.getInstance(replyModal) || new bootstrap.Modal(replyModal);
              modalInstance.hide();
            } else {
              console.error("Error sending reply:", data.error);
            }
          })
          .catch(error => console.error("Error sending reply:", error));
      };
    }
  }
}


// Helper function to get current datetime formatted as "YYYY-MM-DDTHH:MM" for datetime-local inputs
function getCurrentDatetimeLocal() {
  const now = new Date();
  const year = now.getFullYear();
  const month = (now.getMonth() + 1).toString().padStart(2, '0');
  const day = now.getDate().toString().padStart(2, '0');
  const hours = now.getHours().toString().padStart(2, '0');
  const minutes = now.getMinutes().toString().padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

/**
 * Binds click events for all borrow buttons
 */
function bindBorrowButtons(widgetElement, bringWidgetToFront) {
  widgetElement.querySelectorAll(".borrow-button").forEach(function(button) {
    if (button.dataset.eventBound === "true") return;
    button.dataset.eventBound = "true";
    button.addEventListener("click", function(e) {
      e.preventDefault();
      const row = e.target.closest("tr");
      if (row) {
        const itemId = row.getAttribute("data-item-id");
        const label = row.getAttribute("data-label"); // Get the item label
        const borrowModalEl = document.getElementById("borrowModal");
        if (!borrowModalEl) {
          console.error("Borrow modal not found.");
          return;
        }
        // Set hidden item_id field in the borrow form
        borrowModalEl.querySelector("#borrowItemId").value = itemId;
        // Update modal title to "Borrow <label>"
        const modalTitle = borrowModalEl.querySelector("#borrowModalLabel");
        if (modalTitle) {
          modalTitle.innerText = "Borrow " + label;
        }
        // When opening the modal, reset the form fields:
        const borrowOnInput = borrowModalEl.querySelector("#borrowedOn");
        if (borrowOnInput) {
          borrowOnInput.value = getCurrentDatetimeLocal(); // set default borrowed_on to now
        }
        const borrowedUntilInput = borrowModalEl.querySelector("#borrowedUntil");
        if (borrowedUntilInput) {
          borrowedUntilInput.value = ""; // reset borrowed_until
        }
        // Show the borrow modal using Bootstrap Modal
        const borrowModal = new bootstrap.Modal(borrowModalEl);
        borrowModal.show();
        
        // Bind the confirm button click event
        const confirmButton = borrowModalEl.querySelector("#borrowConfirmButton");
        confirmButton.onclick = () => {
          const form = borrowModalEl.querySelector("#borrowForm");
          const formData = new FormData(form);
          fetch("borrow_item/", {
            method: "POST",
            headers: {
              "X-Requested-With": "XMLHttpRequest",
              "X-CSRFToken": getCookie("csrftoken")
            },
            body: formData
          })
            .then(response => response.json().then(data => ({ ok: response.ok, data: data })))
            .then(({ ok, data }) => {
              console.log("Borrow response:", data);
              if (ok && data.success) {
                // Success: close modal and update the row.
                borrowModal.hide();
                updateBorrowedItemRow(form);
              } else {
                // Error: display popup with server HTML.
                console.log("Displaying error popup");
                document.body.insertAdjacentHTML('beforeend', data.html);
                var popupModalEl = document.getElementById('popupModal');
                if (popupModalEl) {
                  var popupModal = new bootstrap.Modal(popupModalEl);
                  popupModal.show();
                }
              }
            })
            .catch(error => console.error("Error borrowing item:", error));
        };
      }
    });
  });
}

/**
 * Updates the table row of the borrowed item based on the form values.
 * It sets "available_from" to the borrowed_until value and sets "currently_borrowed" accordingly.
 */
function updateBorrowedItemRow(form) {
  const itemId = form.querySelector("#borrowItemId").value;
  const borrowedUntilValue = form.querySelector("#borrowedUntil").value;
  const borrowedOnValue = form.querySelector("#borrowedOn").value;
  
  const row = document.querySelector(`tr[data-item-id="${itemId}"]`);
  if (!row) {
    console.error("Row for borrowed item not found.");
    return;
  }
  
  const availableFromCell = row.cells[4];
  if (availableFromCell) {
    availableFromCell.innerText = borrowedUntilValue;
  }
  
  const currentlyBorrowedCell = row.cells[5];
  if (currentlyBorrowedCell) {
    const now = new Date();
    const borrowedOnDate = new Date(borrowedOnValue);
    const twoHoursLater = new Date(now.getTime() + 2 * 60 * 60 * 1000);
    currentlyBorrowedCell.innerText = (borrowedOnDate <= twoHoursLater) ? "True" : "False";
  }
}
