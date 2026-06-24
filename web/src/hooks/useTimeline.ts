import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

interface TimelineEntry {
  slug: string;
  title: string;
  entity_type: string;
  date: string;
  time: string | null;
  snippet: string;
  is_daily_note: boolean;
  tags: string[];
}

interface TimelineDay {
  date: string;
  day_name: string;
  entries: TimelineEntry[];
  daily_note_slug: string | null;
}

interface TimelineResponse {
  days: TimelineDay[];
  total_entries: number;
  date_range: { start: string; end: string };
  has_more: boolean;
}

interface DailyNoteResponse {
  slug: string;
  status: string;
  exists: boolean;
}

export function useTimeline(params?: {
  start_date?: string;
  end_date?: string;
  entity_type?: string;
  tag?: string;
  limit?: number;
}) {
  return useQuery<TimelineResponse>({
    queryKey: ['timeline', params],
    queryFn: () => {
      const searchParams = new URLSearchParams();
      if (params?.start_date) searchParams.set('start_date', params.start_date);
      if (params?.end_date) searchParams.set('end_date', params.end_date);
      if (params?.entity_type) searchParams.set('entity_type', params.entity_type);
      if (params?.tag) searchParams.set('tag', params.tag);
      if (params?.limit) searchParams.set('limit', params.limit.toString());

      const queryString = searchParams.toString();
      return api.get<TimelineResponse>(
        `/api/timeline${queryString ? `?${queryString}` : ''}`
      );
    },
    staleTime: 60_000,
  });
}

export function useCreateDailyNote() {
  const queryClient = useQueryClient();
  return useMutation<DailyNoteResponse, Error, string | undefined>({
    mutationFn: (date?: string) =>
      api.post<DailyNoteResponse>('/api/timeline/daily-note', { date }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['timeline'] });
    },
  });
}
