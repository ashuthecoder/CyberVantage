"""
Simulation routes - phishing email simulation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from api.core.database import get_db
from api.core.auth import get_current_user
from api.models.database import User, SimulationEmail, SimulationResponse, SimulationSession
from api.models.schemas import (
    SimulationEmailResponse, SimulationResponseCreate,
    SimulationResponseData, SimulationSessionCreate, SimulationSessionResponse
)

router = APIRouter()

@router.get("/emails", response_model=List[SimulationEmailResponse])
async def get_simulation_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available simulation emails"""
    emails = db.query(SimulationEmail).filter(SimulationEmail.is_predefined == True).limit(10).all()
    return emails

@router.post("/responses", response_model=SimulationResponseData, status_code=status.HTTP_201_CREATED)
async def submit_simulation_response(
    response_data: SimulationResponseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a simulation response"""
    
    new_response = SimulationResponse(
        user_id=current_user.id,
        email_id=response_data.email_id,
        is_spam_actual=response_data.is_spam_actual,
        user_response=response_data.user_response,
        user_explanation=response_data.user_explanation
    )
    
    db.add(new_response)
    db.commit()
    db.refresh(new_response)
    
    return new_response

@router.get("/sessions", response_model=List[SimulationSessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's simulation sessions"""
    sessions = db.query(SimulationSession).filter(
        SimulationSession.user_id == current_user.id
    ).order_by(SimulationSession.started_at.desc()).all()
    
    return sessions

@router.post("/sessions", response_model=SimulationSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_simulation_session(
    session_data: SimulationSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new simulation session"""
    
    new_session = SimulationSession(
        user_id=current_user.id,
        session_id=session_data.session_id
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session
