import { useState, useEffect } from 'react';

/**
 * Debounces a value by the specified delay (per D-05: 300ms default).
 * @param value The value to debounce
 * @param delay Debounce delay in milliseconds (default: 300)
 */
export function useDebouncedValue<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}