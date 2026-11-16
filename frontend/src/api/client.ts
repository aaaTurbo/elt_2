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
  name: string | null;
  description: string | null;
  price: number | null;
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

export type EditorState = { campaign: Campaign; streams: Stream[], has_draft?: boolean };

import { message } from 'antd';

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error?.response?.data?.detail;

    if (error.response?.status >= 500) {
      message.error(detail || 'Server error. Please check backend logs.');
    } else if (error.code === 'ERR_NETWORK') {
      message.error('Network error. Is the backend running?');
    }

    return Promise.reject(error);
  }
);
