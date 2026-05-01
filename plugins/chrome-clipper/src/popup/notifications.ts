/**
 * Notification System
 *
 * Implements in-popup and system notifications for clip success/failure.
 */

export type NotificationType = 'success' | 'error' | 'info' | 'warning';

export interface NotificationOptions {
  message: string;
  duration?: number; // ms, 0 for persistent
  actions?: Array<{
    label: string;
    onClick: () => void;
  }>;
}

/**
 * Show in-popup notification
 */
export function showNotification(
  type: NotificationType,
  options: string | NotificationOptions
): void {
  const opts = typeof options === 'string' ? { message: options } : options;
  const duration =
    opts.duration ?? (type === 'success' ? 3000 : type === 'error' ? 5000 : 4000);

  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.innerHTML = `
    <span class="notification-icon">${getIcon(type)}</span>
    <span class="notification-message">${escapeHtml(opts.message)}</span>
    ${
      opts.actions
        ? opts.actions
            .map((a) => `<button class="notification-action">${escapeHtml(a.label)}</button>`)
            .join('')
        : ''
    }
    <button class="notification-close">&#x2715;</button>
  `;

  // Add to DOM
  let container = document.querySelector('.notification-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'notification-container';
    document.body.appendChild(container);
  }
  container.appendChild(notification);

  // Bind action buttons
  if (opts.actions) {
    notification.querySelectorAll('.notification-action').forEach((btn, i) => {
      btn.addEventListener('click', opts.actions![i].onClick);
    });
  }

  // Close button
  notification
    .querySelector('.notification-close')!
    .addEventListener('click', () => {
      notification.remove();
    });

  // Auto dismiss
  if (duration > 0) {
    setTimeout(() => {
      notification.classList.add('notification-fade-out');
      setTimeout(() => notification.remove(), 300);
    }, duration);
  }
}

/**
 * Show system notification (requires 'notifications' permission)
 */
export async function showSystemNotification(
  title: string,
  message: string,
  options?: {
    type?: 'basic' | 'image' | 'list';
    iconUrl?: string;
    buttons?: Array<{ title: string }>;
  }
): Promise<void> {
  // For now, use in-popup notifications
  // System notifications require additional permission
  showNotification('info', { message: `${title}: ${message}` });
}

/**
 * Quick toast notification
 */
export function toast(message: string, duration: number = 2000): void {
  showNotification('info', { message, duration });
}

/**
 * Get icon for notification type
 */
function getIcon(type: NotificationType): string {
  switch (type) {
    case 'success':
      return '&#x2714;';
    case 'error':
      return '&#x2716;';
    case 'warning':
      return '&#x26A0;';
    case 'info':
      return '&#x2139;';
  }
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
