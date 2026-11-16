import axios from 'axios';

export const api = axios.create({ baseURL: '/api/v1' });

export type Campaign = {
  id: string;
  name: string;
  geo_code: string;
  domain: string;
  group_id: number;
  source_id: number;
  keitaro_campaign_id: number | null;
  current_version_number: number | null;
};

export type Offer = {
  id: string;
  keitaro_offer_id: number;
  weight: number;
  is_weight_fixed: boolean;
  is_deleted_in_kt: boolean;
  deleted_in_kt_at: string | null;
};

export type Stream = {
  id: string;
  type: 'redirect' | 'flow';
  redirect_url: string | null;
  keitaro_stream_id: number | null;
  position: number;
  offers: Offer[];
};

export type EditorState = { campaign: Campaign; streams: Stream[] };
