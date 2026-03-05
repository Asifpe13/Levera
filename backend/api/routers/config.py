"""Public config: cities list for registration/settings."""
from fastapi import APIRouter
from config import ALL_CITIES

router = APIRouter()


@router.get("/cities")
def get_cities():
    return {"cities": ALL_CITIES}
