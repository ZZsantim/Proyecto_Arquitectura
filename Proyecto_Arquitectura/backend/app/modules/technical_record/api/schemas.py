from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ObservationCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class BatteryUpdate(BaseModel):
    voltage: str | None = Field(default=None, max_length=80)
    amperage: str | None = Field(default=None, max_length=80)
    capacity: str | None = Field(default=None, max_length=80)
    cell_type: str | None = Field(default=None, max_length=120)
    technical_notes: str | None = Field(default=None, max_length=4000)


class ControllerUpdate(BaseModel):
    model: str | None = Field(default=None, max_length=120)
    firmware: str | None = Field(default=None, max_length=120)
    modifications: str | None = Field(default=None, max_length=4000)


class TechnicalSpecificationsUpdate(BaseModel):
    battery: BatteryUpdate | None
    controller: ControllerUpdate | None


class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content: str
    author_username: str
    created_at: datetime


class BatteryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    voltage: str | None
    amperage: str | None
    capacity: str | None
    cell_type: str | None
    technical_notes: str | None


class ControllerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model: str | None
    firmware: str | None
    modifications: str | None


class RepairResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    service_date: date
    summary: str
    technical_details: str | None


class TechnicalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    serial_number: str
    vehicle_type: str
    make_model: str | None
    battery: BatteryResponse | None
    controller: ControllerResponse | None
    repairs: list[RepairResponse]
    observations: list[ObservationResponse]
