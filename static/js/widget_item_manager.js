/**
 * widget_item_manager.js
 *
 * This module manages the "Manage My Items" widget.
 * It allows the logged-in user to edit their own items, including:
 *  - Editing title (label), description, available_from, available, and currently_borrowed
 *  - Uploading and deleting images (with caption editing)
 *  - Deleting an item by setting is_deleted=true
 */

// Utility function to get a cookie value
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
 * Initializes the Item Manager Widget.
 */
export function initWidgetItemManager(appendWidget, bringWidgetToFront, getCookie, showPopupModal) {
  fetch("item_manager/")
    .then(response => response.text())
    .then(html => {
      // Append widget HTML and ensure the widget id is set
      const widgetElement = appendWidget(html);
      if (!widgetElement.id || widgetElement.id !== "widgetItemManager") {
        widgetElement.id = "widgetItemManager";
      }
      // Bind close buttons
      const closeButton = widgetElement.querySelector("#closeWidgetItemManager");
      if (closeButton) {
        closeButton.addEventListener("click", function(e) {
          e.preventDefault();
          widgetElement.remove();
        });
      }
      const secondaryCloseButton = widgetElement.querySelector("#closeItemManagerWidget");
      if (secondaryCloseButton) {
        secondaryCloseButton.addEventListener("click", function(e) {
          e.preventDefault();
          widgetElement.remove();
        });
      }
      // Bind Edit buttons
      widgetElement.querySelectorAll(".edit-item-btn").forEach(function(button) {
        button.addEventListener("click", function(e) {
          e.preventDefault();
          const row = button.closest("tr");
          const itemId = row.getAttribute("data-item-id");
          openEditModal(itemId, widgetElement, getCookie, showPopupModal);
        });
      });
      // Bind Delete buttons using a custom confirmation modal
      widgetElement.querySelectorAll(".delete-item-btn").forEach(function(button) {
        button.addEventListener("click", function(e) {
          e.preventDefault();
          const row = button.closest("tr");
          const itemId = row.getAttribute("data-item-id");
          showCustomConfirm("Are you sure you want to delete this item?", function() {
            deleteItem(itemId, widgetElement, getCookie, showPopupModal);
          });
        });
      });
      // Bind "Add New Item" button
      const addNewItemButton = widgetElement.querySelector("#addNewItemBtn");
      if (addNewItemButton) {
        addNewItemButton.addEventListener("click", function(e) {
          e.preventDefault();
          openCreateModal(widgetElement, getCookie, showPopupModal);
        });
      }
      
      // Scroll-based pagination for Item Manager widget 
      const container = widgetElement.querySelector("#itemManagerTableContainer");
      if (container) {
        console.log("Item Manager scroll container found.");
        container.addEventListener("scroll", function() {
          // small threshold to ensure the event fires when nearing the bottom
          if (container.scrollTop + container.clientHeight >= container.scrollHeight - 25) {
            // Check that not already loading and that there's a next page 
            if (container.dataset.loading !== "true" && container.dataset.hasNext === "true") {
              console.log("Loading next page...");
              container.dataset.loading = "true"; // Set loading flag to prevent duplicate calls
              const nextPage = container.dataset.nextPage || 2;
              fetch("item_manager/?page=" + nextPage)
                .then(response => response.json())
                .then(data => {
                  const tbody = widgetElement.querySelector("#itemManagerTable tbody");
                  // Append the new rows from the partial template
                  tbody.insertAdjacentHTML('beforeend', data.html);
                  // Re-bind Edit buttons for new rows
                  tbody.querySelectorAll(".edit-item-btn").forEach(function(button) {
                    button.addEventListener("click", function(e) {
                      e.preventDefault();
                      const row = button.closest("tr");
                      const itemId = row.getAttribute("data-item-id");
                      openEditModal(itemId, widgetElement, getCookie, showPopupModal);
                    });
                  });
                  // Re-bind Delete buttons for new rows
                  tbody.querySelectorAll(".delete-item-btn").forEach(function(button) {
                    button.addEventListener("click", function(e) {
                      e.preventDefault();
                      const row = button.closest("tr");
                      const itemId = row.getAttribute("data-item-id");
                      showCustomConfirm("Are you sure you want to delete this item?", function() {
                        deleteItem(itemId, widgetElement, getCookie, showPopupModal);
                      });
                    });
                  });
                  // Update pagination dataset attributes
                  container.dataset.hasNext = data.has_next ? "true" : "false";
                  container.dataset.nextPage = data.next_page;
                  container.dataset.loading = "false"; // Reset loading flag
                  console.log("Next page loaded. has_next:", data.has_next, "next_page:", data.next_page);
                })
                .catch(error => {
                  console.error("Error loading next page:", error);
                  container.dataset.loading = "false";
                });
            }
          }
        });
        // Trigger a scroll event shortly after binding the event
        setTimeout(function() {
          container.dispatchEvent(new Event('scroll'));
        }, 100);
      } else {
        console.error("Item Manager scroll container not found.");
      }
    })
    .catch(error => console.error("Error loading widget_item_manager:", error));
}

/**
 * Opens the "Create New Item" modal with empty fields.
 */
function openCreateModal(widgetElement, getCookie, showPopupModal) {
  const modalEl = document.getElementById("itemCreateModal");
  // Reset fields
  modalEl.querySelector("#createTitle").value = "";
  modalEl.querySelector("#createDescription").value = "";
  modalEl.querySelector("#createAvailableFrom").value = "";
  modalEl.querySelector("#createAvailable").checked = false;
  modalEl.querySelector("#createCurrentlyBorrowed").checked = false;
  // Clear preview area
  const imagesContainer = modalEl.querySelector("#createItemImagesContainer");
  if (imagesContainer) {
    imagesContainer.innerHTML = "";
  }
  
  // File input change event for the Create Modal
  const fileInput = modalEl.querySelector("#createNewImage");
  if (fileInput) {
    fileInput.addEventListener("change", function () {
      const files = fileInput.files;
      // Clear previous previews
      imagesContainer.innerHTML = "";
      // Loop through all files and create preview images
      for (let i = 0; i < files.length; i++) {
        const reader = new FileReader();
        reader.onload = function (e) {
          // Create an image element and append it to the preview container
          const img = document.createElement("img");
          img.src = e.target.result;
          img.style.width = "100px"; // desired size
          imagesContainer.appendChild(img);
        };
        reader.readAsDataURL(files[i]);
      }
    });
  }
  
  const modalInstance = new bootstrap.Modal(modalEl);
  modalInstance.show();
  // Bind Save button
  const saveButton = modalEl.querySelector("#saveNewItem");
  saveButton.onclick = function() {
    saveNewItem(modalEl, widgetElement, modalInstance, getCookie, showPopupModal);
  };
}

/**
 * Sends the new item data via AJAX to create the item.
 */
function saveNewItem(modalEl, widgetElement, modalInstance, getCookie, showPopupModal) {
  const form = modalEl.querySelector("#itemCreateForm");
  const formData = new FormData(form);
  fetch(`create_item/`, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (!data.success) {
      showPopupModal(data.html);
      return;
    }
    // Retrieve the new item's id from the response
    const newItemId = data.item_id;
    
    // Get the file input element from the create modal
    const fileInput = modalEl.querySelector("#createNewImage");
    // If there are files selected, upload each one
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
      const files = fileInput.files;
      const caption = modalEl.querySelector("#createNewImageCaption").value;
      let uploadPromises = [];
      // Loop through each file and prepare a FormData for upload
      for (let i = 0; i < files.length; i++) {
        let fd = new FormData();
        fd.append("image", files[i]);
        fd.append("caption", caption);
        uploadPromises.push(
          fetch(`upload_item_image/${newItemId}/`, {
            method: "POST",
            headers: {
              "X-Requested-With": "XMLHttpRequest",
              "X-CSRFToken": getCookie("csrftoken")
            },
            body: fd
          }).then(response => response.json())
        );
      }
      // Wait for all image uploads to complete
      Promise.all(uploadPromises)
      .then(results => {
        // process the upload responses
        showPopupModal(results[0].html);
        modalInstance.hide();
        refreshItemManager(widgetElement, getCookie, showPopupModal);
      })
      .catch(error => {
        console.error("Error uploading images:", error);
        modalInstance.hide();
        refreshItemManager(widgetElement, getCookie, showPopupModal);
      });
    } else {
      // No images selected; just hide the modal and refresh the widget
      modalInstance.hide();
      refreshItemManager(widgetElement, getCookie, showPopupModal);
      showPopupModal(data.html);
    }
  })
  .catch(error => console.error("Error creating new item:", error));
}

/**
 * Opens the edit modal for a given item.
 * Fetches image details via AJAX and pre-populates the form fields.
 */
function openEditModal(itemId, widgetElement, getCookie, showPopupModal) {
  const row = widgetElement.querySelector(`tr[data-item-id="${itemId}"]`);
  const title = row.children[1].textContent;
  const description = row.getAttribute("data-full-description");
  const availableFrom = row.children[3].textContent.trim();
  const available = row.children[4].textContent.trim() === "True";
  const currentlyBorrowed = row.children[5].textContent.trim() === "True";

  const modalEl = document.getElementById("itemEditModal");
  modalEl.querySelector("#editItemId").value = itemId;
  modalEl.querySelector("#editTitle").value = title;
  modalEl.querySelector("#editDescription").value = description;
  if (availableFrom) {
    const dtLocal = availableFrom.replace(" ", "T");
    modalEl.querySelector("#editAvailableFrom").value = dtLocal;
  } else {
    modalEl.querySelector("#editAvailableFrom").value = "";
  }
  modalEl.querySelector("#editAvailable").checked = available;
  modalEl.querySelector("#editCurrentlyBorrowed").checked = currentlyBorrowed;

  const imagesContainer = modalEl.querySelector("#itemImagesContainer");
  imagesContainer.innerHTML = "";
  fetch(`get_item_images/${itemId}/`)
    .then(response => response.json())
    .then(data => {
      if (!data.success) {
        showPopupModal(data.html);
        return;
      }
      if (data.images && data.images.length > 0) {
        data.images.forEach(image => {
          const imgDiv = document.createElement("div");
          imgDiv.className = "mb-2";
          imgDiv.innerHTML = `
            <img src="${image.url}" alt="${image.caption}" style="width:100px; height:auto;">
            <input type="text" class="form-control small-input edit-image-caption" value="${image.caption}" data-image-id="${image.id}">
            <button type="button" class="btn btn-sm btn-danger delete-image-btn" data-image-id="${image.id}" style="width:100px; margin-top:5px;">Delete Image</button>
            <button type="button" class="btn btn-sm btn-secondary save-image-caption-btn" data-image-id="${image.id}" style="width:100px; margin-top:5px;">Save Caption</button>
          `;
          imagesContainer.appendChild(imgDiv);
        });
        imagesContainer.querySelectorAll(".delete-image-btn").forEach(function(btn) {
          btn.addEventListener("click", function(e) {
            e.preventDefault();
            const imageId = btn.getAttribute("data-image-id");
            showCustomConfirm("Delete this image?", function() {
              deleteItemImage(imageId, () => {
                btn.parentElement.remove();
              }, getCookie, showPopupModal);
            });
          });
        });
        imagesContainer.querySelectorAll(".save-image-caption-btn").forEach(function(btn) {
          btn.addEventListener("click", function(e) {
            e.preventDefault();
            const imageId = btn.getAttribute("data-image-id");
            const captionInput = imagesContainer.querySelector(`.edit-image-caption[data-image-id="${imageId}"]`);
            if (captionInput) {
              const newCaption = captionInput.value;
              updateImageCaption(imageId, newCaption);
            }
          });
        });
      }
    })
    .catch(error => console.error("Error fetching item images:", error));
  
  const modalInstance = new bootstrap.Modal(modalEl);
  modalInstance.show();
  modalEl.addEventListener("hidden.bs.modal", function () {
    modalEl.querySelector("#newImage").value = "";
    modalEl.querySelector("#newImageCaption").value = "";

    document.querySelectorAll('.modal-backdrop').forEach(function (backdrop) {
      backdrop.parentNode.removeChild(backdrop);
    });
  });
  const saveButton = modalEl.querySelector("#saveItemEdit");
  saveButton.onclick = function() {
    saveItemEdits(modalEl, widgetElement, modalInstance, getCookie, showPopupModal);
  };
}

/**
 * Saves the edited item details via AJAX.
 */
function saveItemEdits(modalEl, widgetElement, modalInstance, getCookie, showPopupModal) {
  const form = modalEl.querySelector("#itemEditForm");
  const formData = new FormData(form);
  const itemId = formData.get("item_id");

  fetch(`update_item/${itemId}/`, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      if (!data.success) {
        showPopupModal(data.html);
        return;
      }
      const newImageInput = modalEl.querySelector("#newImage");
      if (newImageInput && newImageInput.files && newImageInput.files.length > 0) {
        const files = newImageInput.files;
        let uploadPromises = [];
        // Loop through each selected file
        for (let i = 0; i < files.length; i++) {
          let fd = new FormData();
          fd.append("image", files[i]);
          // Using the same caption for all image
          const caption = modalEl.querySelector("#newImageCaption").value;
          fd.append("caption", caption);
          uploadPromises.push(
            fetch(`upload_item_image/${itemId}/`, {
              method: "POST",
              headers: {
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCookie("csrftoken")
              },
              body: fd
            }).then(response => response.json())
          );
        }
        // Wait for all upload requests to complete
        Promise.all(uploadPromises).then(results => {
          //process each result here
          showPopupModal(results[0].html);
          modalInstance.hide();
          refreshItemManager(widgetElement, getCookie, showPopupModal);
          setTimeout(function() {
            const container = widgetElement.querySelector("#itemManagerTableContainer");
            if (container) {
              container.dispatchEvent(new Event('scroll'));
            }
          }, 200);
        }).catch(error => {
          console.error("Error uploading images:", error);
          modalInstance.hide();
          refreshItemManager(widgetElement, getCookie, showPopupModal);
          setTimeout(function() {
            const container = widgetElement.querySelector("#itemManagerTableContainer");
            if (container) {
              container.dispatchEvent(new Event('scroll'));
            }
          }, 200);
        });
      } else {
        modalInstance.hide();
        refreshItemManager(widgetElement, getCookie, showPopupModal);
        setTimeout(function() {
          const container = widgetElement.querySelector("#itemManagerTableContainer");
          if (container) {
            container.dispatchEvent(new Event('scroll'));
          }
        }, 200);
      }
    })
    .catch(error => console.error("Error saving item edits:", error));
}

/**
 * Deletes an item (sets is_deleted=true) via AJAX.
 */
function deleteItem(itemId, widgetElement, getCookie, showPopupModal) {
  fetch(`delete_item/${itemId}/`, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": getCookie("csrftoken")
    }
  })
    .then(response => response.json())
    .then(data => {
      if (!data.success) {
        showPopupModal(data.html);
      } else {
        const row = widgetElement.querySelector(`tr[data-item-id="${itemId}"]`);
        if (row) row.remove();
        showPopupModal(data.html);
      }
    })
    .catch(error => console.error("Error deleting item:", error));
}

/**
 * Deletes an image associated with an item via AJAX.
 */
function deleteItemImage(imageId, callback, getCookie, showPopupModal) {
  fetch(`delete_item_image/${imageId}/`, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": getCookie("csrftoken")
    }
  })
    .then(response => response.json())
    .then(data => {
      if (!data.success) {
        showPopupModal(data.html);
      } else {
        callback();
        showPopupModal(data.html);
      }
    })
    .catch(error => console.error("Error deleting image:", error));
}

/**
 * Updates the caption of an image via AJAX.
 */
function updateImageCaption(imageId, newCaption) {
  console.log("Updating caption for imageId:", imageId);
  fetch(`update_item_image_caption/${imageId}/`, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: new URLSearchParams({ caption: newCaption })
  })
    .then(response => response.json())
    .then(data => {
      showPopupModal(data.html);
    })
    .catch(error => console.error("Error updating image caption:", error));
}

/**
 * Refreshes the Item Manager widget content.
 */
function refreshItemManager(widgetElement, getCookie, showPopupModal) {
  fetch("item_manager/")
    .then(response => response.text())
    .then(html => {
      // Parse the returned HTML to extract updated parts
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      // Extract the updated tbody content from the fetched HTML
      const newTbody = doc.querySelector("#itemManagerTable tbody");
      if (newTbody) {
        const currentTbody = widgetElement.querySelector("#itemManagerTable tbody");
        if (currentTbody) {
          currentTbody.innerHTML = newTbody.innerHTML;
        }
      }
      // Update the container's dataset attributes (hasNext, nextPage, loading)
      const newContainer = doc.querySelector("#itemManagerTableContainer");
      const currentContainer = widgetElement.querySelector("#itemManagerTableContainer");
      if (newContainer && currentContainer) {
        currentContainer.dataset.hasNext = newContainer.dataset.hasNext;
        currentContainer.dataset.nextPage = newContainer.dataset.nextPage;
        currentContainer.dataset.loading = "false";
      }
      // Re-bind the event listeners for new rows (Edit/Delete buttons)
      const tbody = widgetElement.querySelector("#itemManagerTable tbody");
      tbody.querySelectorAll(".edit-item-btn").forEach(function(button) {
        button.addEventListener("click", function(e) {
          e.preventDefault();
          const row = button.closest("tr");
          const itemId = row.getAttribute("data-item-id");
          openEditModal(itemId, widgetElement, getCookie, showPopupModal);
        });
      });
      tbody.querySelectorAll(".delete-item-btn").forEach(function(button) {
        button.addEventListener("click", function(e) {
          e.preventDefault();
          const row = button.closest("tr");
          const itemId = row.getAttribute("data-item-id");
          showCustomConfirm("Are you sure you want to delete this item?", function() {
            deleteItem(itemId, widgetElement, getCookie, showPopupModal);
          });
        });
      });
    })
    .catch(error => console.error("Error refreshing item manager widget:", error));
}


/**
 * Reinitializes a restored Item Manager Widget.
 * Binds close, edit, and delete event listeners.
 */
export function initRestoredWidget(widgetElement, bringWidgetToFront, getCookie, showPopupModal) {
  // Bind close buttons for the item manager widget
  const closeButton = widgetElement.querySelector("#closeWidgetItemManager");
  if (closeButton) {
    closeButton.addEventListener("click", function(e) {
      e.preventDefault();
      widgetElement.remove();
    });
  }
  const secondaryCloseButton = widgetElement.querySelector("#closeItemManagerWidget");
  if (secondaryCloseButton) {
    secondaryCloseButton.addEventListener("click", function(e) {
      e.preventDefault();
      widgetElement.remove();
    });
  }

  // Bind Edit buttons: open the edit modal for the corresponding item
  widgetElement.querySelectorAll(".edit-item-btn").forEach(function(button) {
    button.addEventListener("click", function(e) {
      e.preventDefault();
      const row = button.closest("tr");
      const itemId = row.getAttribute("data-item-id");
      openEditModal(itemId, widgetElement, getCookie, showPopupModal);
    });
  });

  // Bind Delete buttons: show confirmation and delete the item if confirmed
  widgetElement.querySelectorAll(".delete-item-btn").forEach(function(button) {
    button.addEventListener("click", function(e) {
      e.preventDefault();
      const row = button.closest("tr");
      const itemId = row.getAttribute("data-item-id");
      showCustomConfirm("Are you sure you want to delete this item?", function() {
        deleteItem(itemId, widgetElement, getCookie, showPopupModal);
      });
    });
  });

  // Bind the "Add New Item" button to open the create modal
  const addNewItemButton = widgetElement.querySelector("#addNewItemBtn");
  if (addNewItemButton) {
    addNewItemButton.addEventListener("click", function(e) {
      e.preventDefault();
      openCreateModal(widgetElement, getCookie, showPopupModal);
    });
  }

  // Bind scroll event for pagination on the container
  const container = widgetElement.querySelector("#itemManagerTableContainer");
  if (container) {
    container.addEventListener("scroll", function() {
      // When scrolled near the bottom, load the next page if available
      if (container.scrollTop + container.clientHeight >= container.scrollHeight - 20) {
        if (container.dataset.loading !== "true" && container.dataset.hasNext === "true") {
          container.dataset.loading = "true"; // Prevent duplicate loads
          const nextPage = container.dataset.nextPage || 2;
          fetch("item_manager/?page=" + nextPage)
            .then(response => response.json())
            .then(data => {
              const tbody = widgetElement.querySelector("#itemManagerTable tbody");
              tbody.insertAdjacentHTML('beforeend', data.html);
              // Re-bind new Edit buttons in the newly appended rows
              tbody.querySelectorAll(".edit-item-btn").forEach(function(button) {
                button.addEventListener("click", function(e) {
                  e.preventDefault();
                  const row = button.closest("tr");
                  const itemId = row.getAttribute("data-item-id");
                  openEditModal(itemId, widgetElement, getCookie, showPopupModal);
                });
              });
              // Re-bind new Delete buttons in the newly appended rows
              tbody.querySelectorAll(".delete-item-btn").forEach(function(button) {
                button.addEventListener("click", function(e) {
                  e.preventDefault();
                  const row = button.closest("tr");
                  const itemId = row.getAttribute("data-item-id");
                  showCustomConfirm("Are you sure you want to delete this item?", function() {
                    deleteItem(itemId, widgetElement, getCookie, showPopupModal);
                  });
                });
              });
              // Update pagination dataset attributes
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

  // Rebind modal event listeners for the Create Modal
  const createModalEl = document.getElementById("itemCreateModal");
  if (createModalEl) {
    // Bind Save button in the Create Modal
    const saveNewItemButton = createModalEl.querySelector("#saveNewItem");
    if (saveNewItemButton) {
      saveNewItemButton.onclick = function() {
        // Use bootstrap.Modal.getInstance() to get the current modal instance
        saveNewItem(createModalEl, widgetElement, bootstrap.Modal.getInstance(createModalEl), getCookie, showPopupModal);
      };
    }
    // Cancel button uses data-bs-dismiss
  }

  // Rebind modal event listeners for the Edit Modal
  const editModalEl = document.getElementById("itemEditModal");
  if (editModalEl) {
    const saveItemEditButton = editModalEl.querySelector("#saveItemEdit");
    if (saveItemEditButton) {
      saveItemEditButton.onclick = function() {
        saveItemEdits(editModalEl, widgetElement, bootstrap.Modal.getInstance(editModalEl), getCookie, showPopupModal);
      };
    }
    //  additional buttons 
  }

  // Bring the restored widget to the front
  if (typeof bringWidgetToFront === "function") {
    bringWidgetToFront(widgetElement);
  }
}


/**
 * Custom confirmation modal function.
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
            <button type="button" class="btn btn-danger" id="confirmOk">Delete</button>
          </div>
        </div>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', confirmHtml);
  const confirmModalEl = document.getElementById('confirmPopupModal');
  const confirmModal = new bootstrap.Modal(confirmModalEl);
  confirmModal.show();
  confirmModalEl.querySelector('#confirmCancel').addEventListener('click', function() {
    confirmModal.hide();
    confirmModalEl.addEventListener('hidden.bs.modal', function() {
      confirmModal.dispose(); 
      confirmModalEl.remove();
    }, { once: true });
  });
  confirmModalEl.querySelector('#confirmOk').addEventListener('click', function() {
    onConfirm();
    confirmModal.hide();
    confirmModalEl.addEventListener('hidden.bs.modal', function() {
      confirmModal.dispose();  
      confirmModalEl.remove();
    }, { once: true });
  });
}
