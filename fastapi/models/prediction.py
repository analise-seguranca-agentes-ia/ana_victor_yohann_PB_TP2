import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field, SQLModel


class Prediction(SQLModel, table=True):
    prediction_id: uuid.UUID = Field(
        default_factory=uuid.uuid4, unique=True, primary_key=True
    )
    owner_id: uuid.UUID = Field(foreign_key="user.user_id", ondelete="CASCADE")
    text: str
    intention: str
    created_at: datetime


class PostPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str


class GetPredictionResponse(BaseModel):
    prediction_id: uuid.UUID
    text: str
    intention: str
