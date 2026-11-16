import { useState } from 'react';
import { Button, Table, Typography } from 'antd';
import { Link } from 'react-router-dom';
import { useCampaigns } from '../api/queries';
import CreateCampaignModal from '../components/CreateCampaignModal';

export default function CampaignsPage() {
  const { data, isLoading } = useCampaigns();
  const [open, setOpen] = useState(false);

  return (
    <div className="page">
      <div className="header">
        <Typography.Title level={3}>Campaigns</Typography.Title>
        <Button type="primary" onClick={() => setOpen(true)}>
          Create campaign
        </Button>
      </div>
      <Table
        loading={isLoading}
        rowKey="id"
        dataSource={data || []}
        columns={[
          {
            title: 'Name',
            dataIndex: 'name',
            render: (v, r) => <Link to={`/campaigns/${r.id}`}>{v}</Link>,
          },
          { title: 'GEO', dataIndex: 'geo_code' },
          { title: 'Domain', dataIndex: 'domain' },
          { title: 'KT ID', dataIndex: 'keitaro_campaign_id', render: (v) => v ?? '—' },
          { title: 'Version', dataIndex: 'current_version_number', render: (v) => v ?? '—' },
        ]}
      />
      <CreateCampaignModal open={open} onClose={() => setOpen(false)} />
    </div>
  );
}
