"""Scan endpoints: upload a photo, list your history, view one scan."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import Predictor, get_current_user, get_predictor
from app.models import Scan, User
from app.schemas import ScanRead

router = APIRouter(prefix="/scans", tags=["scans"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("", response_model=ScanRead, status_code=status.HTTP_201_CREATED)
async def create_scan(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    predict: Predictor = Depends(get_predictor),
):
    """Analyze an uploaded skin photo and save the result to the user's history."""
    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload an image file.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image is too large (max 10 MB).",
        )

    try:
        label, confidence = await predict(image_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except RuntimeError as exc:  # model service down / not woken
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    scan = Scan(
        user_id=current_user.id,
        filename=file.filename or "upload",
        predicted_label=label,
        confidence=confidence,
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    return scan


@router.get("", response_model=list[ScanRead])
async def list_scans(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's scans, newest first."""
    result = await db.scalars(
        select(Scan).where(Scan.user_id == current_user.id).order_by(Scan.id.desc())
    )
    return list(result)


@router.get("/{scan_id}", response_model=ScanRead)
async def get_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a single scan, but only if it belongs to the current user."""
    scan = await db.get(Scan, scan_id)
    if scan is None or scan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found."
        )
    return scan
