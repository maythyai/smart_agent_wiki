import { Badge } from '../ui/Badge';

const CONFIDENCE_LABELS: Record<number, string> = {
  1: 'Unverified',
  2: 'Single Source',
  3: 'Cross-Validated',
  4: 'Human Verified',
};

interface ConfidenceBadgeProps {
  value: number;
  showLabel?: boolean;
}

/**
 * Displays confidence level badge (1-4 scale).
 * Per design: 4-tier confidence system.
 */
export function ConfidenceBadge({ value, showLabel = false }: ConfidenceBadgeProps) {
  const clampedValue = Math.max(1, Math.min(4, value));
  const label = showLabel ? CONFIDENCE_LABELS[clampedValue] : undefined;

  return <Badge variant="confidence" level={clampedValue} label={label} />;
}