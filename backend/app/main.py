from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Generator
from urllib.parse import quote
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import BigInteger, JSON, Column, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

try:
    import boto3
except ImportError:
    boto3 = None


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'vehicle_records.db'}")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "").strip()
R2_BUCKET = os.getenv("R2_BUCKET", "").strip()
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "").strip()
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
R2_PUBLIC_BASE_URL = os.getenv("R2_PUBLIC_BASE_URL", "").strip().rstrip("/")

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class VehicleRecord(Base):
    __tablename__ = "vehicle_records"

    record_id = Column(String, primary_key=True)
    name = Column(String, nullable=False, default="")
    sales_photo_file_id = Column(String, nullable=False, default="")
    vehicle_photos = Column(JSON, nullable=False, default=list)
    selling_points = Column(String, nullable=False, default="")
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


Base.metadata.create_all(bind=engine)


class VehiclePhoto(BaseModel):
    key: str = ""
    index: str = ""
    label: str = ""
    fileID: str = ""


class VehicleRecordPayload(BaseModel):
    record_id: str = Field(min_length=1)
    name: str = ""
    sales_photo_file_id: str = ""
    vehicle_photos: list[VehiclePhoto] = Field(default_factory=list)
    selling_points: str = ""
    created_at: int | None = None
    updated_at: int | None = None


class FileDeletePayload(BaseModel):
    file_ids: list[str] = Field(default_factory=list)


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()


def now_ms() -> int:
    import time

    return int(time.time() * 1000)


def storage_key_from_file_id(file_id: str) -> str:
    if not file_id:
        return ""
    return file_id.removeprefix("api://").lstrip("/")


def validate_storage_key(storage_key: str) -> str:
    normalized = storage_key.replace("\\", "/").strip()
    parts = [part for part in normalized.split("/") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        raise HTTPException(status_code=400, detail="无效的文件路径")
    if not all(re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in parts):
        raise HTTPException(status_code=400, detail="文件路径包含不支持的字符")
    return "/".join(parts)


def get_r2_client():
    if not all((boto3, R2_ENDPOINT, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY)):
        return None
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def file_url(file_id: str) -> str:
    if not file_id:
        return ""
    if file_id.startswith("http://") or file_id.startswith("https://"):
        return file_id
    if R2_PUBLIC_BASE_URL:
        return f"{R2_PUBLIC_BASE_URL}/{storage_key_from_file_id(file_id)}"
    return f"{PUBLIC_BASE_URL}/api/files?file_id={quote(file_id, safe='')}"


def save_uploaded_file(upload: UploadFile, storage_key: str) -> str:
    storage_key = validate_storage_key(storage_key)
    r2_client = get_r2_client()
    if r2_client:
        r2_client.upload_fileobj(
            upload.file,
            R2_BUCKET,
            storage_key,
            ExtraArgs={"ContentType": upload.content_type or "application/octet-stream"},
        )
    else:
        target = UPLOAD_DIR / storage_key
        target.parent.mkdir(parents=True, exist_ok=True)
        upload.file.seek(0)
        with target.open("wb") as output:
            shutil.copyfileobj(upload.file, output)
    return f"api://{storage_key}"


def delete_storage_file(file_id: str) -> None:
    storage_key = storage_key_from_file_id(file_id)
    if not storage_key:
        return
    r2_client = get_r2_client()
    if r2_client:
        r2_client.delete_object(Bucket=R2_BUCKET, Key=storage_key)
        return
    target = UPLOAD_DIR / validate_storage_key(storage_key)
    if target.exists():
        target.unlink()


def serialize_record(record: VehicleRecord) -> dict:
    vehicle_photos = record.vehicle_photos or []
    return {
        "id": record.record_id,
        "cloudId": record.record_id,
        "cloudSynced": True,
        "name": record.name or "",
        "salesPhotoFileID": record.sales_photo_file_id or "",
        "salesPhoto": file_url(record.sales_photo_file_id or ""),
        "vehiclePhotos": [
            {
                **photo,
                "fileID": photo.get("fileID", ""),
                "path": file_url(photo.get("fileID", "")),
            }
            for photo in vehicle_photos
        ],
        "sellingPoints": record.selling_points or "",
        "createdAt": record.created_at,
        "updatedAt": record.updated_at,
    }


def collect_record_file_ids(record: VehicleRecord) -> list[str]:
    ids = [record.sales_photo_file_id or ""]
    ids.extend((photo or {}).get("fileID", "") for photo in (record.vehicle_photos or []))
    return [file_id for file_id in ids if file_id]


app = FastAPI(title="说车三岁 API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def service_info() -> dict:
    return {
        "service": "说车三岁 API",
        "ok": True,
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True, "storage": "r2" if get_r2_client() else "local"}


@app.get("/api/records")
def list_records(database: Session = Depends(get_db)) -> list[dict]:
    records = database.query(VehicleRecord).order_by(VehicleRecord.updated_at.desc()).all()
    return [serialize_record(record) for record in records]


@app.get("/api/records/{record_id}")
def get_record(record_id: str, database: Session = Depends(get_db)) -> dict:
    record = database.get(VehicleRecord, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="车辆档案不存在")
    return serialize_record(record)


@app.put("/api/records/{record_id}")
def upsert_record(
    record_id: str,
    payload: VehicleRecordPayload,
    database: Session = Depends(get_db),
) -> dict:
    if record_id != payload.record_id:
        raise HTTPException(status_code=400, detail="record_id 不一致")

    timestamp = now_ms()
    record = database.get(VehicleRecord, record_id)
    if not record:
        record = VehicleRecord(record_id=record_id, created_at=payload.created_at or timestamp)
        database.add(record)

    record.name = payload.name.strip()
    record.sales_photo_file_id = payload.sales_photo_file_id or ""
    record.vehicle_photos = [photo.model_dump() for photo in payload.vehicle_photos]
    record.selling_points = payload.selling_points.strip()
    record.created_at = record.created_at or payload.created_at or timestamp
    record.updated_at = payload.updated_at or timestamp
    database.commit()
    database.refresh(record)
    return serialize_record(record)


@app.delete("/api/records/{record_id}")
def delete_record(record_id: str, database: Session = Depends(get_db)) -> dict:
    record = database.get(VehicleRecord, record_id)
    if not record:
        return {"ok": True}

    for file_id in collect_record_file_ids(record):
        try:
            delete_storage_file(file_id)
        except Exception:
            pass

    database.delete(record)
    database.commit()
    return {"ok": True}


@app.post("/api/records/{record_id}/files")
def upload_record_file(
    record_id: str,
    file: UploadFile = File(...),
    storage_key: str = Form(...),
    database: Session = Depends(get_db),
) -> dict:
    if not database.get(VehicleRecord, record_id):
        raise HTTPException(status_code=404, detail="车辆档案不存在")
    if not storage_key.startswith(f"vehicles/{record_id}/"):
        raise HTTPException(status_code=400, detail="文件路径与车辆档案不匹配")
    try:
        file_id = save_uploaded_file(file, storage_key)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"文件上传失败：{error}") from error
    return {"fileID": file_id, "path": file_url(file_id)}


@app.delete("/api/files")
def delete_files(payload: FileDeletePayload) -> dict:
    errors: list[str] = []
    for file_id in payload.file_ids:
        try:
            delete_storage_file(file_id)
        except Exception as error:
            errors.append(str(error))
    if errors:
        raise HTTPException(status_code=502, detail="；".join(errors))
    return {"ok": True}


@app.get("/api/files")
def get_file(file_id: str) -> RedirectResponse:
    storage_key = validate_storage_key(storage_key_from_file_id(file_id))
    r2_client = get_r2_client()
    if r2_client:
        url = r2_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": R2_BUCKET, "Key": storage_key},
            ExpiresIn=3600,
        )
        return RedirectResponse(url)

    target = UPLOAD_DIR / storage_key
    if not target.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return RedirectResponse(f"{PUBLIC_BASE_URL}/media/{quote(storage_key, safe='/')}")


from fastapi.staticfiles import StaticFiles

app.mount("/media", StaticFiles(directory=str(UPLOAD_DIR)), name="media")
