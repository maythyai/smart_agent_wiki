import { useEntityType } from '../../hooks/useEntityTypes';

interface Props {
  typeId: string;
  properties: Record<string, unknown>;
  onChange: (properties: Record<string, unknown>) => void;
  readOnly?: boolean;
}

export default function PropertiesEditor({
  typeId,
  properties,
  onChange,
  readOnly = false,
}: Props) {
  const { data: entityType } = useEntityType(typeId);

  if (!entityType || entityType.fields.length === 0) {
    return null;
  }

  const updateField = (name: string, value: unknown) => {
    onChange({ ...properties, [name]: value });
  };

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400">
        {entityType.icon} {entityType.name} 属性
      </h4>
      {entityType.fields.map((field) => (
        <div key={field.name}>
          <label className="mb-1 block text-xs font-medium text-gray-600 dark:text-gray-400">
            {field.description || field.name}
            {field.required && <span className="ml-0.5 text-red-500">*</span>}
          </label>
          {renderFieldInput(field, properties[field.name], updateField, readOnly)}
        </div>
      ))}
    </div>
  );
}

function renderFieldInput(
  field: { name: string; field_type: string; options: string[] },
  value: unknown,
  onChange: (name: string, value: unknown) => void,
  readOnly: boolean,
) {
  const strVal = String(value ?? '');
  const baseClass =
    'w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none';

  switch (field.field_type) {
    case 'select':
      return (
        <select
          className={baseClass}
          value={strVal}
          disabled={readOnly}
          onChange={(e) => onChange(field.name, e.target.value)}
        >
          <option value="">—</option>
          {field.options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      );

    case 'date':
      return (
        <input
          type="date"
          className={baseClass}
          value={strVal}
          readOnly={readOnly}
          onChange={(e) => onChange(field.name, e.target.value)}
        />
      );

    case 'url':
      return (
        <input
          type="url"
          className={baseClass}
          placeholder="https://..."
          value={strVal}
          readOnly={readOnly}
          onChange={(e) => onChange(field.name, e.target.value)}
        />
      );

    case 'number':
      return (
        <input
          type="number"
          className={baseClass}
          value={strVal}
          readOnly={readOnly}
          onChange={(e) => onChange(field.name, Number(e.target.value))}
        />
      );

    case 'tags':
      return (
        <input
          type="text"
          className={baseClass}
          placeholder="逗号分隔..."
          value={Array.isArray(value) ? (value as string[]).join(', ') : strVal}
          readOnly={readOnly}
          onChange={(e) =>
            onChange(
              field.name,
              e.target.value
                .split(',')
                .map((s) => s.trim())
                .filter(Boolean),
            )
          }
        />
      );

    default:
      return (
        <input
          type="text"
          className={baseClass}
          value={strVal}
          readOnly={readOnly}
          onChange={(e) => onChange(field.name, e.target.value)}
        />
      );
  }
}
