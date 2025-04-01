
import os
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Optional
from datetime import datetime
from pydantic import EmailStr
import requests

from database import get_db
from repositories.chat_repository import ChatRepository
from repositories.document_repository import DocumentRepository
import schemas

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)

@router.post(
	"/upload",
	status_code=status.HTTP_201_CREATED,
	response_model=schemas.Document,
)
def upload_document(
	document: schemas.Document,
	db=Depends(get_db),
):
	document_repository = DocumentRepository(db)
	uploaded_document = document_repository.insert_document(document)
	return uploaded_document
