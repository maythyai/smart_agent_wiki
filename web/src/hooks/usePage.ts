import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router';
import { api } from '../lib/api';
import type { PageResponse, PageUpdate, PageStatus } from '../types/api';

/**
 * TanStack Query hook for fetching a single page.
 * @param slug Page slug/identifier
 * @returns Query result with data (PageResponse), isLoading, error
 */
export function usePage(slug: string) {
  return useQuery<PageResponse>({
    queryKey: ['page', slug],
    queryFn: () => api.get<PageResponse>(`/api/pages/${encodeURIComponent(slug)}`),
    enabled: !!slug, // Only fetch when slug is truthy
    staleTime: 60_000, // Consider fresh for 1min
  });
}

/**
 * TanStack Query hook for updating a page.
 * @param slug Page slug/identifier
 * @returns Mutation result with mutate (updatePage), isPending
 */
export function useUpdatePage(slug: string) {
  const queryClient = useQueryClient();

  return useMutation<PageStatus, Error, PageUpdate>({
    mutationFn: (data: PageUpdate) =>
      api.put<PageStatus>(`/api/pages/${encodeURIComponent(slug)}`, data),
    onSuccess: () => {
      // Invalidate the page query to refetch updated data
      queryClient.invalidateQueries({ queryKey: ['page', slug] });
    },
  });
}

/**
 * TanStack Query hook for deleting a page.
 * @param slug Page slug/identifier
 * @returns Mutation result with mutate (deletePage), isPending
 */
export function useDeletePage(slug: string) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation<PageStatus, Error, void>({
    mutationFn: () =>
      api.delete<PageStatus>(`/api/pages/${encodeURIComponent(slug)}`),
    onSuccess: () => {
      // Invalidate both the specific page and the pages list
      queryClient.invalidateQueries({ queryKey: ['page', slug] });
      queryClient.invalidateQueries({ queryKey: ['pages'] });
      // Navigate to home after successful deletion
      navigate('/');
    },
  });
}

/**
 * TanStack Query hook for updating a page's entity_type and/or properties.
 * @param slug Page slug/identifier
 * @returns Mutation result with mutate (updateProperties), isPending
 */
export function useUpdateProperties(slug: string) {
  const queryClient = useQueryClient();

  return useMutation<
    PageStatus,
    Error,
    { entity_type?: string; properties?: Record<string, unknown> }
  >({
    mutationFn: (data) =>
      api.patch<PageStatus>(
        `/api/pages/${encodeURIComponent(slug)}/properties`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['page', slug] });
      queryClient.invalidateQueries({ queryKey: ['pages'] });
    },
  });
}
