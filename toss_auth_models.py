"""
Pydantic models for Toss Cert Authentication API.
Based on https://developers-apps-in-toss.toss.im/tossauth/develop.md
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


# --- Request Models ---

class TossAuthInitRequest(BaseModel):
    """Request to initiate Toss authentication with authorization code."""
    authorizationCode: str = Field(..., description="Authorization code from appLogin()")


# --- Response Models from Toss API ---

class TossAccessTokenResponse(BaseModel):
    """OAuth2 access token response from Toss."""
    access_token: str = Field(..., description="Bearer token for API calls")
    scope: str = Field(..., description="Granted scope (e.g., 'ca')")
    token_type: str = Field(..., description="Token type, always 'Bearer'")
    expires_in: int = Field(..., description="Token expiry in seconds")


class TossAuthRequestSuccess(BaseModel):
    """Success response from auth request API."""
    txId: str = Field(..., description="Transaction ID for this auth request")
    appScheme: Optional[str] = Field(None, description="App scheme for Toss app")
    androidAppUri: Optional[str] = Field(None, description="Android intent URI")
    iosAppUri: Optional[str] = Field(None, description="iOS universal link")
    requestedDt: str = Field(..., description="Request timestamp in ISO 8601")


class TossAuthError(BaseModel):
    """Error response from Toss API."""
    errorType: int = Field(..., description="Error type code")
    errorCode: str = Field(..., description="Error code (e.g., CE1000)")
    reason: str = Field(..., description="Error message")
    data: dict = Field(default_factory=dict, description="Additional error data")
    title: Optional[str] = Field(None, description="Error title")


class TossAuthRequestResponse(BaseModel):
    """Complete auth request response."""
    resultType: Literal["SUCCESS", "FAIL"] = Field(..., description="Result status")
    success: Optional[TossAuthRequestSuccess] = Field(None, description="Success data")
    error: Optional[TossAuthError] = Field(None, description="Error data")


class TossAuthStatusSuccess(BaseModel):
    """Auth status success response."""
    txId: str = Field(..., description="Transaction ID")
    status: Literal["REQUESTED", "IN_PROGRESS", "COMPLETED", "EXPIRED"] = Field(
        ..., description="Current auth status"
    )
    requestedDt: str = Field(..., description="Request timestamp")


class TossAuthStatusResponse(BaseModel):
    """Auth status check response."""
    resultType: Literal["SUCCESS", "FAIL"] = Field(..., description="Result status")
    success: Optional[TossAuthStatusSuccess] = Field(None, description="Success data")
    error: Optional[TossAuthError] = Field(None, description="Error data")


class TossPersonalData(BaseModel):
    """Encrypted personal data from auth result."""
    ci: str = Field(..., description="Encrypted CI (Connecting Information)")
    name: str = Field(..., description="Encrypted user name")
    birthday: str = Field(..., description="Encrypted birthday (YYYYMMDD)")
    gender: str = Field(..., description="Encrypted gender (MALE/FEMALE)")
    nationality: str = Field(..., description="Encrypted nationality (LOCAL/FOREIGNER)")
    ci2: Optional[str] = Field(None, description="Reserved field, always null")
    di: str = Field(..., description="Encrypted DI (Duplication Information)")
    ciUpdate: Optional[str] = Field(None, description="Reserved field, always null")
    ageGroup: str = Field(..., description="Encrypted age group (ADULT/MINOR)")


class TossAuthResultSuccess(BaseModel):
    """Auth result success response with user data."""
    txId: str = Field(..., description="Transaction ID")
    status: Literal["COMPLETED"] = Field(..., description="Status, always COMPLETED")
    userIdentifier: Optional[str] = Field(None, description="Reserved, always null")
    userCiToken: Optional[str] = Field(None, description="Reserved, always null")
    signature: str = Field(..., description="User's digital signature (Base64 DER)")
    randomValue: Optional[str] = Field(None, description="Reserved, always null")
    completedDt: str = Field(..., description="Completion timestamp")
    requestedDt: str = Field(..., description="Request timestamp")
    personalData: TossPersonalData = Field(..., description="Encrypted personal data")


class TossAuthResultResponse(BaseModel):
    """Auth result response."""
    resultType: Literal["SUCCESS", "FAIL"] = Field(..., description="Result status")
    success: Optional[TossAuthResultSuccess] = Field(None, description="Success data")
    error: Optional[TossAuthError] = Field(None, description="Error data")


# --- Decrypted User Data Models ---

class DecryptedUserData(BaseModel):
    """Decrypted user data (simplified for now - only name)."""
    name: str = Field(..., description="User name")
    # TODO: Add other fields when proper decryption is implemented
    # ci: str = Field(..., description="User CI (Connecting Information)")
    # birthday: str = Field(..., description="Birthday in YYYYMMDD format")
    # gender: Literal["MALE", "FEMALE"] = Field(..., description="User gender")
    # nationality: Literal["LOCAL", "FOREIGNER"] = Field(..., description="Nationality")
    # di: str = Field(..., description="User DI (Duplication Information)")
    # ageGroup: Literal["ADULT", "MINOR"] = Field(..., description="Age group")


# --- App Response Models ---

class TossAuthResponse(BaseModel):
    """Response sent to mobile app after successful authentication."""
    txId: str = Field(..., description="Transaction ID")
    userData: DecryptedUserData = Field(..., description="Decrypted user information")
    signature: str = Field(..., description="Digital signature")
    completedAt: str = Field(..., description="Completion timestamp")
