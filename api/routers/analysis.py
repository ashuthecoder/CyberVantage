"""
Analysis routes - performance analytics
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from api.core.database import get_db
from api.core.auth import get_current_user
from api.models.database import User, SimulationResponse, SimulationSession
from api.models.schemas import AnalysisData, SessionHistory

router = APIRouter()

@router.get("/performance", response_model=AnalysisData)
async def get_performance_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user performance analysis"""
    
    # Get all responses for user
    responses = db.query(SimulationResponse).filter(
        SimulationResponse.user_id == current_user.id
    ).all()
    
    total_responses = len(responses)
    correct_responses = sum(1 for r in responses if r.is_spam_actual == r.user_response)
    accuracy = (correct_responses / total_responses * 100) if total_responses > 0 else 0
    
    # Get latest session scores
    latest_session = db.query(SimulationSession).filter(
        SimulationSession.user_id == current_user.id
    ).order_by(SimulationSession.started_at.desc()).first()
    
    return {
        "total_responses": total_responses,
        "correct_responses": correct_responses,
        "accuracy": round(accuracy, 2),
        "phase1_score": latest_session.phase1_score if latest_session else None,
        "phase2_score": latest_session.phase2_score if latest_session else None,
        "avg_ai_score": latest_session.avg_phase2_score if latest_session else None
    }

@router.get("/history", response_model=SessionHistory)
async def get_session_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's session history"""
    
    sessions = db.query(SimulationSession).filter(
        SimulationSession.user_id == current_user.id
    ).order_by(SimulationSession.started_at.desc()).limit(50).all()
    
    return {
        "sessions": sessions,
        "total_sessions": len(sessions)
    }
