/**
 * Property Mapping Editor
 * Per UI-SPEC.md 2.4 and D-12-D-14: Field mapping dropdowns for Notion/Logseq.
 */

import { useState } from 'react';

interface PropertyMappingEditorProps {
  platform: string;
  mappings: Record<string, string>;
  availableProperties?: string[];
  onMappingChange: (field: string, property: string) => void;
  onAddMapping?: (field: string, property: string) => void;
  disabled?: boolean;
}

// SAW standard fields that can be mapped
const SAW_FIELDS = [
  { key: 'title', label: 'Title', required: true },
  { key: 'content', label: 'Content', required: true },
  { key: 'confidence', label: 'Confidence', required: false },
  { key: 'freshness', label: 'Freshness', required: false },
];

// Platforms that support property mapping
const MAPPING_PLATFORMS = ['notion', 'logseq'];

// Default properties for Logseq (property drawer fields)
const LOGSEQ_DEFAULT_PROPERTIES = [
  'title',
  'content',
  'confidence',
  'freshness',
  'tags',
  'created-at',
  'updated-at',
];

export function PropertyMappingEditor({
  platform,
  mappings,
  availableProperties,
  onMappingChange,
  onAddMapping,
  disabled = false,
}: PropertyMappingEditorProps) {
  const [customField, setCustomField] = useState('');
  const [customProperty, setCustomProperty] = useState('');

  // Only render for platforms that support property mapping
  if (!MAPPING_PLATFORMS.includes(platform)) {
    return null;
  }

  // Determine available properties based on platform
  const properties = platform === 'logseq'
    ? LOGSEQ_DEFAULT_PROPERTIES
    : availableProperties || ['Name', 'Body', 'Confidence Score', 'Last Modified'];

  const handleAddCustomMapping = () => {
    if (customField && customProperty && onAddMapping) {
      onAddMapping(customField, customProperty);
      setCustomField('');
      setCustomProperty('');
    }
  };

  return (
    <section className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Property Mappings
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        Map SAW fields to {platform === 'notion' ? 'Notion database' : 'Logseq property'} fields
      </p>

      {/* Standard field mappings */}
      <div className="space-y-4">
        {SAW_FIELDS.map((field) => (
          <div key={field.key} className="flex items-center gap-4">
            <label
              htmlFor={`mapping-${field.key}`}
              className="text-sm font-medium text-gray-700 w-24 shrink-0"
            >
              {field.label}
              {field.required && (
                <span className="text-red-500 ml-1">*</span>
              )}
            </label>
            <select
              id={`mapping-${field.key}`}
              value={mappings[field.key] || ''}
              onChange={(e) => onMappingChange(field.key, e.target.value)}
              disabled={disabled}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg
                text-sm text-gray-900 bg-white
                focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Select property...</option>
              {properties.map((prop) => (
                <option key={prop} value={prop}>
                  {prop}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>

      {/* Add custom mapping */}
      {onAddMapping && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Add Custom Mapping
          </h3>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              placeholder="SAW field name"
              value={customField}
              onChange={(e) => setCustomField(e.target.value)}
              disabled={disabled}
              className="px-3 py-2 border border-gray-300 rounded-lg
                text-sm text-gray-900 bg-white
                focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                disabled:bg-gray-100 disabled:cursor-not-allowed
                flex-1"
            />
            <select
              value={customProperty}
              onChange={(e) => setCustomProperty(e.target.value)}
              disabled={disabled}
              className="px-3 py-2 border border-gray-300 rounded-lg
                text-sm text-gray-900 bg-white
                focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                disabled:bg-gray-100 disabled:cursor-not-allowed
                flex-1"
            >
              <option value="">Select property...</option>
              {properties.map((prop) => (
                <option key={prop} value={prop}>
                  {prop}
                </option>
              ))}
            </select>
            <button
              onClick={handleAddCustomMapping}
              disabled={disabled || !customField || !customProperty}
              className="px-4 py-2 text-sm font-medium text-blue-600
                border border-blue-600 rounded-lg
                hover:bg-blue-50 focus:ring-2 focus:ring-blue-500
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-colors"
            >
              Add
            </button>
          </div>
        </div>
      )}
    </section>
  );
}