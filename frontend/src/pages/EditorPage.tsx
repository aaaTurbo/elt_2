import {useState} from 'react';
import {
    Alert, Button, Card, Checkbox, Divider, InputNumber, Space, Table, Tag,
    Typography, message,
} from 'antd';
import {useParams, useNavigate } from 'react-router-dom';
import {
    KtOffer,
    useAddOffer, useDiscard, useEditor, useFetchKt, usePush, useRemoveOffer,
    useRollbackOffer, useSetFixed,
} from '../api/queries';
import type {Offer, Stream} from '../api/client';
import OfferAutocomplete from "../components/OfferAutocomplete";

export default function EditorPage() {
    const {id = ''} = useParams();
    const navigate = useNavigate();
    const {data, isLoading} = useEditor(id);
    const push = usePush(id);
    const fetchKt = useFetchKt(id);
    const discard = useDiscard(id);

    if (isLoading || !data) return <div className="page">Loading…</div>;

    const totalFixed = data.streams
        .flatMap((s) => s.offers)
        .filter((o) => o.is_weight_fixed && !o.is_deleted_in_kt)
        .reduce((acc, o) => acc + o.weight, 0);

        return (
        <div
            className="page"
            style={{

                backgroundColor: data.has_draft ? '#fffbe6' : '#f5f5f5',
                transition: 'background-color 0.3s ease',
                minHeight: '100vh',
                padding: '24px'
            }}
        >
            <div className="header">
                <div>
                    <Button onClick={() => navigate('/')} style={{ marginBottom: 8 }}>
                        ← Back to Campaigns
                    </Button>
                    <Typography.Title level={3} style={{ margin: 0 }}>
                        {data.campaign.name}
                        {data.has_draft && <Tag color="warning" style={{ marginLeft: 12 }}>Draft mode</Tag>}
                    </Typography.Title>
                    <Typography.Text type="secondary">
                        GEO {data.campaign.geo_code} · KT ID {data.campaign.keitaro_campaign_id ?? '—'} ·
                        version {data.campaign.current_version_number ?? '—'}
                    </Typography.Text>
                </div>
                <Space>
                    <Button
                        onClick={() => fetchKt.mutate(undefined, {
                            onSuccess: () => message.success('Fetched from Keitaro'),
                            onError: (e: any) => message.error(e?.response?.data?.detail || 'Fetch failed'),
                        })}
                        loading={fetchKt.isPending}
                    >
                        Fetch from KT
                    </Button>

                    <Button
                        danger
                        onClick={() => discard.mutate(undefined, {
                            onSuccess: () => message.success('Draft discarded'),
                            onError: (e: any) => message.error(e?.response?.data?.detail || 'Discard failed'),
                        })}
                        loading={discard.isPending}
                        disabled={!data.has_draft}
                    >
                        Discard draft
                    </Button>

                    <Button
                        type="primary"
                        onClick={() => push.mutate(undefined, {
                            onSuccess: (data: any) => message.success(`Pushed! KT ID: ${data.keitaro_campaign_id}`),
                            onError: (e: any) => message.error(e?.response?.data?.detail || 'Push failed. Check logs.'),
                        })}
                        loading={push.isPending}
                    >
                        Push to KT
                    </Button>
                </Space>
            </div>

            {/* Баннер предупреждения */}
            {data.has_draft && (
                <Alert
                    type="warning"
                    showIcon
                    message="You have un-pushed changes"
                    description="Your local changes are not saved to Keitaro yet. Click 'Push to KT' to apply them, or 'Discard draft' to revert."
                    style={{ marginBottom: 24 }}
                />
            )}

            {totalFixed > 100 && (
                <Alert type="error" message={`Fixed weights sum = ${totalFixed}% (>100%)`} style={{ marginBottom: 24 }} />
            )}

            <div className="streams">
                {data.streams.map((s) => (
                    <StreamCard key={s.id} campaignId={id} stream={s}/>
                ))}
            </div>
        </div>
    );
}

function StreamCard({campaignId, stream}: { campaignId: string; stream: Stream }) {
    const add = useAddOffer(campaignId);
    const remove = useRemoveOffer(campaignId);
    const rollback = useRollbackOffer(campaignId);
    const setFixed = useSetFixed(campaignId);
    const [newOffer, setNewOffer] = useState<number | null>(null);

    const activeSum = stream.offers
        .filter((o) => !o.is_deleted_in_kt)
        .reduce((a, o) => a + o.weight, 0);

    return (
        <Card
            title={
                <Space>
                    <Tag color={stream.type === 'redirect' ? 'orange' : 'blue'}>
                        {stream.type === 'redirect' ? 'Redirect' : 'Offer flow'}
                    </Tag>
                    <span>Stream #{stream.position}</span>
                    {stream.type === 'flow' && (
                        <Tag color={Math.abs(activeSum - 100) < 0.01 ? 'green' : 'red'}>
                            Sum: {activeSum.toFixed(2)}%
                        </Tag>
                    )}
                </Space>
            }
            style={{marginBottom: 16}}
        >
            {stream.type === 'redirect' ? (
                <Typography.Paragraph>
                    Redirects to <a href={stream.redirect_url || '#'}>{stream.redirect_url}</a>.
                    No offers in this stream.
                </Typography.Paragraph>
            ) : (
                <>
                    <Table<Offer>
                        rowKey="id"
                        pagination={false}
                        dataSource={stream.offers}
                        rowClassName={(r) => (r.is_deleted_in_kt ? 'row-deleted' : '')}
                        columns={[
                            {
                                title: 'Offer',
                                dataIndex: 'keitaro_offer_id',
                                render: (v, r) => (
                                    <Space direction="vertical" size={0}>
                                        <span><strong>{v}</strong></span>
                                        {r.name && <Typography.Text type="secondary">{r.name}</Typography.Text>}
                                        {r.is_deleted_in_kt && <Tag color="red">deleted in KT</Tag>}
                                    </Space>
                                ),
                            },
                            {
                                title: 'Weight %',
                                dataIndex: 'weight',
                                width: 180,
                                render: (v: number, r) =>
                                    r.is_deleted_in_kt ? (
                                        <span>{v.toFixed(2)}</span>
                                    ) : r.is_weight_fixed ? (
                                        <InputNumber
                                            min={0}
                                            max={100}
                                            step={0.01}
                                            value={v}
                                            onChange={(val) =>
                                                setFixed.mutate({
                                                    streamId: stream.id,
                                                    offerRowId: r.id,
                                                    fixed: true,
                                                    weight: Number(val ?? 0),
                                                })
                                            }
                                        />
                                    ) : (
                                        <span>{v.toFixed(2)}</span>
                                    ),
                            },
                            {
                                title: 'Fixed',
                                dataIndex: 'is_weight_fixed',
                                width: 100,
                                render: (v: boolean, r) => (
                                    <Checkbox
                                        checked={v}
                                        disabled={r.is_deleted_in_kt}
                                        onChange={(e) =>
                                            setFixed.mutate({
                                                streamId: stream.id,
                                                offerRowId: r.id,
                                                fixed: e.target.checked,
                                            })
                                        }
                                    />
                                ),
                            },
                            {
                                title: 'Actions',
                                width: 220,
                                render: (_, r) =>
                                    r.is_deleted_in_kt ? (
                                        <Button
                                            type="primary"
                                            size="small"
                                            onClick={() =>
                                                rollback.mutate({streamId: stream.id, offerRowId: r.id})
                                            }
                                        >
                                            Rollback
                                        </Button>
                                    ) : (
                                        <Button
                                            danger
                                            size="small"
                                            onClick={() =>
                                                remove.mutate({streamId: stream.id, offerRowId: r.id})
                                            }
                                        >
                                            Remove
                                        </Button>
                                    ),
                            },
                        ]}
                    />
                    <Divider/>
                    <AddOfferBlock campaignId={campaignId} streamId={stream.id}/>
                </>
            )}
        </Card>
    );
}

function AddOfferBlock({campaignId, streamId}: { campaignId: string; streamId: string }) {
    const [selectedOffer, setSelectedOffer] = useState<KtOffer | null>(null);
    const add = useAddOffer(campaignId);

    return (
        <Space.Compact style={{width: '100%', maxWidth: 480}}>
            <OfferAutocomplete value={selectedOffer} onChange={setSelectedOffer}/>
            <Button
                type="primary"
                disabled={!selectedOffer}
                loading={add.isPending}
                onClick={() => {
                    if (!selectedOffer) return;
                    add.mutate(
                        {streamId, offerId: selectedOffer.id, name: selectedOffer.name},
                        {
                            onSuccess: () => {
                                setSelectedOffer(null);
                                message.success('Offer added');
                            },
                            onError: (e: any) =>
                                message.error(e?.response?.data?.detail || 'Failed to add offer'),
                        }
                    );
                }}
            >
                Add
            </Button>
        </Space.Compact>
    );
}
