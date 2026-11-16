import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, Campaign, EditorState } from './client';

export const useCampaigns = () =>
  useQuery({
    queryKey: ['campaigns'],
    queryFn: async () => (await api.get<Campaign[]>('/campaigns')).data,
  });

export const useCreateCampaign = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      name: string;
      geo_code: string;
      offer_id: number;
      offer_name?: string;
    }) => (await api.post<Campaign>('/campaigns', body)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['campaigns'] }),
  });
};

export const useEditor = (id: string) =>
  useQuery({
    queryKey: ['editor', id],
    queryFn: async () =>
      (await api.get<EditorState>(`/campaigns/${id}/editor`)).data,
    enabled: !!id,
  });

const useEditorMutation = (id: string, fn: (arg: any) => Promise<any>) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: (data: EditorState) => {
      qc.setQueryData(['editor', id], data);
      qc.invalidateQueries({ queryKey: ['editor', id] });
    },
  });
};

export const useAddOffer = (id: string) =>
  useEditorMutation(id, (a: { streamId: string; offerId: number; name?: string }) =>
    api
      .post<EditorState>(
        `/campaigns/${id}/editor/streams/${a.streamId}/offers`,
        { keitaro_offer_id: a.offerId, name: a.name }
      )
      .then((r) => r.data)
  );
export const useRemoveOffer = (id: string) =>
  useEditorMutation(id, (a: { streamId: string; offerRowId: string }) =>
    api
      .delete<EditorState>(
        `/campaigns/${id}/editor/streams/${a.streamId}/offers/${a.offerRowId}`
      )
      .then((r) => r.data)
  );

export const useRollbackOffer = (id: string) =>
  useEditorMutation(id, (a: { streamId: string; offerRowId: string }) =>
    api
      .post<EditorState>(
        `/campaigns/${id}/editor/streams/${a.streamId}/offers/${a.offerRowId}/rollback`
      )
      .then((r) => r.data)
  );

export const useSetFixed = (id: string) =>
  useEditorMutation(
    id,
    (a: { streamId: string; offerRowId: string; fixed: boolean; weight?: number }) =>
      api
        .patch<EditorState>(
          `/campaigns/${id}/editor/streams/${a.streamId}/offers/${a.offerRowId}`,
          { fixed: a.fixed, weight: a.weight }
        )
        .then((r) => r.data)
  );

export const usePush = (id: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post(`/campaigns/${id}/editor/push`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['editor', id] });
      qc.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
};

export const useFetchKt = (id: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api.post<EditorState>(`/campaigns/${id}/editor/fetch`).then((r) => r.data),
    onSuccess: (data) => {
      qc.setQueryData(['editor', id], data);
      qc.invalidateQueries({ queryKey: ['editor', id] });
      qc.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
};

export const useDiscard = (id: string) => {
  const qc = useQueryClient();
  return useMutation({

    mutationFn: () => api.post<EditorState>(`/campaigns/${id}/editor/discard`).then((r) => r.data),
    onSuccess: (data) => {
      qc.setQueryData(['editor', id], data);
      qc.invalidateQueries({ queryKey: ['editor', id] });
    },
  });
};

export type KtOffer = { id: number; name: string };

export const useOfferSearch = (q: string) =>
  useQuery({
    queryKey: ['offers-search', q],
    queryFn: async () =>
      (
        await api.get<KtOffer[]>('/offers/search', { params: { q, limit: 20 } })
      ).data,
    enabled: q.length >= 0,
    placeholderData: (prev) => prev,
  });