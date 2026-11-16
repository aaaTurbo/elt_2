import { useEffect, useState } from 'react';
import { AutoComplete, Input } from 'antd';
import { useOfferSearch, KtOffer } from '../api/queries';

interface Props {
  value?: KtOffer | null;
  onChange?: (offer: KtOffer | null) => void;
  placeholder?: string;
}

const DEBOUNCE_MS = 250;

export default function OfferAutocomplete({ value, onChange, placeholder }: Props) {
  const [text, setText] = useState(value ? `${value.id} — ${value.name}` : '');
  const [debounced, setDebounced] = useState('');

  useEffect(() => {
    if (!value) setText('');
  }, [value]);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(text), DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [text]);

  const searchQuery = debounced.includes(' — ') ? '' : debounced;
  const { data: offers = [], isFetching } = useOfferSearch(searchQuery);

  const label = (o: KtOffer) => `${o.id} — ${o.name}`;

  return (
    <AutoComplete
      value={text}
      onChange={(v) => {
        setText(v);
        if (!v || !v.includes(' — ')) onChange?.(null);
      }}
      onSelect={(v: string) => {
        setText(v);
        const offer = offers.find((o) => label(o) === v);
        if (offer) onChange?.(offer);
      }}
      options={offers.map((o) => ({ value: label(o), label: label(o) }))}
      notFoundContent={isFetching ? 'Loading…' : 'No offers'}
      style={{ width: '100%' }}
    >
      <Input placeholder={placeholder ?? 'Search offer by id or name'} />
    </AutoComplete>
  );
}