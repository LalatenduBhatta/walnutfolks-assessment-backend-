# app/routes/user_charts.py
from fastapi import APIRouter, HTTPException, status
from app.models import UserChartRequest, UserChartResponse, ChartData, ErrorResponse
from app.database import Database
import re

router = APIRouter()

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@router.post("/v1/user-charts", response_model=UserChartResponse)
async def handle_user_charts(request: UserChartRequest):
    """
    Save or retrieve user chart data
    """
    try:
        # Validate email
        if not request.email or not is_valid_email(request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid email is required"
            )

        client = Database.get_client()
        email = request.email.lower().strip()

        if request.action == "save":
            if not request.chartData:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Chart data is required for save action"
                )

            # Validate chart data structure
            if not all(hasattr(request.chartData, attr) for attr in ['callDuration', 'sadPath']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid chart data structure"
                )

            # Save or update chart data
            result = client.table('user_charts')\
                .upsert({
                    'email': email,
                    'chart_data': request.chartData.dict(),
                    'updated_at': 'now()'
                }, on_conflict='email')\
                .execute()

            if result.error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save chart data"
                )

            return UserChartResponse(
                success=True,
                message="Chart data saved successfully"
            )

        elif request.action == "get":
            # Get existing chart data
            result = client.table('user_charts')\
                .select('chart_data, updated_at')\
                .eq('email', email)\
                .execute()

            if result.error and result.error.message != "JSON object requested, multiple (or no) rows returned":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch chart data"
                )

            chart_data = None
            last_updated = None

            if result.data and len(result.data) > 0:
                chart_data_dict = result.data[0]['chart_data']
                chart_data = ChartData(**chart_data_dict)
                last_updated = result.data[0]['updated_at']

            return UserChartResponse(
                success=True,
                chartData=chart_data,
                lastUpdated=last_updated
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Use 'save' or 'get'"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"User charts API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )