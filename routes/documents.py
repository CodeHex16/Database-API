import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import EmailStr
import requests
from motor.motor_asyncio import AsyncIOMotorDatabase

from database import get_db
from repositories.document_repository import DocumentRepository
import schemas

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


def get_document_repository(db: AsyncIOMotorDatabase = Depends(get_db)):
    return DocumentRepository(db)


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Document,
)
async def upload_document(
    document: schemas.Document,
    document_repository=Depends(get_document_repository),
):
    print("Document to upload:", type(document), "content:", document)

    # document_dict = document.model_dump()
    # print("Document dict:", document_dict)

    uploaded_document = await document_repository.insert_document(document)
    return uploaded_document
