import { useStore } from '../../stores';

interface GraphControlsProps {
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  onFit?: () => void;
}

export function GraphControls({ onZoomIn, onZoomOut, onFit }: GraphControlsProps) {
  const viewMode = useStore((s) => s.viewMode);
  const setViewMode = useStore((s) => s.setViewMode);
  const layout = useStore((s) => s.layout);
  const setLayout = useStore((s) => s.setLayout);

  const viewModes: Array<{ value: typeof viewMode; label: string }> = [
    { value: 'full', label: 'Full Graph (<50)' },
    { value: 'community', label: 'Community (50-200)' },
    { value: 'clusters', label: 'Clusters (>200)' },
  ];

  const layouts: Array<{ value: typeof layout; label: string }> = [
    { value: 'fcose', label: 'Force' },
    { value: 'concentric', label: 'Concentric' },
    { value: 'breadthfirst', label: 'Hierarchy' },
  ];

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
      <h3 className="font-medium text-gray-900">Controls</h3>

      {/* Zoom controls per D-11 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Zoom
        </label>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onZoomIn}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
          >
            +
          </button>
          <button
            type="button"
            onClick={onFit}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
          >
            Fit
          </button>
          <button
            type="button"
            onClick={onZoomOut}
            className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
          >
            -
          </button>
        </div>
      </div>

      {/* View mode per D-10 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          View Mode
        </label>
        <select
          value={viewMode}
          onChange={(e) => setViewMode(e.target.value as typeof viewMode)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {viewModes.map((mode) => (
            <option key={mode.value} value={mode.value}>
              {mode.label}
            </option>
          ))}
        </select>
      </div>

      {/* Layout per D-10 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Layout
        </label>
        <select
          value={layout}
          onChange={(e) => setLayout(e.target.value as typeof layout)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {layouts.map((l) => (
            <option key={l.value} value={l.value}>
              {l.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
