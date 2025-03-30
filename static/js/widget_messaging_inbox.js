/**
 * widget_messaging_inbox.js
 *
 * This module manages the Messages Inbox widget
 * It exports two functions:
 *   - initWidgetMessagingInbox: for the initial loading of the widget
 *   - initRestoredWidget: for reinitializing restored widgets
 */

/**
 * Helper function to read the CSRF token from the cookies
 */
function getCookie(name) {
  let cookieValue = null
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
      let cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === (name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

/**
 * Helper function to safely set the innerText of an element
 */
function setInnerTextSafe(parent, selector, value) {
  const elem = parent.querySelector(selector)
  if (elem) {
    elem.innerText = value
  } else {
    console.error("Element " + selector + " not found in modal")
  }
}

/**
 * Initializes the Messaging Inbox widget
 */
export function initWidgetMessagingInbox(appendWidget, bringWidgetToFront, showPopupModal) {
  // Retrieve widget content from the server
  fetch("messages_inbox/")
    .then((response) => response.text())
    .then((html) => {
      const widgetElement = appendWidget(html)

      // Bind event to close widget using the top close button
      const closeWidgetBtn = widgetElement.querySelector("#closeWidgetMessagesInbox")
      if (closeWidgetBtn) {
        closeWidgetBtn.addEventListener("click", () => widgetElement.remove())
      }
      // Bind event to close widget using the secondary close button
      const closeBtn = widgetElement.querySelector("#closeMessagesInbox")
      if (closeBtn) {
        closeBtn.addEventListener("click", () => widgetElement.remove())
      }

      let selectedMessageData = {}
      const messageList = widgetElement.querySelector("#messageList")
      const messageBodyDisplay = widgetElement.querySelector("#messageBodyDisplay")

      // Bind click event on message list rows to update message display and store selected message data
      if (messageList && messageBodyDisplay) {
        messageList.addEventListener("click", (e) => {
          const row = e.target.closest("tr")
          if (row && row.dataset.messageId) {
            // Remove highlight from all rows before setting the active row
            Array.from(messageList.getElementsByTagName("tr")).forEach((r) => r.classList.remove("table-active"))
            row.classList.add("table-active")
            // Clean and format message body before displaying
            let cleanBody = row.dataset.body.replace(/\\u002D\s*/g, "")
            cleanBody = cleanBody.replace(/\\u000A/g, "\n").replace(/\\u000D/g, "\r")
            messageBodyDisplay.value = cleanBody
            // Save selected message details for reply functionality
            selectedMessageData = {
              senderNickname: row.dataset.senderNickname,
              senderFlat: row.dataset.senderFlat,
              title: row.dataset.title,
              senderId: row.dataset.senderId,
              receiverId: row.dataset.receiverId,
              messageCode: row.dataset.messageCode,
            }
          }
        })
      }

      // Bind scroll event on message list container for infinite scrolling
      const messageListContainer = widgetElement.querySelector("#messageListContainer")
      let currentPage = 1
      let loading = false
      if (messageListContainer) {
        messageListContainer.addEventListener("scroll", function onScroll() {
          if (loading) return
          // Check if the container has been scrolled near the bottom
          if (messageListContainer.scrollTop + messageListContainer.clientHeight >= messageListContainer.scrollHeight - 10) {
            loading = true
            // Fetch next page of messages from the server
            fetch("messages_inbox/?page=" + (currentPage + 1), {
              headers: { "X-Requested-With": "XMLHttpRequest" },
            })
              .then((response) => response.json())
              .then((data) => {
                if (data.html) {
                  messageList.insertAdjacentHTML("beforeend", data.html)
                  currentPage++
                  // Remove scroll event if no further pages are available
                  if (!data.has_next) {
                    messageListContainer.removeEventListener("scroll", onScroll)
                  }
                }
                loading = false
              })
              .catch((error) => {
                console.error("Error loading more messages:", error)
                loading = false
              })
          }
        })
      }

      // Set up periodic refresh of messages when the list is scrolled to the top
      setInterval(function refreshMessages() {
        if (!messageListContainer) return
        if (messageListContainer.scrollTop > 0) return
        fetch("messages_inbox/?page=1", {
          headers: { "X-Requested-With": "XMLHttpRequest" },
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.html) {
              // Replace message list with refreshed content
              messageList.innerHTML = data.html
            }
          })
          .catch((error) => {
            console.error("Error refreshing messages:", error)
            showPopupModal("<div>Error refreshing messages: " + error + "</div>")
          })
      }, 30000)

      // Bind event to handle reply button click
      const replyButton = widgetElement.querySelector("#replyButton")
      if (replyButton) {
        replyButton.addEventListener("click", () => {
          if (!selectedMessageData.title) {
            alert("Please select a message first")
            return
          }
          const modalId = "replyModal_MessagesInbox"
          const modalEl = document.getElementById(modalId)
          if (!modalEl) {
            console.error("Modal with ID " + modalId + " not found in the DOM")
            return
          }
          // Log the modal element for debugging purposes
          console.log("Modal element found:", modalEl)

          // Populate modal fields with selected message data
          setInnerTextSafe(modalEl, "#replySenderNicknameDisplay_" + modalId, selectedMessageData.senderNickname)
          setInnerTextSafe(modalEl, "#replySenderFlatDisplay_" + modalId, selectedMessageData.senderFlat)
          setInnerTextSafe(modalEl, "#replyTitleDisplay_" + modalId, selectedMessageData.title)

          const senderNicknameInput = modalEl.querySelector("#replySenderNickname_" + modalId)
          if (senderNicknameInput) senderNicknameInput.value = selectedMessageData.senderNickname
          const senderFlatInput = modalEl.querySelector("#replySenderFlat_" + modalId)
          if (senderFlatInput) senderFlatInput.value = selectedMessageData.senderFlat
          const titleInput = modalEl.querySelector("#replyTitle_" + modalId)
          if (titleInput) titleInput.value = selectedMessageData.title
          const senderIdInput = modalEl.querySelector("#replySenderId_" + modalId)
          if (senderIdInput) senderIdInput.value = selectedMessageData.senderId
          const receiverIdInput = modalEl.querySelector("#replyReceiverId_" + modalId)
          if (receiverIdInput) receiverIdInput.value = selectedMessageData.receiverId
          const messageCodeInput = modalEl.querySelector("#replyMessageCode_" + modalId)
          if (messageCodeInput) messageCodeInput.value = selectedMessageData.messageCode
          const replyText = modalEl.querySelector("#replyText_" + modalId)
          if (replyText) replyText.value = ""

          // Create and show the reply modal using Bootstrap's modal plugin
          const replyModal = new bootstrap.Modal(modalEl)
          replyModal.show()

          // Bind the reply submission event to the send reply button in the modal
          const sendReplyButton = modalEl.querySelector("#sendReply_" + modalId)
          if (sendReplyButton) {
            sendReplyButton.onclick = () => {
              const form = modalEl.querySelector("#replyForm_" + modalId)
              const formData = new FormData(form)
              // Send the reply data to the server via a POST request
              fetch("send_reply/", {
                method: "POST",
                headers: {
                  "X-Requested-With": "XMLHttpRequest",
                  "X-CSRFToken": getCookie("csrftoken"),
                },
                body: formData,
              })
                .then((response) => response.json())
                .then((data) => {
                  if (data.success) {
                    // Hide the modal upon successful reply submission
                    replyModal.hide()
                  } else {
                    console.error("Error sending reply:", data.error)
                  }
                })
                .catch((error) => {
                  console.error("Error sending reply:", error)
                  showPopupModal("<div>Error sending reply: " + error + "</div>")
                })
            }
          } else {
            console.error("Send Reply button not found in modal with ID " + modalId)
          }

          // Ensure the widget is brought to front after the modal is closed
          modalEl.addEventListener(
            "hidden.bs.modal",
            () => {
              bringWidgetToFront(widgetElement)
            },
            { once: true }
          )
        })
      }
    })
    .catch((error) => console.error("Error loading messaging inbox widget:", error))
}

/**
 * Reinitializes a restored Messaging Inbox widget
 * Re-binds all event handlers to ensure full functionality after restoration
 */
export function initRestoredWidget(widgetElement, bringWidgetToFront, showPopupModal) {
  // Bind event to close the restored widget using the top close button
  const closeWidgetBtn = widgetElement.querySelector("#closeWidgetMessagesInbox")
  if (closeWidgetBtn) {
    closeWidgetBtn.addEventListener("click", () => widgetElement.remove())
  }
  // Bind event to close the restored widget using the secondary close button
  const closeBtn = widgetElement.querySelector("#closeMessagesInbox")
  if (closeBtn) {
    closeBtn.addEventListener("click", () => widgetElement.remove())
  }

  let selectedMessageData = {}
  const messageList = widgetElement.querySelector("#messageList")
  const messageBodyDisplay = widgetElement.querySelector("#messageBodyDisplay")
  // Bind click event on message list rows to update message display and store selected message data
  if (messageList && messageBodyDisplay) {
    messageList.addEventListener("click", (e) => {
      const row = e.target.closest("tr")
      if (row && row.dataset.messageId) {
        // Remove active styling from all rows before highlighting the selected one
        Array.from(messageList.getElementsByTagName("tr")).forEach((r) => r.classList.remove("table-active"))
        row.classList.add("table-active")
        // Process message body for proper formatting
        let cleanBody = row.dataset.body.replace(/\\u002D\s*/g, "")
        cleanBody = cleanBody.replace(/\\u000A/g, "\n").replace(/\\u000D/g, "\r")
        messageBodyDisplay.value = cleanBody
        // Store message details for later use in reply functionality
        selectedMessageData = {
          senderNickname: row.dataset.senderNickname,
          senderFlat: row.dataset.senderFlat,
          title: row.dataset.title,
          senderId: row.dataset.senderId,
          receiverId: row.dataset.receiverId,
          messageCode: row.dataset.messageCode,
        }
      }
    })
  }

  // Bind event to handle reply button click for the restored widget
  const replyButton = widgetElement.querySelector("#replyButton")
  if (replyButton) {
    replyButton.addEventListener("click", () => {
      if (!selectedMessageData.title) {
        alert("Please select a message first")
        return
      }
      const modalId = "replyModal_MessagesInbox"
      const modalEl = document.getElementById(modalId)
      if (!modalEl) {
        console.error("Modal with ID " + modalId + " not found in the DOM")
        return
      }

      // Populate modal fields with the data from the selected message
      setInnerTextSafe(modalEl, "#replySenderNicknameDisplay_" + modalId, selectedMessageData.senderNickname)
      setInnerTextSafe(modalEl, "#replySenderFlatDisplay_" + modalId, selectedMessageData.senderFlat)
      setInnerTextSafe(modalEl, "#replyTitleDisplay_" + modalId, selectedMessageData.title)

      const senderNicknameInput = modalEl.querySelector("#replySenderNickname_" + modalId)
      if (senderNicknameInput) senderNicknameInput.value = selectedMessageData.senderNickname
      const senderFlatInput = modalEl.querySelector("#replySenderFlat_" + modalId)
      if (senderFlatInput) senderFlatInput.value = selectedMessageData.senderFlat
      const titleInput = modalEl.querySelector("#replyTitle_" + modalId)
      if (titleInput) titleInput.value = selectedMessageData.title
      const senderIdInput = modalEl.querySelector("#replySenderId_" + modalId)
      if (senderIdInput) senderIdInput.value = selectedMessageData.senderId
      const receiverIdInput = modalEl.querySelector("#replyReceiverId_" + modalId)
      if (receiverIdInput) receiverIdInput.value = selectedMessageData.receiverId
      const messageCodeInput = modalEl.querySelector("#replyMessageCode_" + modalId)
      if (messageCodeInput) messageCodeInput.value = selectedMessageData.messageCode
      const replyText = modalEl.querySelector("#replyText_" + modalId)
      if (replyText) replyText.value = ""

      // Create and display the reply modal using Bootstrap
      const replyModal = new bootstrap.Modal(modalEl)
      replyModal.show()

      // Bind reply submission to the send reply button in the restored widget
      const sendReplyButton = modalEl.querySelector("#sendReply_" + modalId)
      if (sendReplyButton) {
        sendReplyButton.onclick = () => {
          const form = modalEl.querySelector("#replyForm_" + modalId)
          const formData = new FormData(form)
          fetch("send_reply/", {
            method: "POST",
            headers: {
              "X-Requested-With": "XMLHttpRequest",
              "X-CSRFToken": getCookie("csrftoken"),
            },
            body: formData,
          })
            .then((response) => response.json())
            .then((data) => {
              if (data.success) {
                replyModal.hide()
              } else {
                console.error("Error sending reply:", data.error)
              }
            })
            .catch((error) => {
              console.error("Error sending reply:", error)
            })
        }
      } else {
        console.error("Send Reply button not found in modal with ID " + modalId)
      }

      // Ensure the restored widget is brought to the front after the reply modal is closed
      modalEl.addEventListener(
        "hidden.bs.modal",
        () => {
          bringWidgetToFront(widgetElement)
        },
        { once: true }
      )
    })
  }
}
