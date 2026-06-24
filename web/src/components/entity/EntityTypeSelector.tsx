import { useEntityTypes } from '../../hooks/useEntityTypes';

interface Props {
  value: string;
  onChange: (typeId: string) => void;
}

export default function EntityTypeSelector({ value, onChange }: Props) {
  const { data: types, isLoading } = useEntityTypes();

  if (isLoading || !types) {
    return (
      <div className="grid grid-cols-4 gap-2 animate-pulse">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="h-16 rounded-lg bg-gray-100 dark:bg-gray-700" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-4 gap-2">
      {types.map((type) => {
        const isSelected = value === type.id;
        return (
          <button
            key={type.id}
            type="button"
            onClick={() => onChange(type.id)}
            className={`flex flex-col items-center gap-1 rounded-lg border-2 p-3 transition-all hover:scale-105 ${
              isSelected
                ? 'border-current shadow-md'
                : 'border-transparent bg-gray-50 hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700'
            }`}
            style={isSelected ? { borderColor: type.color, color: type.color } : undefined}
            title={type.description}
          >
            <span className="text-2xl">{type.icon}</span>
            <span className="text-xs font-medium">{type.name}</span>
          </button>
        );
      })}
    </div>
  );
}
