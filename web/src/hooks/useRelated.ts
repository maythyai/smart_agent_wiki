import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

interface RelatedPage {
  slug: string;
  title: string;
  score: number;
  reasons: string[];
}

export function useRelatedPages(slug: string, topK: number = 8) {
  return useQuery<RelatedPage[]>({
    queryKey: ['related', slug, topK],
    queryFn: () => api.get<RelatedPage[]>(`/api/pages/${encodeURIComponent(slug)}/related?top_k=${topK}`),
    enabled: !!slug,
    staleTime: 120_000,
  });
}
