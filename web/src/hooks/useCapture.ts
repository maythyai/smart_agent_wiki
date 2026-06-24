import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';

interface QuickCaptureRequest {
  title: string;
  content?: string;
  tags?: string[];
}

interface QuickCaptureResponse {
  slug: string;
  title: string;
  status: string;
}

export function useCapture() {
  const queryClient = useQueryClient();

  return useMutation<QuickCaptureResponse, Error, QuickCaptureRequest>({
    mutationFn: (data) => api.post<QuickCaptureResponse>('/api/capture', data),
    onSuccess: () => {
      // Invalidate pages list so new page appears
      queryClient.invalidateQueries({ queryKey: ['pages'] });
    },
  });
}
