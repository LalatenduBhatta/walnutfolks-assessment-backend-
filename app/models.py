# app/models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class TransactionStatus(str, Enum):
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"

class WebhookPayload(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction identifier")
    source_account: str = Field(..., description="Source account identifier")
    destination_account: str = Field(..., description="Destination account identifier")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field("INR", description="Currency code")

class TransactionResponse(BaseModel):
    transaction_id: str
    source_account: str
    destination_account: str
    amount: float
    currency: str
    status: TransactionStatus
    created_at: datetime
    processed_at: Optional[datetime] = None

class HealthResponse(BaseModel):
    status: str
    current_time: datetime
    service: str = "WalnutFolks Transaction Service"
    version: str = "1.0.0"

class ChartDataItem(BaseModel):
    name: str
    value: Optional[float] = None
    duration: Optional[float] = None

class ChartData(BaseModel):
    callDuration: List[ChartDataItem]
    sadPath: List[ChartDataItem]

class UserChartRequest(BaseModel):
    email: str
    chartData: Optional[ChartData] = None
    action: str  # "save" or "get"

class UserChartResponse(BaseModel):
    success: bool
    chartData: Optional[ChartData] = None
    message: Optional[str] = None
    lastUpdated: Optional[datetime] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None