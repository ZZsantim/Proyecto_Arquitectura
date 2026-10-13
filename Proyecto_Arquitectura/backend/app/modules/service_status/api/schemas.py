from pydantic import BaseModel, ConfigDict, Field


class PublicServiceStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    message: str
    vehicle_type: str | None = None
    serial_number: str | None = None
    order_code: str | None = None


class PublicLookupRequest(BaseModel):
    tracking_code: str = Field(min_length=6, max_length=32)
