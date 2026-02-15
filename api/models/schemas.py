"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_admin: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# Password Reset Schemas
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

# Simulation Schemas
class SimulationEmailResponse(BaseModel):
    id: int
    sender: str
    subject: str
    date: str
    content: str
    is_spam: bool
    is_predefined: bool
    
    class Config:
        from_attributes = True

class SimulationResponseCreate(BaseModel):
    email_id: int
    is_spam_actual: bool
    user_response: bool
    user_explanation: Optional[str] = None

class SimulationResponseData(BaseModel):
    id: int
    email_id: int
    is_spam_actual: bool
    user_response: bool
    user_explanation: Optional[str]
    ai_feedback: Optional[str]
    score: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Simulation Session Schemas
class SimulationSessionCreate(BaseModel):
    session_id: str

class SimulationSessionResponse(BaseModel):
    id: int
    session_id: str
    phase1_completed: bool
    phase2_completed: bool
    phase1_score: Optional[int]
    phase2_score: Optional[int]
    avg_phase2_score: Optional[float]
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Analysis Schemas
class AnalysisData(BaseModel):
    total_responses: int
    correct_responses: int
    accuracy: float
    phase1_score: Optional[int]
    phase2_score: Optional[int]
    avg_ai_score: Optional[float]
    
class SessionHistory(BaseModel):
    sessions: list[SimulationSessionResponse]
    total_sessions: int
