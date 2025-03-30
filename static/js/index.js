document.addEventListener('DOMContentLoaded', function() {
  // ----------------------------------------------------------------
  // Inject CSS to ensure that modal dialogs are not cut off at the top
  // ----------------------------------------------------------------
  var modalStyle = document.createElement('style');
  modalStyle.innerHTML = ".modal-dialog { margin-top: 50px !important; }";
  document.head.appendChild(modalStyle);

  // ----------------------------------------------------------------
  // Ensure the navbar is always on top
  // ----------------------------------------------------------------
  var navbar = document.querySelector('.navbar');
  if (navbar) {
    navbar.style.zIndex = '10000'; 
    if (window.getComputedStyle(navbar).position === 'static') {
      navbar.style.position = 'relative';
    }
  }

  // ----------------------------------------------------------------
  // Setup the widget container dimensions and padding
  // ----------------------------------------------------------------
  var widgetContainer = document.getElementById('widgetContainer');
  if (widgetContainer) {
    if (!widgetContainer.style.width) {
      widgetContainer.style.width = window.innerWidth + "px";
    }
    if (!widgetContainer.style.height) {
      widgetContainer.style.height = window.innerHeight + "px";
    }
    widgetContainer.style.paddingTop = '50px';
    if (window.getComputedStyle(widgetContainer).position === 'static') {
      widgetContainer.style.position = 'relative';
    }
  }

  // ----------------------------------------------------------------
  // Global variable to track the highest z-index
  // ----------------------------------------------------------------
  var highestWidgetZIndex = 100;

  /**
   * bringWidgetToFront:
   * Increases the global z-index counter and assigns it to the widget
   */
  function bringWidgetToFront(widget) {
    highestWidgetZIndex++;
    widget.style.zIndex = highestWidgetZIndex;
  }

  /**
   * initDraggableResizable:
   * Applies Interact.js draggable/resizable functionality to the widget
   */
  function initDraggableResizable(widgetElement) {
    if (typeof interact !== 'undefined') {
      interact(widgetElement)
        .draggable({
          inertia: true,
          // Prevent elements inside #itemListTableContainer from being draggable
          ignoreFrom: '#itemListTableContainer',
          modifiers: [
            interact.modifiers.restrictRect({ restriction: 'parent', endOnly: true })
          ],
          listeners: {
            start: function(event) {
              bringWidgetToFront(widgetElement);
            },
            move: dragMoveListener
          }
        })
        .resizable({
          edges: { left: true, right: true, bottom: true, top: true },
          modifiers: [
            interact.modifiers.restrictEdges({ outer: 'parent' })
          ],
          inertia: true,
          listeners: {
            move: function(event) {
              var target = event.target;
              let x = (parseFloat(target.getAttribute('data-x')) || 0);
              let y = (parseFloat(target.getAttribute('data-y')) || 0);
              target.style.width = event.rect.width + 'px';
              target.style.height = event.rect.height + 'px';
              x += event.deltaRect.left;
              y += event.deltaRect.top;
              target.style.transform = 'translate(' + x + 'px, ' + y + 'px)';
              target.setAttribute('data-x', x);
              target.setAttribute('data-y', y);
            }
          }
        });
    }
  }
  

  /**
   * appendWidget:
   * Inserts widget HTML into the widget container, calculates a random position,
   * makes  widget visible, and initializes draggable/resizable functionality
   */
  function appendWidget(html) {
    var container = document.getElementById('widgetContainer');
    if (!container) {
      console.error("Widget container not found.");
      return null;
    }
    container.insertAdjacentHTML('beforeend', html);
    container.classList.remove('hidden');

    var widgets = container.getElementsByClassName('widget');
    var newWidget = widgets[widgets.length - 1];
    newWidget.style.position = "absolute";
    newWidget.style.visibility = "hidden"; 

    var defaultTopOffset = 50;
    setTimeout(function() {
      var containerWidth = container.clientWidth;
      var containerHeight = container.clientHeight;
      var widgetWidth = newWidget.offsetWidth;
      var widgetHeight = newWidget.offsetHeight;
      // var randomLeft = Math.floor(Math.random() * Math.max(0, containerWidth - widgetWidth));
      //var randomTop = Math.floor(Math.random() * Math.max(0, containerHeight - widgetHeight));
      var randomLeft = Math.floor(Math.random() * Math.max(0, (containerWidth - widgetWidth) * 0.3));
      var randomTop = Math.floor(Math.random() * Math.max(0, (containerHeight - widgetHeight) * 0.2));
      newWidget.style.left = randomLeft + "px";
      newWidget.style.top = (randomTop + defaultTopOffset) + "px";
      newWidget.style.visibility = "visible";
      // Immediately bring new widget to the front
      bringWidgetToFront(newWidget);
      // Initialize draggable/resizable functionality
      initDraggableResizable(newWidget);
    }, 0);

    newWidget.addEventListener('mousedown', function() {
      bringWidgetToFront(newWidget);
    });

    return newWidget;
  }

  /**
   * Returns the value of the specified cookie
   */
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      let cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  /**
   * Appends the modal HTML to the document body and displays it
   */
  function showPopupModal(html) {
    document.body.insertAdjacentHTML('beforeend', html);
    var modalEl = document.getElementById('popupModal');
    if (modalEl) {
      var dialog = modalEl.querySelector('.modal-dialog');
      if (dialog) {
        dialog.style.marginTop = '50px';
      }
      var modal = new bootstrap.Modal(modalEl);
      modal.show();
      modalEl.addEventListener('hidden.bs.modal', function () {
        modalEl.remove();
      });
    }
  }

  /**
   * Updates the widget's translation during a drag event
   */
  function dragMoveListener(event) {
    var target = event.target;
    var x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
    var y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
    target.style.transform = 'translate(' + x + 'px, ' + y + 'px)';
    target.setAttribute('data-x', x);
    target.setAttribute('data-y', y);
  }


  //Show Access Code modal if the user is not authorized
  var isAuthorizedEl = document.getElementById('is_authorized');
  if (isAuthorizedEl) {
    if (isAuthorizedEl.dataset.isAuthorized === 'False' && isAuthorizedEl.dataset.isSuperuser === 'False') {
      var modalFormCodeEl = document.getElementById('modalFormCode');
      if (modalFormCodeEl) {
        var accessCodeModal = new bootstrap.Modal(modalFormCodeEl);
        accessCodeModal.show();
      }
    }
  }

  // Invitation modal event listener
  var openInvitationModal = document.getElementById('openInvitationModal');
  if (openInvitationModal && modalContainer) {
    openInvitationModal.addEventListener('click', function(e) {
      e.preventDefault();
      fetch('form_invitation/')
        .then(response => response.text())
        .then(modalHtml => {
          modalContainer.innerHTML = modalHtml;
          var dialog = modalContainer.querySelector('.modal-dialog');
          if (dialog) {
            dialog.style.marginTop = '50px';
          }
          var modalInvitationEl = document.getElementById('modalFormInvitation');
          if (modalInvitationEl) {
            var modalInvitation = new bootstrap.Modal(modalInvitationEl);
            modalInvitation.show();
          }
        })
        .catch(error => console.error('Error loading modalFormInvitation:', error));
    });
  }

  // Building modal event listener
  var openBuildingModal = document.getElementById('openBuildingModal');
  if (openBuildingModal && modalContainer) {
    openBuildingModal.addEventListener('click', function(e) {
      e.preventDefault();
      fetch('form_building/')
        .then(response => response.text())
        .then(modalHtml => {
          modalContainer.innerHTML = modalHtml;
          var dialog = modalContainer.querySelector('.modal-dialog');
          if (dialog) {
            dialog.style.marginTop = '50px';
          }
          var modalBuildingEl = document.getElementById('modalFormBuilding');
          if (modalBuildingEl) {
            var modalBuilding = new bootstrap.Modal(modalBuildingEl);
            modalBuilding.show();
          }
        })
        .catch(error => console.error('Error loading modalFormBuilding:', error));
    });
  }

  // Application Settings modal event listener
  var openAppSettingsModal = document.getElementById('openAppSettingsModal');
  if (openAppSettingsModal && modalContainer) {
    openAppSettingsModal.addEventListener('click', function(e) {
      e.preventDefault();
      fetch('app_settings/')
        .then(response => response.text())
        .then(modalHtml => {
          modalContainer.innerHTML = modalHtml;
          var dialog = modalContainer.querySelector('.modal-dialog');
          if (dialog) {
            dialog.style.marginTop = '50px';
          }
          var modalAppSettingsEl = document.getElementById('modalAppSettings');
          if (modalAppSettingsEl) {
            var modalAppSettings = new bootstrap.Modal(modalAppSettingsEl);
            modalAppSettings.show();
          }
        })
        .catch(error => console.error('Error loading app settings modal:', error));
    });
  }

  // Access Code management modal event listener
  var openAccessCodeModal = document.getElementById('openAccessCodeModal');
  if (openAccessCodeModal && modalContainer) {
    openAccessCodeModal.addEventListener('click', function(e) {
      e.preventDefault();
      fetch('access_code/')
        .then(response => response.text())
        .then(modalHtml => {
          modalContainer.innerHTML = modalHtml;
          var dialog = modalContainer.querySelector('.modal-dialog');
          if (dialog) {
            dialog.style.marginTop = '50px';
          }
          var modalAccessCodeEl = document.getElementById('modalAccessCode');
          if (modalAccessCodeEl) {
            var modalAccessCode = new bootstrap.Modal(modalAccessCodeEl);
            modalAccessCode.show();
          }
        })
        .catch(error => console.error('Error loading access code modal:', error));
    });
  }

  // New Code button event delegation in Access Code modal
  if (modalContainer) {
    modalContainer.addEventListener('click', function(e) {
      if (e.target && e.target.classList.contains('new-code-btn')) {
        e.preventDefault();
        var inputGroup = e.target.closest('.input-group');
        if (inputGroup) {
          var codeInput = inputGroup.querySelector('input[type="text"]');
          if (codeInput) {
            fetch('generate_code/')
              .then(response => response.json())
              .then(data => {
                if (data.code) {
                  codeInput.value = data.code;
                } else {
                  console.error("No code returned from generate_code endpoint.");
                }
              })
              .catch(error => console.error('Error generating new code:', error));
          }
        }
      }
    });
  }

  // Generate Access Codes" button event
  if (modalContainer) {
    modalContainer.addEventListener('click', function(e) {
      if (e.target && e.target.id === 'generateAccessCodes') {
        e.preventDefault();
        var codeCountInput = document.querySelector('input[name="code_count"]');
        if (codeCountInput) {
          var count = parseInt(codeCountInput.value, 10);
          if (isNaN(count) || count < 0) count = 0;
          fetch('generate_codes/?count=' + count)
            .then(response => response.json())
            .then(data => {
              if (data.codes && Array.isArray(data.codes)) {
                var tableBody = document.getElementById('existingAccessCodeTableBody');
                if (tableBody) {
                  data.codes.forEach(function(code) {
                    var row = document.createElement('tr');
                    row.innerHTML = `
                      <td></td>
                      <td>
                        <input type="text" name="new_flat_no_generated[]" value="" class="form-control">
                      </td>
                      <td>
                        <div class="input-group">
                          <input type="text" name="new_code_generated[]" value="${code}" class="form-control" maxlength="16">
                          <button type="button" class="btn btn-info new-code-btn">New Code</button>
                        </div>
                      </td>
                    `;
                    tableBody.appendChild(row);
                  });
                }
              } else {
                console.error("No codes returned from generate_codes endpoint.");
              }
            })
            .catch(error => console.error('Error generating multiple access codes:', error));
        }
      }
    });
  }

  // Update Application Settings table on building dropdown change
  if (modalContainer) {
    modalContainer.addEventListener('change', function(e) {
      if (e.target && e.target.id === 'buildingSelectAppSettings') {
        var selectedId = e.target.value;
        if (selectedId) {
          fetch('get_app_settings/?building_id=' + selectedId)
            .then(response => response.json())
            .then(data => {
              if (data.error) {
                console.error(data.error);
              } else {
                var tableBody = document.getElementById('settingsTableBody');
                if (tableBody) {
                  tableBody.innerHTML = '';
                  let counter = 1;
                  data.settings.forEach(function(setting) {
                    var row = document.createElement('tr');
                    row.innerHTML = `
                      <td>
                        ${setting.id}
                        <input type="hidden" name="setting_id_${counter}" value="${setting.id}">
                      </td>
                      <td>
                        <select name="key_${counter}" class="form-control">
                          <option value="0" ${setting.key === '0' ? 'selected' : ''}>Invitor distance</option>
                          <option value="1" ${setting.key === '1' ? 'selected' : ''}>GMX Reply to Mail Processing</option>
                        </select>
                      </td>
                      <td>
                        <input type="text" name="value_${counter}" value="${setting.value}" class="form-control">
                      </td>
                    `;
                    tableBody.appendChild(row);
                    counter++;
                  });
                  for (let i = 1; i <= 5; i++) {
                    var row = document.createElement('tr');
                    row.innerHTML = `
                      <td></td>
                      <td>
                        <select name="new_key_${i}" class="form-control">
                          <option value="">-- Select Key --</option>
                          <option value="0">Invitor distance</option>
                          <option value="1">GMX Reply to Mail Processing</option>
                        </select>
                      </td>
                      <td>
                        <input type="text" name="new_value_${i}" value="" class="form-control">
                      </td>
                    `;
                    tableBody.appendChild(row);
                  }
                }
              }
            })
            .catch(error => console.error('Error fetching app settings:', error));
        }
      }
    });
  }

  // Update building details in Building modal
  if (modalContainer) {
    modalContainer.addEventListener('change', function(e) {
      if (e.target && e.target.id === 'buildingSelect') {
        var selectedId = e.target.value;
        if (selectedId) {
          fetch('get_building_details/?building_id=' + selectedId)
            .then(response => response.json())
            .then(data => {
              if (data.error) {
                console.error(data.error);
              } else {
                var buildingNameEl = document.getElementById('buildingName');
                var addressLine1El = document.getElementById('addressLine1');
                var addressLine2El = document.getElementById('addressLine2');
                var cityEl = document.getElementById('city');
                var postalCodeEl = document.getElementById('postalCode');
                var unitsEl = document.getElementById('units');
                if (buildingNameEl) buildingNameEl.value = data.name;
                if (addressLine1El) addressLine1El.value = data.address_line1;
                if (addressLine2El) addressLine2El.value = data.address_line2;
                if (cityEl) cityEl.value = data.city;
                if (postalCodeEl) postalCodeEl.value = data.postal_code;
                if (unitsEl) unitsEl.value = data.units;
              }
            })
            .catch(error => console.error('Error fetching building details:', error));
        } else {
          ['buildingName', 'addressLine1', 'addressLine2', 'city', 'postalCode', 'units'].forEach(function(id) {
            var el = document.getElementById(id);
            if (el) el.value = '';
          });
        }
      }
    });
  }

  // Update Access Code table in Access Code modal
  if (modalContainer) {
    modalContainer.addEventListener('change', function(e) {
      if (e.target && e.target.id === 'buildingSelectAccessCode') {
        var selectedId = e.target.value;
        if (selectedId) {
          fetch('get_access_codes/?building_id=' + selectedId)
            .then(response => response.json())
            .then(data => {
              if (data.error) {
                console.error(data.error);
              } else {
                var tableBody = document.getElementById('existingAccessCodeTableBody');
                if (tableBody) {
                  tableBody.innerHTML = '';
                  let counter = 1;
                  data.access_codes.forEach(function(ac) {
                    var row = document.createElement('tr');
                    row.innerHTML = `
                      <td>
                        ${ac.id}
                        <input type="hidden" name="access_code_id_${counter}" value="${ac.id}">
                      </td>
                      <td>
                        <input type="text" name="flat_no_${counter}" value="${ac.flat_no}" class="form-control">
                      </td>
                      <td>
                        <div class="input-group">
                          <input type="text" name="code_${counter}" value="${ac.code}" class="form-control" maxlength="16">
                          <button type="button" class="btn btn-info new-code-btn">New Code</button>
                        </div>
                      </td>
                    `;
                    tableBody.appendChild(row);
                    counter++;
                  });
                }
              }
            })
            .catch(error => console.error('Error fetching access codes:', error));
        }
      }
    });
  }

  // Send Message widget
  var menuSendMessage = document.getElementById('menuSendMessage');
  if (menuSendMessage) {
    menuSendMessage.addEventListener('click', function(e) {
      e.preventDefault();
      import('./widget_send_message.js')
        .then(module => {
          module.initWidgetSendMessage(appendWidget, bringWidgetToFront, getCookie, showPopupModal);
        })
        .catch(error => console.error('Error loading widget_send_message module:', error));
    });
  }

  // Items available for Loan widget
  var menuItemList = document.getElementById('menuItemList');
  if (menuItemList) {
    console.log("menuItemList loaded");
    menuItemList.addEventListener('click', function(e) {
      e.preventDefault();
      import('./widget_item_list.js')
        .then(module => {
          module.initWidgetItemList(appendWidget, bringWidgetToFront);
        })
        .catch(error => console.error('Error loading widget_item_list module:', error));
    });
  }

  // Item Manager widget
  var menuItemManager = document.getElementById('menuItemManager');
  if (menuItemManager) {
    menuItemManager.addEventListener('click', function(e) {
      e.preventDefault();
      import('./widget_item_manager.js')
        .then(module => {
          module.initWidgetItemManager(appendWidget, bringWidgetToFront, getCookie, showPopupModal);
        })
        .catch(error => console.error('Error loading widget_item_manager module:', error));
    });
  }

  // Borrowed Items widget
  var menuBorrowedItems = document.getElementById('menuIBorrowedItems');
  if (menuBorrowedItems) {
    menuBorrowedItems.addEventListener('click', function(e) {
      e.preventDefault();
      import('./widget_borrowed_items.js')
        .then(module => {
          module.initWidgetBorrowedItems(appendWidget, bringWidgetToFront, getCookie, showPopupModal);
        })
        .catch(error => console.error('Error loading widget_borrowed_items module:', error));
    });
  }

  // Loaned Items widget 
  var menuLoanedItems = document.getElementById('menuLoanedItems');
  if (menuLoanedItems) {
    menuLoanedItems.addEventListener('click', function(e) {
      e.preventDefault();
      import('./widget_loaned_items.js')
        .then(module => {
          module.initWidgetLoanedItems(appendWidget, bringWidgetToFront, getCookie, showPopupModal);
        })
        .catch(error => console.error('Error loading widget_loaned_items module:', error));
    });
  }


  // Member Info widget
  var menuMemberInfo = document.getElementById('menuMemberInfo');
  if (menuMemberInfo) {
    menuMemberInfo.addEventListener('click', function(e) {
      e.preventDefault();
      import('./widget_member_info.js')
        .then(module => {
          module.initWidgetMemberInfo(appendWidget, bringWidgetToFront, showPopupModal);
        })
        .catch(error => console.error('Error loading widget_member_info module:', error));
    });
  }

  // Borrowing Request widget
  var borrowingMenu = document.getElementById('menuBorrowingRequest');
  if (borrowingMenu) {
    borrowingMenu.addEventListener('click', function(e) {
      e.preventDefault();
      import('./widget_borrowing_request.js')
        .then(module => {
          module.initWidgetBorrowingRequest(appendWidget, bringWidgetToFront, showPopupModal);
        })
        .catch(error => console.error('Error loading widget_borrowing_request module:', error));
    });
  }

  // Member Communication widget
  var menuCommunication = document.getElementById('menuCommunication');
  if (menuCommunication) {
    menuCommunication.addEventListener('click', function(e) {
      e.preventDefault();
      import('./widget_member_communication.js')
        .then(module => {
          module.initWidgetMemberCommunication(appendWidget, bringWidgetToFront, showPopupModal);
        })
        .catch(error => console.error('Error loading widget_member_communication module:', error));
    });
  }

  // Messages Inbox widget
  var menuMessagesInbox = document.getElementById('menuMessagesInbox');
  if (menuMessagesInbox) {
    menuMessagesInbox.addEventListener('click', function(e) {
      e.preventDefault();
      import('./widget_messaging_inbox.js')
        .then(module => {
          module.initWidgetMessagingInbox(appendWidget, bringWidgetToFront, showPopupModal);
        })
        .catch(error => console.error('Error loading widget_messaging_inbox module:', error));
    });
  }

  // Messages Outbox widget
  var menuMessagesOutbox = document.getElementById('menuMessagesOutbox');
  if (menuMessagesOutbox) {
    menuMessagesOutbox.addEventListener('click', function(e) {
      e.preventDefault();
      import('./widget_messaging_outbox.js')
        .then(module => {
          module.initWidgetMessagingOutbox(appendWidget, bringWidgetToFront, showPopupModal);
        })
        .catch(error => console.error('Error loading widget_messaging_outbox module:', error));
    });
  }

  // Calendar widget
  var menuCalendar = document.getElementById('menuCalendar');
  if (menuCalendar) {
    menuCalendar.addEventListener('click', function(e) {
      e.preventDefault();
      import('./widget_calendar.js')
        .then(module => {
          module.initWidgetCalendar(appendWidget, bringWidgetToFront, showPopupModal);
        })
        .catch(error => console.error('Error loading widget_calendar module:', error));
    });
  }    

  // ----------------------------------------------------------------
  // Widget State Persistence and Drag/Resize Handling
  // ----------------------------------------------------------------
  var authEl = document.getElementById('is_authorized');
  var currentUsername = (authEl && authEl.getAttribute('data-username')) ? authEl.getAttribute('data-username') : 'default';
  var storageKey = "widgetStates_" + currentUsername;

  var savedStates = localStorage.getItem(storageKey);
  if (savedStates) {
    try {
      var widgetStates = JSON.parse(savedStates);
      widgetStates.forEach(function(state) {
        restoreWidget(state);
      });
    } catch (e) {
      console.error("Error parsing widget states from localStorage:", e);
    }
  }

  function saveWidgetStatesNow() {
    var container = document.getElementById('widgetContainer');
    var widgetElements = container ? container.getElementsByClassName('widget') : [];
    var states = [];
    Array.from(widgetElements).forEach(function(widget) {
      var widgetType = "";
      if (widget.querySelector('#closeWidgetMemberInfo') || widget.querySelector('#cancelMemberInfo')) {
        widgetType = "member_info";
      } else if (widget.querySelector('#closeWidgetBorrowingRequest')) {
        widgetType = "borrowing_request";
      } else if (widget.querySelector('#closeWidgetMemberCommunication')) {
        widgetType = "member_communication";
      } else if (widget.querySelector('#closeWidgetMessagesInbox')) {
        widgetType = "messages_inbox";
      } else if (widget.querySelector('#closeWidgetMessagesOutbox')) {
        widgetType = "messages_outbox";
      } else if (widget.querySelector('#closeWidgetSendMessage')) {
        widgetType = "send_message";
      } else if (widget.querySelector('#closeWidgetItemList')) {
        widgetType = "item_list";
      } else if (widget.id === "widgetItemManager" || widget.querySelector('#closeWidgetItemManager')) {
        widgetType = "item_manager";
      } else if (widget.querySelector('#closeWidgetCalendar')) {
        widgetType = "calendar";
      } else if (widget.id === "widgetBorrowedItems" || widget.querySelector('#closeWidgetBorrowedItems')) {
        widgetType = "borrowed_items";
      } else if (widget.id === "widgetLoanedItems" || widget.querySelector('#closeWidgetLoanedItems')) {
        widgetType = "loaned_items";
      }
      if (widgetType) {
        states.push({
          type: widgetType,
          left: widget.style.left,
          top: widget.style.top,
          width: widget.style.width || (widget.offsetWidth + "px"),
          height: widget.style.height || (widget.offsetHeight + "px"),
          zIndex: widget.style.zIndex
        });
      }
    });
    localStorage.setItem(storageKey, JSON.stringify(states));
  }

  window.addEventListener('beforeunload', function() {
    saveWidgetStatesNow();
  });

  var logoutLinks = document.querySelectorAll('a[href*="logout"]');
  logoutLinks.forEach(function(link) {
    link.addEventListener('click', function(e) {
      saveWidgetStatesNow();
    });
  });

  function bringToFront(widget) {
    var container = document.getElementById('widgetContainer');
    if (!container) return;
    var widgets = container.getElementsByClassName('widget');
    var maxZ = 100;
    Array.from(widgets).forEach(function(w) {
      var z = parseInt(w.style.zIndex, 10) || 100;
      if (z > maxZ) maxZ = z;
    });
    widget.style.zIndex = maxZ + 1;
  }

  function dragMoveListener(event) {
    var target = event.target;
    var x = (parseFloat(target.getAttribute('data-x')) || 0) + event.dx;
    var y = (parseFloat(target.getAttribute('data-y')) || 0) + event.dy;
    target.style.transform = 'translate(' + x + 'px, ' + y + 'px)';
    target.setAttribute('data-x', x);
    target.setAttribute('data-y', y);
  }

  var closeButtonSelectors = {
    member_info: ["#closeWidgetMemberInfo", "#cancelMemberInfo"],
    borrowing_request: ["#closeWidgetBorrowingRequest"],
    member_communication: ["#closeWidgetMemberCommunication"],
    messages_inbox: ["#closeWidgetMessagesInbox"],
    messages_outbox: ["#closeWidgetMessagesOutbox"],
    send_message: ["#closeWidgetSendMessage"],
    item_list: ["#closeWidgetItemList"],
    item_manager: ["#closeWidgetItemManager"],
    calendar: ["#closeWidgetCalendar", "#closeWidgetCalendarBottom"],
    borrowed_items: ["#closeWidgetBorrowedItems"],
    loaned_items: ["#closeWidgetLoanedItems"],
  };

  function restoreWidget(widgetState) {
      // Mapping: Widget type -> URL for HTML and module path
      var urlMap = {
        member_info: "member_info/",
        borrowing_request: "borrowing_request/",
        member_communication: "member_communication/",
        messages_inbox: "messages_inbox/",
        messages_outbox: "messages_outbox/",
        send_message: "send_message/",
        item_list: "item_list/",
        item_manager: "item_manager/",
        calendar: "calendar/",
        borrowed_items: "borrowed_items/",
        loaned_items: "loaned_items/"
      };
      var moduleMap = {
        member_info: "./widget_member_info.js",
        borrowing_request: "./widget_borrowing_request.js",
        member_communication: "./widget_member_communication.js",
        messages_inbox: "./widget_messaging_inbox.js",
        messages_outbox: "./widget_messaging_outbox.js",
        send_message: "./widget_send_message.js",
        item_list: "./widget_item_list.js",
        item_manager: "./widget_item_manager.js",
        calendar: "./widget_calendar.js",
        borrowed_items: "./widget_borrowed_items.js",
       loaned_items: "./widget_loaned_items.js",
      };
    
      var url = urlMap[widgetState.type];
      if (!url) return;
    
      fetch(url)
        .then(function(response) {
          return response.text();
        })
        .then(function(html) {
          var container = document.getElementById('widgetContainer');
          if (!container) return;
          container.insertAdjacentHTML('beforeend', html);
          container.classList.remove('hidden');
          var widgets = container.getElementsByClassName('widget');
          var newWidget = widgets[widgets.length - 1];
          newWidget.style.position = "absolute";
          newWidget.style.left = widgetState.left;
          newWidget.style.top = widgetState.top;
          newWidget.style.width = widgetState.width;
          newWidget.style.height = widgetState.height;
          newWidget.style.zIndex = widgetState.zIndex;
          newWidget.style.visibility = "visible";
    
          // Bring restored widget to front when clicked
          newWidget.addEventListener('mousedown', function() {
            bringToFront(newWidget);
          });
    
          // Bind close button events
          var selectors = closeButtonSelectors[widgetState.type] || [];
          selectors.forEach(function(selector) {
            var btn = newWidget.querySelector(selector);
            if (btn) {
              btn.addEventListener('click', function(e) {
                e.preventDefault();
                newWidget.remove();
              });
            }
          });
    
          // Initialize draggable/resizable functionality
          initDraggableResizable(newWidget);
    
          // Dynamically import the appropriate module to bind widget-specific events for restored widget
          var moduleUrl = moduleMap[widgetState.type];
          if (moduleUrl) {
            import(moduleUrl)
              .then(module => {
                if (typeof module.initRestoredWidget === 'function') {
                  module.initRestoredWidget(newWidget, bringWidgetToFront, showPopupModal);
                }
              })
              .catch(error =>
                console.error("Error initializing restored widget of type " + widgetState.type, error)
              );
          }
        })
        .catch(function(error) {
          console.error("Error restoring widget of type " + widgetState.type + ":", error);
        });
    }

    var popupModalEl = document.getElementById("popupModal"); 
      if (popupModalEl) { var popupModal = new bootstrap.Modal(popupModalEl); 
        popupModal.show(); 
      } 

});
