import uuid
from datetime import UTC, datetime
from random import choice

from database import get_session
from models.prediction import (GetPredictionResponse, PostPredictionRequest,
                               Prediction)
from models.user import User, UserRole
from security.rbac import RoleChecker
from sqlmodel import Session, select

from fastapi import APIRouter, Depends, HTTPException, status

prediction_router = APIRouter(prefix="/predict", tags=["prediction"])


allow_create_prediction = RoleChecker(
    [UserRole.ADMIN.name.lower(), UserRole.DEFAULT.name.lower()]
)
allow_read_prediction = RoleChecker(
    [UserRole.ADMIN.name.lower(), UserRole.DEFAULT.name.lower()]
)

user_intentions = [
    "Refund request",
    "Software bug",
    "Network problem",
    "Account access",
]


@prediction_router.post(
    "",
    response_model=GetPredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def predict_intention(
    text: PostPredictionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(allow_create_prediction),
):
    user_intent = Prediction(
        owner_id=current_user.user_id,
        text=text.text,
        intention=choice(user_intentions),
        created_at=datetime.now(UTC),
    )

    session.add(user_intent)
    session.commit()
    session.refresh(user_intent)

    return user_intent


@prediction_router.get(
    "",
    response_model=list[GetPredictionResponse],
)
async def get_user_predictions(
    session: Session = Depends(get_session),
    current_user: User = Depends(allow_read_prediction),
):
    predictions = session.exec(
        select(Prediction).where(Prediction.owner_id == current_user.user_id)
    )

    return predictions


@prediction_router.get("/{id}", response_model=GetPredictionResponse)
async def get_user_prediction_by_id(
    id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(allow_read_prediction),
):
    prediction = session.exec(
        select(Prediction).where(Prediction.prediction_id == id)
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Could not find prediction"
        )

    if prediction.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden."
        )

    return prediction
