import { Badge } from '../ui/Badge';

const FRESHNESS_LABELS: Record<number, string> = {
  0: 'Fresh',
  1: '1 day',
  2: '2-3 days',
  3: '4-7 days',
  4: '1-2 weeks',
  5: '2-4 weeks',
  6: '1-2 months',
  7: '2-6 months',
  8: 'Stale',
};

interface FreshnessBadgeProps {
  value: number;
  showLabel?: boolean;
}

/**
 * Displays freshness level badge (0-8 scale).
 * Per design: 9-level freshness system.
 */
export function FreshnessBadge({ value, showLabel = false }: FreshnessBadgeProps) {
  const clampedValue = Math.max(0, Math.min(8, value));
  const label = showLabel ? FRESHNESS_LABELS[clampedValue] : undefined;

  return <Badge variant="freshness" level={clampedValue} label={label} />;
}