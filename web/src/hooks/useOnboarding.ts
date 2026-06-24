import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

interface OnboardingStatus {
  is_first_run: boolean;
  page_count: number;
}

interface SeedResponse {
  success: boolean;
  kit_id: string;
  kit_name: string;
  pages_created: number;
  errors: string[];
}

export function useOnboardingStatus() {
  return useQuery<OnboardingStatus>({
    queryKey: ['onboarding-status'],
    queryFn: () => api.get<OnboardingStatus>('/api/onboarding/status'),
    staleTime: 60_000,
  });
}

export function useSeedStarterKit() {
  const queryClient = useQueryClient();
  return useMutation<SeedResponse, Error, string>({
    mutationFn: (kitId: string) =>
      api.post<SeedResponse>(`/api/onboarding/seed?kit_id=${kitId}`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding-status'] });
      queryClient.invalidateQueries({ queryKey: ['pages'] });
    },
  });
}
