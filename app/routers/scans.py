"""Scan endpoints: upload a photo (processed in the background), list, view."""
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_db
from app.deps import Predictor, get_current_user, get_predictor
from app.models import Scan, User
from app.schemas import ScanRead

router = APIRouter(prefix="/scans", tags=["scans"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


async def process_scan(scan_id: int, image_bytes: bytes, predict: Predictor) -> None:
    """Run the (slow) prediction in the background and save the outcome.

    Uses its own database session because the request that created the scan
    has already returned and closed its session.
    """
    async with AsyncSessionLocal() as db:
        scan = await db.get(Scan, scan_id)
        if scan is None:
            return
        try:
            label, confidence = await predict(image_bytes)
            scan.predicted_label = label
            scan.confidence = confidence
            scan.status = "done"
        except Exception as exc:  # model down, waking too slowly, etc.
            scan.status = "failed"
            scan.error = str(exc)[:500]
        await db.commit()


@router.post("", response_model=ScanRead, status_code=status.HTTP_202_ACCEPTED)
async def create_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    predict: Predictor = Depends(get_predictor),
):
    """Accept a skin photo and start analyzing it. Returns immediately with a
    'processing' scan; poll GET /scans/{id} for the result."""
    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload an image file.",
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The image is empty."
        )
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image is too large (max 10 MB).",
        )

    scan = Scan(
        user_id=current_user.id,
        filename=file.filename or "upload",
        status="processing",
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    # Hand the slow model call off to a background task and return right away.
    background_tasks.add_task(process_scan, scan.id, image_bytes, predict)
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
    """Return a single scan (with its current status), if it belongs to you."""
    scan = await db.get(Scan, scan_id)
    if scan is None or scan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found."
        )
    return scan
