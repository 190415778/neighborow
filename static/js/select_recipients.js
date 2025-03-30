function initSelectRecipientsFilter() {
  // Get the filter input and recipient select elements
  const filterInput = document.getElementById('filterInput');
  const recipientSelect = document.getElementById('recipientSelect');

  if (filterInput && recipientSelect) {
    // Bind input event to filter the select options dynamically
    filterInput.addEventListener('input', function() {
      const filterValue = filterInput.value.toLowerCase();
      for (let i = 0; i < recipientSelect.options.length; i++) {
        let option = recipientSelect.options[i];
        option.hidden = option.text.toLowerCase().indexOf(filterValue) === -1;
      }
    });
  }

  // Log that the filter function for select recipients has been initialized
  console.log('Filter function for select recipients has been initialized.');
}

// Global event listener for clicks
document.addEventListener('click', function(e) {
if (e.target && e.target.id === 'modalSelectRecipientsOK') {
  // Read selected options
  const recipientSelect = document.getElementById('recipientSelect');
  const selectedIds = Array.from(recipientSelect.selectedOptions).map(option => option.value);
  
  // Update hidden field in widget with selected recipient IDs
  const hiddenInput = document.getElementById('selectedRecipients');
  hiddenInput.value = selectedIds.join(',');
  
  // close the modal
  const modalEl = document.getElementById('modalSelectRecipients');
  let modalInstance = bootstrap.Modal.getInstance(modalEl);
  if (!modalInstance) {
    modalInstance = new bootstrap.Modal(modalEl);
  }
  modalInstance.hide();
}
});
