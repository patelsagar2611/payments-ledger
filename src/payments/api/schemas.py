from pydantic import BaseModel, ConfigDict, StrictInt

from payments.domain.money import Currency


class MoneyModel(BaseModel):
    """An amount in minor units with its currency, as sent over HTTP.

    StrictInt rejects 100.0, "100" and true instead of coercing them to 100.
    """

    model_config = ConfigDict(from_attributes=True)

    amount_minor: StrictInt
    currency: Currency
