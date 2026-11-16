from decimal import Decimal, ROUND_DOWN
from app.models import StreamOffer
from app.exceptions import ValidationError

TWO = Decimal("0.01")
HUNDRED = Decimal("100")


class WeightAllocator:
    """
    Пересчитывает веса офферов в потоке.

    Инварианты:
      * is_deleted_in_kt=True офферы не участвуют в распределении.
      * Сумма весов активных офферов = 100.
      * is_weight_fixed=True офферы сохраняют вес; Σfixed ≤ 100.
      * Остаток (100 - Σfixed) распределяется пропорционально среди free-офферов.
      * При добавлении нового free-оффера он получает равную долю,
        остальные free пересчитываются пропорционально остатку.
    """

    def recalculate(self, offers: list[StreamOffer]) -> None:

        active = [o for o in offers if not o.is_deleted_in_kt]
        fixed = [o for o in active if o.is_weight_fixed]
        free = [o for o in active if not o.is_weight_fixed]

        fixed_sum = sum((o.weight for o in fixed), Decimal("0"))
        if fixed_sum > HUNDRED:
            raise ValidationError(
                f"Sum of fixed weights ({fixed_sum}) exceeds 100%"
            )
        remaining = HUNDRED - fixed_sum

        if not free:
            if remaining > Decimal("0.01"):
                raise ValidationError(
                    "No free offers to allocate the remaining weight. "
                    "Either unfix some offers or add new ones."
                )
            self._normalize(fixed)
            return

        free_sum = sum((o.weight for o in free), Decimal("0"))
        if free_sum == 0:
            share = remaining / len(free)
            for o in free:
                o.weight = share
        else:
            for o in free:
                o.weight = (o.weight / free_sum) * remaining

        self._normalize(fixed + free)

    def allocate_for_new(
        self, offers: list[StreamOffer], new_offer: StreamOffer
    ) -> None:

        active_others = [
            o for o in offers
            if o is not new_offer and not o.is_deleted_in_kt
        ]
        fixed = [o for o in active_others if o.is_weight_fixed]
        free = [o for o in active_others if not o.is_weight_fixed]

        fixed_sum = sum((o.weight for o in fixed), Decimal("0"))
        if fixed_sum > HUNDRED:
            raise ValidationError("Sum of fixed weights exceeds 100%")
        remaining = HUNDRED - fixed_sum

        new_share = remaining / Decimal(len(free) + 1)
        new_offer.weight = new_share
        rest = remaining - new_share

        if free:
            free_sum = sum((o.weight for o in free), Decimal("0"))
            if free_sum == 0:
                share = rest / len(free)
                for o in free:
                    o.weight = share
            else:
                for o in free:
                    o.weight = (o.weight / free_sum) * rest

        self._normalize(fixed + free + [new_offer])

    def _normalize(self, active: list[StreamOffer]) -> None:

        total = Decimal("0")
        for i, o in enumerate(active):
            if i == len(active) - 1:
                o.weight = (HUNDRED - total).quantize(TWO)
            else:
                w = o.weight.quantize(TWO, rounding=ROUND_DOWN)
                o.weight = w
                total += w
