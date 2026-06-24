import { useEntityTypes } from '../../hooks/useEntityTypes';

interface Props {
  typeId: string;
  size?: 'sm' | 'md';
}

export default function EntityTypeBadge({ typeId, size = 'sm' }: Props) {
  const { data: types } = useEntityTypes();
  const type = types?.find((t) => t.id === typeId);

  if (!type) {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300 ${
          size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm'
        }`}
      >
        📄 {typeId}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm'
      }`}
      style={{
        backgroundColor: `${type.color}18`,
        color: type.color,
      }}
    >
      {type.icon} {type.name}
    </span>
  );
}
