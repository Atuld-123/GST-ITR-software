import hashlib
import uuid
from pathlib import PurePath
from urllib.parse import quote

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db import get_session
from app.models import AuditLog, Client, EncryptedDocument, OrganizationMember, Role, User
from app.security import current_user

router = APIRouter(prefix="/api/v1/organizations/{organization_id}/documents", tags=["documents"])
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}


class DocumentClientLink(BaseModel):
    client_id: uuid.UUID


def document_cipher() -> Fernet:
    if not settings.documents_encryption_key:
        raise HTTPException(status_code=503, detail="Encrypted document storage is not configured")
    try:
        return Fernet(settings.documents_encryption_key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as error:
        raise HTTPException(status_code=503, detail="Document encryption key is invalid") from error


async def check_document_access(organization_id: uuid.UUID, user: User, session: AsyncSession, write: bool = False) -> None:
    role = await session.scalar(select(Role).join(OrganizationMember, OrganizationMember.role_id == Role.id).where(OrganizationMember.organization_id == organization_id, OrganizationMember.user_id == user.id))
    permission = "documents:write" if write else "documents:read"
    if role is None or not any(grant == permission or grant == "documents:*" for grant in role.permissions):
        raise HTTPException(status_code=403, detail="Document access denied")


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(organization_id: uuid.UUID, file: UploadFile = File(...), client_id: uuid.UUID | None = Form(default=None), service_case_id: uuid.UUID | None = Form(default=None), document_label: str | None = Form(default=None, max_length=200), user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await check_document_access(organization_id, user, session, write=True)
    if client_id is not None:
        client = await session.scalar(select(Client.id).where(Client.id == client_id, Client.organization_id == organization_id))
        if client is None:
            raise HTTPException(status_code=404, detail="Client not found")
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Only PDF, JPEG and PNG documents are accepted")
    content = await file.read(MAX_DOCUMENT_BYTES + 1)
    if not content or len(content) > MAX_DOCUMENT_BYTES:
        raise HTTPException(status_code=413, detail="Document must be between 1 byte and 10 MB")
    signatures = {"application/pdf": content.startswith(b"%PDF-"), "image/jpeg": content.startswith(b"\xff\xd8\xff"), "image/png": content.startswith(b"\x89PNG\r\n\x1a\n")}
    if not signatures.get(file.content_type, False):
        raise HTTPException(status_code=415, detail="The file content does not match its declared type")
    cipher = document_cipher()
    record = EncryptedDocument(organization_id=organization_id, client_id=client_id, service_case_id=service_case_id, document_label=document_label, uploaded_by=user.id, filename=PurePath(file.filename or "document").name[:255], content_type=file.content_type, ciphertext=cipher.encrypt(content), sha256=hashlib.sha256(content).hexdigest())
    session.add(record); await session.flush()
    session.add(AuditLog(organization_id=organization_id,actor_id=user.id,action="document.uploaded",entity_type="encrypted_document",entity_id=record.id,metadata_={"content_type":record.content_type,"size_bytes":len(content),"client_id":str(client_id) if client_id else None,"service_case_id":str(service_case_id) if service_case_id else None,"document_label":document_label}))
    await session.commit()
    return {"id":str(record.id),"client_id":str(record.client_id) if record.client_id else None,"service_case_id":str(record.service_case_id) if record.service_case_id else None,"document_label":record.document_label,"filename":record.filename,"content_type":record.content_type,"size_bytes":len(content),"encrypted_at_rest":True,"status":"stored"}


@router.get("")
async def list_documents(organization_id: uuid.UUID, client_id: uuid.UUID | None = None, service_case_id: uuid.UUID | None = None, unassigned: bool = False, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[dict]:
    await check_document_access(organization_id, user, session)
    query = select(EncryptedDocument).where(EncryptedDocument.organization_id == organization_id)
    if client_id is not None:
        client = await session.scalar(select(Client.id).where(Client.id == client_id, Client.organization_id == organization_id))
        if client is None:
            raise HTTPException(status_code=404, detail="Client not found")
        query = query.where(EncryptedDocument.client_id == client_id)
    elif unassigned:
        query = query.where(EncryptedDocument.client_id.is_(None))
    if service_case_id is not None:
        query = query.where(EncryptedDocument.service_case_id == service_case_id)
    records = (await session.scalars(query.order_by(EncryptedDocument.created_at.desc()))).all()
    return [{"id":str(d.id),"client_id":str(d.client_id) if d.client_id else None,"service_case_id":str(d.service_case_id) if d.service_case_id else None,"document_label":d.document_label,"filename":d.filename,"content_type":d.content_type,"sha256":d.sha256,"created_at":d.created_at.isoformat(),"status":"stored","encrypted_at_rest":True} for d in records]


@router.post("/{document_id}/link")
async def link_document_to_client(organization_id: uuid.UUID, document_id: uuid.UUID, payload: DocumentClientLink, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    await check_document_access(organization_id, user, session, write=True)
    client = await session.scalar(select(Client.id).where(Client.id == payload.client_id, Client.organization_id == organization_id))
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    record = await session.scalar(select(EncryptedDocument).where(EncryptedDocument.id == document_id, EncryptedDocument.organization_id == organization_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if record.client_id not in (None, payload.client_id):
        raise HTTPException(status_code=409, detail="This document is already linked to another client")
    record.client_id = payload.client_id
    session.add(AuditLog(organization_id=organization_id, actor_id=user.id, action="document.linked_to_client", entity_type="encrypted_document", entity_id=record.id, metadata_={"client_id":str(payload.client_id)}))
    await session.commit()
    return {"id":str(record.id),"client_id":str(record.client_id),"status":"stored"}


@router.get("/{document_id}/download")
async def download_document(organization_id: uuid.UUID, document_id: uuid.UUID, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> Response:
    await check_document_access(organization_id, user, session)
    record = await session.scalar(select(EncryptedDocument).where(EncryptedDocument.id == document_id, EncryptedDocument.organization_id == organization_id))
    if record is None: raise HTTPException(status_code=404, detail="Document not found")
    try: cleartext = document_cipher().decrypt(record.ciphertext)
    except InvalidToken as error: raise HTTPException(status_code=500, detail="Document could not be decrypted") from error
    session.add(AuditLog(organization_id=organization_id,actor_id=user.id,action="document.downloaded",entity_type="encrypted_document",entity_id=record.id,metadata_={}))
    await session.commit()
    safe_filename = PurePath(record.filename).name
    return Response(cleartext, media_type=record.content_type, headers={"Content-Disposition":f"attachment; filename*=UTF-8''{quote(safe_filename)}",'X-Content-Type-Options':'nosniff'})
