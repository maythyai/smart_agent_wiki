import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { EntityType } from '../types/api';

export function useEntityTypes() {
  return useQuery<EntityType[]>({
    queryKey: ['entity-types'],
    queryFn: () => api.get<EntityType[]>('/api/entity-types'),
    staleTime: 300_000, // 5 min — rarely changes
  });
}

export function useEntityType(typeId: string | undefined) {
  const all = useEntityTypes();
  const entityType = all.data?.find((t) => t.id === typeId) ?? undefined;
  return { ...all, data: entityType };
}
