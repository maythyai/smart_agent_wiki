import { useStore } from '../../stores';
import { Spinner } from '../ui/Spinner';

interface EditorToolbarProps {
  /** Callback when save button is clicked */
  onSave?: () => void;
  /** Callback to switch to edit mode */
  onEdit?: () => void;
  /** Callback to switch to view/preview mode */
  onPreview?: () => void;
  /** Callback when cancel is clicked (discard changes) */
  onCancel?: () => void;
  /** Whether a save operation is in progress */
  isSaving?: boolean;
}

/**
 * Editor toolbar with mode-based action buttons.
 * Per D-14: Supports view/edit/preview mode transitions.
 * Per D-15: Save button enabled only when there are unsaved changes.
 */
export function EditorToolbar({
  onSave,
  onEdit,
  onPreview,
  onCancel,
  isSaving = false,
}: EditorToolbarProps) {
  const { mode, isDirty, setMode } = useStore();

  const handleModeSwitch = (newMode: 'view' | 'edit' | 'preview') => {
    setMode(newMode);
    if (newMode === 'edit') {
      onEdit?.();
    } else if (newMode === 'preview') {
      onPreview?.();
    }
  };

  const handleSave = () => {
    if (!isSaving && isDirty) {
      onSave?.();
    }
  };

  const handleCancel = () => {
    // Reset dirty state handled by parent
    onCancel?.();
  };

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200">
      {/* Mode switcher - left side */}
      <div className="flex items-center space-x-2">
        <ModeButton
          label="View"
          active={mode === 'view'}
          onClick={() => handleModeSwitch('view')}
          disabled={isSaving}
        />
        <ModeButton
          label="Edit"
          active={mode === 'edit'}
          onClick={() => handleModeSwitch('edit')}
          disabled={isSaving}
        />
        <ModeButton
          label="Preview"
          active={mode === 'preview'}
          onClick={() => handleModeSwitch('preview')}
          disabled={isSaving}
        />
      </div>

      {/* Action buttons - right side */}
      <div className="flex items-center space-x-3">
        {mode === 'edit' && isDirty && (
          <button
            type="button"
            onClick={handleCancel}
            disabled={isSaving}
            className="px-3 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        )}

        {mode === 'edit' && (
          <button
            type="button"
            onClick={handleSave}
            disabled={!isDirty || isSaving}
            className="inline-flex items-center px-4 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-blue-400"
          >
            {isSaving ? (
              <>
                <Spinner size="sm" className="mr-2 text-white" />
                Saving...
              </>
            ) : (
              <>
                <SaveIcon className="mr-1.5" />
                Save
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
}

interface ModeButtonProps {
  label: string;
  active: boolean;
  onClick: () => void;
  disabled?: boolean;
}

function ModeButton({ label, active, onClick, disabled }: ModeButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
        active
          ? 'bg-white text-blue-600 shadow-sm border border-gray-200'
          : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
      } disabled:opacity-50 disabled:cursor-not-allowed`}
    >
      {label}
    </button>
  );
}

function SaveIcon({ className = '' }: { className?: string }) {
  return (
    <svg
      className={`w-4 h-4 ${className}`}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"
      />
    </svg>
  );
}

export default EditorToolbar;