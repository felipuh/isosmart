import Swal from 'sweetalert2';

const baseOptions = {
  background: '#0f172a',
  color: '#e2e8f0',
  confirmButtonColor: '#004990',
  cancelButtonColor: '#475569',
  buttonsStyling: false,
  customClass: {
    popup: 'smart3ai-swal-popup',
    confirmButton: 'smart3ai-swal-confirm',
    cancelButton: 'smart3ai-swal-cancel',
  },
};

export async function showAlert(message, options = {}) {
  return Swal.fire({
    ...baseOptions,
    title: options.title || '',
    text: message,
    icon: options.icon || 'info',
    confirmButtonText: options.confirmButtonText,
  });
}

export async function showConfirm(message, options = {}) {
  const result = await Swal.fire({
    ...baseOptions,
    title: options.title || '',
    text: message,
    icon: options.icon || 'warning',
    showCancelButton: true,
    confirmButtonText: options.confirmButtonText,
    cancelButtonText: options.cancelButtonText,
    reverseButtons: true,
    focusCancel: true,
  });

  return Boolean(result.isConfirmed);
}
