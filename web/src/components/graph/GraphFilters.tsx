import { useStore } from '../../stores';
import { Badge } from '../ui/Badge';

interface GraphFiltersProps {
  onRefresh?: () => void;
}

const ENTITY_TYPES = [
  { value: undefined, label: 'All Types' },
  { value: 'concept', label: 'Concept' },
  { value: 'entity', label: 'Entity' },
  { value: 'document', label: 'Document' },
  { value: 'claim', label: 'Claim' },
  { value: 'person', label: 'Person' },
  { value: 'organization', label: 'Organization' },
];

const RELATION_TYPES = [
  { value: undefined, label: 'All Relations' },
  { value: 'related_to', label: 'Related To' },
  { value: 'contradicts', label: 'Contradicts' },
  { value: 'supports', label: 'Supports' },
  { value: 'derives_from', label: 'Derives From' },
  { value: 'mentions', label: 'Mentions' },
];

const CONFIDENCE_LEVELS = [
  { value: undefined, label: 'Any Confidence' },
  { value: 4, label: 'Human Verified' },
  { value: 3, label: 'Cross-Validated' },
  { value: 2, label: 'Single Source' },
  { value: 1, label: 'Unverified' },
];

export function GraphFilters({ onRefresh }: GraphFiltersProps) {
  const entityTypeFilter = useStore((s) => s.entityTypeFilter);
  const relationTypeFilter = useStore((s) => s.relationTypeFilter);
  const minConfidence = useStore((s) => s.minConfidence);
  const setEntityTypeFilter = useStore((s) => s.setEntityTypeFilter);
  const setRelationTypeFilter = useStore((s) => s.setRelationTypeFilter);
  const setMinConfidence = useStore((s) => s.setMinConfidence);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
      <h3 className="font-medium text-gray-900">Filters</h3>

      {/* Entity type filter per D-12 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Entity Type
        </label>
        <select
          value={entityTypeFilter ?? ''}
          onChange={(e) => setEntityTypeFilter(e.target.value || null)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {ENTITY_TYPES.map((type) => (
            <option key={type.label} value={type.value ?? ''}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Relation type filter per D-12 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Relation Type
        </label>
        <select
          value={relationTypeFilter ?? ''}
          onChange={(e) => setRelationTypeFilter(e.target.value || null)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {RELATION_TYPES.map((type) => (
            <option key={type.label} value={type.value ?? ''}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Confidence filter per D-12 */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Minimum Confidence
        </label>
        <div className="flex flex-wrap gap-2">
          {CONFIDENCE_LEVELS.map((level) => (
            <button
              key={level.label}
              type="button"
              onClick={() => setMinConfidence(level.value ?? null)}
              className={`
                px-3 py-1.5 rounded-lg text-xs font-medium border
                ${minConfidence === level.value
                  ? 'bg-blue-100 border-blue-500 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                }
              `}
            >
              {level.label}
            </button>
          ))}
        </div>
        {minConfidence !== null && (
          <div className="mt-2">
            <Badge variant="confidence" level={minConfidence} />
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="pt-4 flex gap-2">
        <button
          type="button"
          onClick={onRefresh}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          Refresh
        </button>
        <button
          type="button"
          onClick={() => {
            setEntityTypeFilter(null);
            setRelationTypeFilter(null);
            setMinConfidence(null);
          }}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
