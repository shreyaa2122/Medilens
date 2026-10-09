import uuid

from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_app_settings, get_current_user, get_db, get_storage
from app.core.config import Settings
from app.db.models import User
from app.schemas.common import ApiResponse
from app.schemas.document import DocumentOut
from app.services import document_service
from app.services.storage_service import StorageService

router = APIRouter(tags=["documents"])


@router.post("/documents/upload", response_model=ApiResponse[DocumentOut], status_code=201)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
    settings: Settings = Depends(get_app_settings),
    user: User = Depends(get_current_user),
) -> ApiResponse[DocumentOut]:
    # Read one byte more than the limit so we can tell "too large" from "exactly at the limit".
    content = file.file.read(settings.max_upload_bytes + 1)
    document = document_service.register_upload(
        db, storage, user, file.filename, content, settings.max_upload_bytes
    )
    return ApiResponse(data=DocumentOut.model_validate(document))


@router.get("/documents", response_model=ApiResponse[list[DocumentOut]])
def list_documents(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> ApiResponse[list[DocumentOut]]:
    documents = document_service.list_documents(db, user)
    return ApiResponse(data=[DocumentOut.model_validate(d) for d in documents])


@router.get("/documents/{document_id}", response_model=ApiResponse[DocumentOut])
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ApiResponse[DocumentOut]:
    document = document_service.get_document(db, user, document_id)
    return ApiResponse(data=DocumentOut.model_validate(document))


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage),
    user: User = Depends(get_current_user),
) -> Response:
    document = document_service.get_document(db, user, document_id)
    document_service.delete_document(db, storage, document)
    return Response(status_code=204)
