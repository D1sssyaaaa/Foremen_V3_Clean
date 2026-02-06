from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
from datetime import date
from pydantic import BaseModel
from app.core.database import get_db
from app.models import User, CostObject, TimeEntry, RecentWorker
import json

router = APIRouter()

# --- Schemas ---
class WorkerDTO(BaseModel):
    id: int
    full_name: str
    avatar_url: Optional[str] = None

class ObjectDTO(BaseModel):
    id: int
    name: str

class InitResponse(BaseModel):
    user: WorkerDTO
    objects: List[ObjectDTO]

class TimeEntryCreate(BaseModel):
    worker_id: int
    hours: float

class SubmitRequest(BaseModel):
    date: date
    object_id: int
    entries: List[TimeEntryCreate]

# --- Endpoints ---

@router.get("/init", response_model=InitResponse)
async def init_miniapp(
    x_telegram_init_data: str = Header(None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize Mini App: Validate User & Load Context
    """
    # TODO: Implement actual validation of init_data using bot token
    # For now, we mock/bypass or assume a dev header for testing logic
    if not x_telegram_init_data:
         # raise HTTPException(status_code=401, detail="Missing init data")
         pass # Allow dev mode for now
    
    # Mock user for development if no valid auth (REMOVE IN PRODUCTION)
    # In real world, extract user_id from init_data
    # Use execute/scalar for AsyncSession
    foreman_res = await db.execute(select(User).where(User.role == "FOREMAN"))
    foreman = foreman_res.scalars().first()
    
    if not foreman:
         # Fallback to any user
         foreman_res = await db.execute(select(User))
         foreman = foreman_res.scalars().first()
    
    if not foreman:
        raise HTTPException(status_code=404, detail="User not found")

    # Get Objects available to this foreman (or all active objects)
    objects_res = await db.execute(select(CostObject).where(CostObject.is_active == True))
    objects = objects_res.scalars().all()

    return {
        "user": {
            "id": foreman.id,
            "full_name": foreman.full_name,
            "avatar_url": None
        },
        "objects": [{"id": o.id, "name": o.name} for o in objects]
    }

@router.get("/workers/recent", response_model=List[WorkerDTO])
async def get_recent_workers(
    foreman_id: int, # Should be inferred from Auth
    db: AsyncSession = Depends(get_db)
):
    """
    Get workers recently used by this foreman
    """
    # 1. Get from RecentWorkers table
    # Need to eager load worker? or join
    # AsyncSession lazy load is tricky, better to use join or selectinload
    from sqlalchemy.orm import selectinload
    
    query = (
        select(RecentWorker)
        .options(selectinload(RecentWorker.worker))
        .where(RecentWorker.foreman_id == foreman_id)
        .order_by(desc(RecentWorker.last_used_at))
        .limit(20)
    )
    result = await db.execute(query)
    recent_links = result.scalars().all()
    
    workers = []
    for link in recent_links:
        if link.worker:
            workers.append({
                "id": link.worker.id,
                "full_name": link.worker.full_name,
                "avatar_url": None
            })
            
    # 2. If empty, maybe return all users with role WORKER?
    if not workers:
         query_all = select(User).where(User.role == "WORKER").limit(50)
         res_all = await db.execute(query_all)
         all_workers = res_all.scalars().all()
         workers = [{"id": w.id, "full_name": w.full_name} for w in all_workers]

    return workers

@router.post("/timesheets/submit")
async def submit_timesheet(
    request: SubmitRequest,
    foreman_id: int = 1, # TODO: Extract from Auth
    db: AsyncSession = Depends(get_db)
):
    """
    Submit daily entries
    """
    submitted_entries = []
    
    for entry_data in request.entries:
        # Create Time Entry
        new_entry = TimeEntry(
            date=request.date,
            object_id=request.object_id,
            worker_id=entry_data.worker_id,
            foreman_id=foreman_id,
            hours=entry_data.hours,
            status="APPROVED"
        )
        db.add(new_entry)
        
        # Update/Create Recent Worker Link
        # Check existence
        query_recent = select(RecentWorker).where(
            RecentWorker.foreman_id == foreman_id,
            RecentWorker.worker_id == entry_data.worker_id
        )
        res_recent = await db.execute(query_recent)
        recent = res_recent.scalars().first()
        
        if recent:
            recent.last_used_at = func.now()
        else:
            new_recent = RecentWorker(foreman_id=foreman_id, worker_id=entry_data.worker_id)
            db.add(new_recent)
            
        submitted_entries.append(new_entry)
    
    await db.commit()
    return {"status": "ok", "count": len(submitted_entries)}

