import { Link } from 'react-router';
import { Badge } from '../ui/Badge';
import type { SearchResult } from '../../types/api';

interface ResultCardProps {
  result: SearchResult;
}

const CONFIDENCE_LABELS: Record<number, string> = {
  1: 'Unverified',
  2: 'Single Source',
  3: 'Cross-Validated',
  4: 'Human Verified',
};

const FRESHNESS_LABELS: Record<number, string> = {
  0: 'Fresh',
  1: 'Recent',
  2: 'Stable',
  3: 'Aging',
  4: 'Moderate',
  5: 'Stale',
  6: 'Old',
  7: 'Very Old',
  8: 'Critical',
};

export function ResultCard({ result }: ResultCardProps) {
  return (
    <article className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow">
      <Link to={`/page/${result.slug}`} className="block">
        <div className="flex items-start justify-between gap-4">
          <h3 className="text-lg font-semibold text-gray-900 hover:text-blue-600">
            {result.title}
          </h3>
          {result.score > 0 && (
            <span className="text-xs text-gray-500 whitespace-nowrap">
              Score: {result.score.toFixed(2)}
            </span>
          )}
        </div>

        <p className="mt-2 text-gray-600 text-sm line-clamp-3">
          {result.snippet}
        </p>

        <div className="mt-3 flex items-center gap-2 flex-wrap">
          {/* Confidence badge per D-06 */}
          <Badge
            variant="confidence"
            level={result.confidence}
            label={CONFIDENCE_LABELS[result.confidence]}
          />

          {/* Freshness indicator per D-06 */}
          <Badge
            variant="freshness"
            level={result.freshness}
            label={FRESHNESS_LABELS[result.freshness]}
          />

          {/* Citation count per D-06 */}
          {result.citations.length > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600">
              {result.citations.length} citation{result.citations.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </Link>
    </article>
  );
}