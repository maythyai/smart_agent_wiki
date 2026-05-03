/**
 * Sync Configuration Section
 * Per UI-SPEC.md 2.1-2.3: Sync interval dropdown and direction radio buttons.
 */

interface SyncConfigSectionProps {
  syncInterval: string;
  syncDirection: string;
  onIntervalChange: (value: string) => void;
  onDirectionChange: (value: string) => void;
  disabled?: boolean;
}

const SYNC_INTERVALS = [
  { value: '5min', label: '5 minutes' },
  { value: '15min', label: '15 minutes' },
  { value: '1hr', label: '1 hour' },
  { value: '6hr', label: '6 hours' },
  { value: 'manual', label: 'Manual only' },
];

const SYNC_DIRECTIONS = [
  { value: 'bidirectional', label: 'Bidirectional', icon: '⟳', description: 'Two-way sync' },
  { value: 'inbound_only', label: 'Inbound only', icon: '↓', description: 'Import to SAW' },
  { value: 'outbound_only', label: 'Outbound only', icon: '↑', description: 'Export to platform' },
];

export function SyncConfigSection({
  syncInterval,
  syncDirection,
  onIntervalChange,
  onDirectionChange,
  disabled = false,
}: SyncConfigSectionProps) {
  return (
    <section className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Sync Configuration
      </h2>

      {/* Sync Interval Dropdown */}
      <div className="mb-6">
        <label
          htmlFor="sync-interval"
          className="block text-sm font-medium text-gray-700 mb-2"
        >
          Sync Interval
        </label>
        <select
          id="sync-interval"
          value={syncInterval}
          onChange={(e) => onIntervalChange(e.target.value)}
          disabled={disabled}
          className="w-full sm:w-auto min-w-[200px] px-3 py-2 border border-gray-300 rounded-lg
            text-sm text-gray-900 bg-white
            focus:ring-2 focus:ring-blue-500 focus:border-blue-500
            disabled:bg-gray-100 disabled:cursor-not-allowed"
        >
          {SYNC_INTERVALS.map((interval) => (
            <option key={interval.value} value={interval.value}>
              {interval.label}
            </option>
          ))}
        </select>
        <p className="mt-1 text-xs text-gray-500">
          How often to sync with this platform
        </p>
      </div>

      {/* Sync Direction Radio Group */}
      <fieldset>
        <legend className="block text-sm font-medium text-gray-700 mb-2">
          Sync Direction
        </legend>
        <div className="space-y-2">
          {SYNC_DIRECTIONS.map((direction) => (
            <label
              key={direction.value}
              className={`
                flex items-center gap-3 p-3 rounded-lg border cursor-pointer
                transition-colors
                ${syncDirection === direction.value
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <input
                type="radio"
                name="sync-direction"
                value={direction.value}
                checked={syncDirection === direction.value}
                onChange={() => onDirectionChange(direction.value)}
                disabled={disabled}
                className="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <span className="text-xl" aria-hidden="true">
                {direction.icon}
              </span>
              <div>
                <span className="text-sm font-medium text-gray-900">
                  {direction.label}
                </span>
                <span className="text-xs text-gray-500 ml-2">
                  {direction.description}
                </span>
              </div>
            </label>
          ))}
        </div>
      </fieldset>
    </section>
  );
}