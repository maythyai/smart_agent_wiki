interface BadgeProps {
  variant: 'confidence' | 'freshness' | 'default';
  level: number;
  label?: string;
}

const CONFIDENCE_COLORS: Record<number, string> = {
  1: 'bg-gray-100 text-gray-800',
  2: 'bg-amber-100 text-amber-800',
  3: 'bg-green-100 text-green-800',
  4: 'bg-blue-100 text-blue-800',
};

const FRESHNESS_COLORS: Record<number, string> = {
  0: 'bg-green-100 text-green-800',
  1: 'bg-lime-100 text-lime-800',
  2: 'bg-yellow-100 text-yellow-800',
  3: 'bg-yellow-100 text-yellow-800',
  4: 'bg-amber-100 text-amber-800',
  5: 'bg-orange-100 text-orange-800',
  6: 'bg-red-100 text-red-800',
  7: 'bg-red-100 text-red-800',
  8: 'bg-red-200 text-red-900',
};

export function Badge({ variant, level, label }: BadgeProps) {
  const colorClass = variant === 'confidence'
    ? CONFIDENCE_COLORS[level] || CONFIDENCE_COLORS[1]
    : variant === 'freshness'
      ? FRESHNESS_COLORS[level] || FRESHNESS_COLORS[0]
      : 'bg-gray-100 text-gray-800';

  const displayLabel = label ?? (variant === 'confidence'
    ? `C${level}`
    : variant === 'freshness'
      ? `F${level}`
      : String(level));

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
      {displayLabel}
    </span>
  );
}