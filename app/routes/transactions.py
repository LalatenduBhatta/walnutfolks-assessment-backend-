# app/routes/transactions.py
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import List
from app.models import WebhookPayload, TransactionResponse, HealthResponse, ErrorResponse
from app.database import Database
from app.utils import process_transaction_in_background, is_processing, generate_transaction_id

router = APIRouter()

@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    """
    from datetime import datetime
    db_healthy = await Database.health_check()
    
    return HealthResponse(
        status="HEALTHY" if db_healthy else "UNHEALTHY",
        current_time=datetime.utcnow()
    )

@router.post("/v1/webhooks/transactions", status_code=status.HTTP_202_ACCEPTED)
async def receive_transaction_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks
):
    """
    Receive transaction webhook from payment processors
    - Returns 202 Accepted immediately
    - Processes transaction in background with 30-second delay
    - Handles duplicate transactions gracefully
    """
    try:
        # Validate required fields
        if not all([payload.transaction_id, payload.source_account, 
                   payload.destination_account, payload.amount]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields"
            )

        # Validate amount
        if payload.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be positive"
            )

        client = Database.get_client()

        # Check if already processing (in-memory check for immediate duplicates)
        if is_processing(payload.transaction_id):
            return {"acknowledged": True, "status": "already_processing"}

        # Check database for existing transaction
        existing_transaction = client.table('transactions')\
            .select('transaction_id, status')\
            .eq('transaction_id', payload.transaction_id)\
            .execute()

        if existing_transaction.data and len(existing_transaction.data) > 0:
            return {"acknowledged": True, "status": "duplicate"}

        # Insert transaction with PROCESSING status
        transaction_data = {
            'transaction_id': payload.transaction_id,
            'source_account': payload.source_account,
            'destination_account': payload.destination_account,
            'amount': int(payload.amount * 100),  # Store in cents
            'currency': payload.currency,
            'status': 'PROCESSING',
            'created_at': 'now()',
            'processed_at': None
        }

        insert_result = client.table('transactions')\
            .insert(transaction_data)\
            .execute()

        if insert_result.error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process transaction"
            )

        # Start background processing
        background_tasks.add_task(process_transaction_in_background, payload.transaction_id)

        return {
            "acknowledged": True,
            "transaction_id": payload.transaction_id,
            "status": "processing"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/v1/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction_status(transaction_id: str):
    """
    Get transaction status by transaction ID
    """
    try:
        if not transaction_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction ID is required"
            )

        client = Database.get_client()
        result = client.table('transactions')\
            .select('*')\
            .eq('transaction_id', transaction_id)\
            .execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        transaction = result.data[0]

        # Convert amount back from cents to main unit
        response_data = {
            'transaction_id': transaction['transaction_id'],
            'source_account': transaction['source_account'],
            'destination_account': transaction['destination_account'],
            'amount': transaction['amount'] / 100.0,  # Convert back from cents
            'currency': transaction['currency'],
            'status': transaction['status'],
            'created_at': transaction['created_at'],
            'processed_at': transaction['processed_at']
        }

        return TransactionResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )