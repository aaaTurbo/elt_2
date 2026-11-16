import {Form, Input, Modal, message} from 'antd';
import {useCreateCampaign} from '../api/queries';
import OfferAutocomplete from './OfferAutocomplete';

export default function CreateCampaignModal({
                                                open,
                                                onClose,
                                            }: {
    open: boolean;
    onClose: () => void;
}) {
    const [form] = Form.useForm();
    const mutation = useCreateCampaign();

    return (
        <Modal
            title="Create campaign"
            open={open}
            onCancel={() => {
                form.resetFields();
                onClose();
            }}
            onOk={async () => {
                try {
                    const values = await form.validateFields();

                    const offerId = typeof values.offer_id === 'object' ? values.offer_id?.id : values.offer_id;
                    const offerName = typeof values.offer_id === 'object' ? values.offer_id?.name : undefined;

                    if (!offerId) {
                        message.error('Please select a valid offer');
                        return;
                    }

                    await mutation.mutateAsync({
                        ...values,
                        offer_id: Number(offerId),
                        offer_name: offerName
                    });

                    message.success('Campaign created');
                    form.resetFields();
                    onClose();
                } catch (e: any) {
                    if (e?.response?.data?.detail) {
                        const details = e.response.data.detail;
                        if (Array.isArray(details)) {
                            message.error(details.map((d: any) => d.msg).join(', '));
                        } else {
                            message.error(details);
                        }
                    } else if (!e?.errorFields) {
                        message.error(e.message || 'Failed to create campaign');
                    }
                }
            }}
            confirmLoading={mutation.isPending}
        >
            <Form form={form} layout="vertical">
                <Form.Item name="name" label="Name" rules={[{required: true}]}>
                    <Input/>
                </Form.Item>
                <Form.Item name="geo_code" label="GEO code (ISO)" rules={[{required: true, len: 2}]}>
                    <Input maxLength={2}/>
                </Form.Item>
                <Form.Item name="offer_id" label="Keitaro offer ID"
                           rules={[{required: true, message: 'Select an offer'}]}>
                    <OfferAutocomplete placeholder="Search by id or name..."/>
                </Form.Item>
            </Form>
        </Modal>
    );
}