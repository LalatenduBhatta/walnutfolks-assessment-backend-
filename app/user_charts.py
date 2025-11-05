# app/routes/user_charts.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
import re

router = APIRouter()

# Pydantic models for request/response
class ChartData(BaseModel):
    callDuration: Dict[str, Any]
    sadPath: Dict[str, Any]

class UserChartRequest(BaseModel):
    email: str
    chartData: Optional[ChartData] = None
    action: str

    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower().strip()

    @validator('action')
    def validate_action(cls, v):
        if v not in ['save', 'get']:
            raise ValueError('Action must be "save" or "get"')
        return v

    @validator('chartData', always=True)
    def validate_chart_data(cls, v, values):
        if 'action' in values and values['action'] == 'save' and v is None:
            raise ValueError('Chart data is required for save action')
        return v

class UserChartResponse(BaseModel):
    success: Optional[bool] = None
    message: Optional[str] = None
    chartData: Optional[Dict[str, Any]] = None
    lastUpdated: Optional[str] = None

# In-memory store for tracking processing transactions (for idempotency)
user_charts_db = {}

@router.post("/user-charts", response_model=UserChartResponse)
async def handle_user_charts(request: UserChartRequest):
    try:
        email = request.email

        if request.action == 'save':
            if not request.chartData:
                raise HTTPException(
                    status_code=400,
                    detail="Chart data is required for save action"
                )

            # Validate chart data structure
            if not request.chartData.callDuration or not request.chartData.sadPath:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid chart data structure"
                )

            # Save or update chart data (mock database operation)
            user_charts_db[email] = {
                'chart_data': request.chartData.dict(),
                'updated_at': '2024-01-01T00:00:00Z'
            }

            return UserChartResponse(
                success=True,
                message="Chart data saved successfully"
            )

        elif request.action == 'get':
            # Get existing chart data
            user_data = user_charts_db.get(email)
            
            if user_data:
                return UserChartResponse(
                    chartData=user_data['chart_data'],
                    lastUpdated=user_data['updated_at']
                )
            else:
                return UserChartResponse(
                    chartData=None,
                    lastUpdated=None
                )

    except HTTPException:
        raise
    except Exception as error:
        print(f'User charts API error: {error}')
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@router.get("/user-charts")
async def method_not_allowed():
    raise HTTPException(
        status_code=405,
        detail="Method not allowed. Use POST."
    )