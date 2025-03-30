/**
 * widget_calendar.js
 *
 * This module implements the Calendar widget
 * It exports two functions:
 *   - initWidgetCalendar: Loads and displays the Calendar widget
 *   - initRestoredWidget: Binds necessary events to a restored Calendar widget
 */

export function initWidgetCalendar(appendWidget, bringWidgetToFront, showPopupModal) {
  // Load the calendar for the current month by default
  fetch('calendar/')
    .then(response => response.text())
    .then(html => {
      var widgetElement = appendWidget(html);
      // Initialize calendar functionality on the widget element
      initCalendarWidget(widgetElement);
    })
    .catch(error => console.error('Error loading calendar widget:', error));
}

export function initRestoredWidget(widgetElement, bringWidgetToFront, showPopupModal) {
  // Reinitialize calendar functionality on the restored widget element
  initCalendarWidget(widgetElement);
}

/**
* initCalendarWidget:
* Binds Close and Navigation events to the Calendar widget
*/
function initCalendarWidget(widgetElement) {
  // Bind top Close button to remove the widget
  var closeButton = widgetElement.querySelector('#closeWidgetCalendar');
  if (closeButton) {
    closeButton.addEventListener('click', function() {
      widgetElement.remove();
    });
  }
  
  // Bind bottom Close button to remove the widget
  var closeButtonBottom = widgetElement.querySelector('#closeWidgetCalendarBottom');
  if (closeButtonBottom) {
    closeButtonBottom.addEventListener('click', function() {
      widgetElement.remove();
    });
  }
  
  // Get navigation buttons and the calendar title element
  var prevButton = widgetElement.querySelector('#prevMonth');
  var nextButton = widgetElement.querySelector('#nextMonth');
  var calendarTitle = widgetElement.querySelector('#calendarTitle');

  // Helper function to parse the calendar title
  function parseCalendarTitle(titleText) {
    var parts = titleText.replace('Calendar - ', '').split(' ');
    if (parts.length === 2) {
      var monthName = parts[0];
      var year = parseInt(parts[1], 10);
      // Determine the month index from the month name
      var month = new Date(Date.parse(monthName + " 1, 2012")).getMonth() + 1;
      return { year: year, month: month };
    }
    return null;
  }
  
  // Function to update the calendar via AJAX based on the given year and month
  function updateCalendar(year, month) {
    var url = 'calendar/' + year + '/' + month + '/';
    fetch(url)
      .then(response => response.text())
      .then(html => {
        // Create a temporary container to parse the new HTML
        var tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        // Extract the new header and calendar container content
        var newHeader = tempDiv.querySelector('.calendar-header');
        var newCalendarContainer = tempDiv.querySelector('.calendar-container');
        // Update the inner parts of the current widget element
        var header = widgetElement.querySelector('.calendar-header');
        var calendarContainer = widgetElement.querySelector('.calendar-container');
        if (header && newHeader) {
          header.innerHTML = newHeader.innerHTML;
        }
        if (calendarContainer && newCalendarContainer) {
          calendarContainer.innerHTML = newCalendarContainer.innerHTML;
        }
        // Re-bind calendar events after updating the content
        initCalendarWidget(widgetElement);
      })
      .catch(error => console.error('Error updating calendar widget:', error));
  }
  
  // Bind previous month navigation button
  if (prevButton) {
    prevButton.addEventListener('click', function() {
      var current = parseCalendarTitle(calendarTitle.textContent);
      if (current) {
        var year = current.year;
        var month = current.month;
        month -= 1;
        if (month < 1) {
          month = 12;
          year -= 1;
        }
        updateCalendar(year, month);
      }
    });
  }
  
  // Bind next month navigation button
  if (nextButton) {
    nextButton.addEventListener('click', function() {
      var current = parseCalendarTitle(calendarTitle.textContent);
      if (current) {
        var year = current.year;
        var month = current.month;
        month += 1;
        if (month > 12) {
          month = 1;
          year += 1;
        }
        updateCalendar(year, month);
      }
    });
  }
}
