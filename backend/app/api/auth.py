"""
NetraLink AI: Authentication & RBAC Router
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str = "investigator_singh"
    password: str = "password"
    role: str = "Senior Investigator"


@router.post("/login")
def login(payload: LoginRequest):
    return {
        "status": "authenticated",
        "token": "ntl_token_sec_89f0a2c",
        "user": {
            "name": "Insp. A. K. Singh",
            "badge_number": "MP-CID-0491",
            "role": payload.role,
            "agency": "Special Crime & Intelligence Branch",
            "jurisdiction": "Central Zone (MP & Maharashtra)",
            "clearance_level": "LEVEL 4 (NATIONAL INTELLIGENCE ACCESS)"
        }
    }


@router.get("/me")
def get_current_user():
    return {
        "name": "Insp. A. K. Singh",
        "badge_number": "MP-CID-0491",
        "role": "Senior Investigator",
        "agency": "Special Crime & Intelligence Branch",
        "clearance_level": "LEVEL 4"
    }
