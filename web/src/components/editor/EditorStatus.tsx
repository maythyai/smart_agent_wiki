import { useStore } from '../../stores';

interface EditorStatusProps {
  /** Whether a save operation is in progress */
  isSaving?: boolean;
  /** Custom class name for styling */
  className?: string;
}

/**
 * Editor status indicator showing save state.
 * Displays "Saving...", "Unsaved changes", or "Saved at {time}".
 * Uses colored indicators for visual feedback.
 */
export function EditorStatus({ isSaving = false, className = '' }: EditorStatusProps) {
  const { isDirty, lastSaved } = useStore();

  // Determine current status
  const status = getStatus(isSaving, isDirty, lastSaved);

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <StatusIndicator status={status} />
      <span className={`text-sm ${status.textColor}`}>
        {status.label}
      </span>
    </div>
  );
}

type StatusType = 'saving' | 'unsaved' | 'saved';

interface StatusInfo {
  type: StatusType;
  label: string;
  indicatorColor: string;
  textColor: string;
}

function getStatus(isSaving: boolean, isDirty: boolean, lastSaved: string | null): StatusInfo {
  if (isSaving) {
    return {
      type: 'saving',
      label: 'Saving...',
      indicatorColor: 'bg-blue-500 animate-pulse',
      textColor: 'text-blue-600',
    };
  }

  if (isDirty) {
    return {
      type: 'unsaved',
      label: 'Unsaved changes',
      indicatorColor: 'bg-amber-500',
      textColor: 'text-amber-600',
    };
  }

  if (lastSaved) {
    const savedTime = formatTime(lastSaved);
    return {
      type: 'saved',
      label: `Saved at ${savedTime}`,
      indicatorColor: 'bg-green-500',
      textColor: 'text-green-600',
    };
  }

  return {
    type: 'saved',
    label: 'Ready',
    indicatorColor: 'bg-gray-400',
    textColor: 'text-gray-500',
  };
}

function formatTime(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return 'unknown';
  }
}

function StatusIndicator({ status }: { status: StatusInfo }) {
  return (
    <span
      className={`inline-block w-2.5 h-2.5 rounded-full ${status.indicatorColor}`}
      aria-label={`${status.type} indicator`}
    />
  );
}

export default EditorStatus;