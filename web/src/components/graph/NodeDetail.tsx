import { Link } from 'react-router';
import { Badge } from '../ui/Badge';

interface NodeDetailProps {
  nodeData?: {
    id: string;
    label: string;
    type: string;
    confidence: number;
    description?: string;
  };
}

const CONFIDENCE_LABELS: Record<number, string> = {
  1: 'Unverified',
  2: 'Single Source',
  3: 'Cross-Validated',
  4: 'Human Verified',
};

export function NodeDetail({ nodeData }: NodeDetailProps) {
  if (!nodeData) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <p className="text-gray-500 text-sm">
          Click a node to see details
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
      <div className="flex items-start justify-between">
        <h3 className="font-semibold text-gray-900 text-lg">
          {nodeData.label}
        </h3>
        <Badge variant="confidence" level={nodeData.confidence} />
      </div>

      <div className="space-y-2">
        <div>
          <span className="text-sm font-medium text-gray-500">Type:</span>
          <span className="ml-2 text-sm text-gray-900">{nodeData.type}</span>
        </div>

        <div>
          <span className="text-sm font-medium text-gray-500">Confidence:</span>
          <span className="ml-2">
            <Badge variant="confidence" level={nodeData.confidence} label={CONFIDENCE_LABELS[nodeData.confidence]} />
          </span>
        </div>

        {nodeData.description && (
          <div>
            <span className="text-sm font-medium text-gray-500">Description:</span>
            <p className="mt-1 text-sm text-gray-700">{nodeData.description}</p>
          </div>
        )}
      </div>

      <div className="pt-4 border-t">
        <Link
          to={`/page/${nodeData.label.toLowerCase().replace(/\s+/g, '-')}`}
          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          View Page {'>'}
        </Link>
      </div>
    </div>
  );
}
