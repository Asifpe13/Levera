"""User profile: get, update."""
from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_db, get_current_user_email
from api.schemas import UserResponse, UserUpdateRequest, user_dict_to_response
from database.db import DatabaseManager

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_me(
    email: str = Depends(get_current_user_email),
    db: DatabaseManager = Depends(get_db),
):
    user = db.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_dict_to_response(user)


@router.put("/me", response_model=UserResponse)
def update_me(
    body: UserUpdateRequest,
    email: str = Depends(get_current_user_email),
    db: DatabaseManager = Depends(get_db),
):
    user = db.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update = {}
    if body.name is not None:
        update["name"] = body.name
    if body.target_cities is not None:
        update["target_cities"] = body.target_cities
    if body.search_type is not None:
        update["search_type"] = body.search_type
    if body.equity is not None:
        update["equity"] = body.equity
    if body.monthly_income is not None:
        update["monthly_income"] = body.monthly_income
    if body.room_range_min is not None:
        update["room_range_min"] = body.room_range_min
    if body.room_range_max is not None:
        update["room_range_max"] = body.room_range_max
    if body.max_price is not None:
        update["max_price"] = body.max_price if body.max_price > 0 else None
    if body.max_repayment_ratio is not None:
        update["max_repayment_ratio"] = body.max_repayment_ratio
    if body.rent_room_range_min is not None:
        update["rent_room_range_min"] = body.rent_room_range_min
    if body.rent_room_range_max is not None:
        update["rent_room_range_max"] = body.rent_room_range_max
    if body.max_rent is not None:
        update["max_rent"] = body.max_rent if body.max_rent > 0 else None
    if body.extra_preferences is not None:
        update["extra_preferences"] = body.extra_preferences
    merged = {**user, **update}
    db.upsert_user(merged)
    updated = db.get_user_by_email(email)
    return user_dict_to_response(updated)
