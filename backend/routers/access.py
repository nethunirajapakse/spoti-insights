# backend/routers/access.py
import os
import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import resend
from backend.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="",
    tags=["Access Requests"]
)

class AccessRequest(BaseModel):
    email: EmailStr

@router.post("/request-access", status_code=status.HTTP_200_OK)
async def request_access(payload: AccessRequest):
    if not settings.resend_api_key:
        logger.error("Resend API key missing from environment variables.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email service configuration missing on server."
        )
        
    try:
        params = {
            "from": "SpotiInsights <onboarding@resend.dev>",  # Replace with a verified domain if you have one
            "to": [settings.destination_email],
            "subject": "New Spoti-Insights Access Request",
            "html": f"""
                <div style="font-family: sans-serif; padding: 20px; color: #333;">
                    <h2>New Access Request</h2>
                    <p>A user has requested access to Spoti Insights via the allowlist form.</p>
                    <p><strong>User Email:</strong> <a href="mailto:{payload.email}">{payload.email}</a></p>
                </div>
            """
        }
        
        email = resend.Emails.send(params)
        return {"success": True, "message": "Request sent successfully!", "id": email.get("id")}
        
    except Exception as e:
        logger.exception("Failed to send access request email via Resend.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
