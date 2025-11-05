# app/routes/webhooks.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, validator
from typing import Optional
import asyncio
from datetime import datetime

router = APIRouter()

# Pydantic models
class WebhookRequest(BaseModel):
    transaction_id: str
    source_account: str
    destination_account: str
    amount: float
    currency: str = "INR"

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be a positive number')
        return v

class WebhookResponse(BaseModel):
    acknowledged: bool
    transaction_id: str
    status: str

# In-memory store for tracking processing transactions
processing_transactions = set()

# Mock database
transactions_db = {}

async def process_transaction_in_background(transaction_id: str):
    """
    Background task to simulate processing a transaction
    """
    print(f'Starting background processing for transaction: {transaction_id}')
    
    try:
        # Simulate 30-second delay for external API calls
        await asyncio.sleep(30)

        print(f'Completing processing for transaction: {transaction_id}')

        # Update transaction status to PROCESSED
        if transaction_id in transactions_db:
            transactions_db[transaction_id].update({
                "status": "PROCESSED",
                "processed_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z"
            })

        print(f'Transaction {transaction_id} processed successfully')

    except Exception as error:
        print(f'Background processing error: {error}')
        
        # Update transaction with error status
        if transaction_id in transactions_db:
            transactions_db[transaction_id].update({
                "status": "PROCESSING",
                "updated_at": datetime.utcnow().isoformat() + "Z"
            })
            
    finally:
        # Remove from processing set
        if transaction_id in processing_transactions:
            processing_transactions.remove(transaction_id)

@router.post("/webhooks/transactions")
async def handle_transaction_webhook(
    request: WebhookRequest, 
    background_tasks: BackgroundTasks
):
    start_time = datetime.utcnow()
    
    try:
        print(f'Received webhook: {request.dict()}')
        
        # Check if already processing (in-memory check for immediate duplicates)
        if request.transaction_id in processing_transactions:
            print(f'Transaction {request.transaction_id} is already being processed')
            from fastapi.responses import Response
            return Response(status_code=202)

        # Check database for existing transaction
        existing_transaction = transactions_db.get(request.transaction_id)
        
        if existing_transaction:
            print(f'Transaction {request.transaction_id} already exists with status: {existing_transaction["status"]}')
            from fastapi.responses import Response
            return Response(status_code=202)

        # Add to processing set
        processing_transactions.add(request.transaction_id)

        # Insert transaction with PROCESSING status
        transaction_data = {
            "transaction_id": request.transaction_id,
            "source_account": request.source_account,
            "destination_account": request.destination_account,
            "amount": round(request.amount * 100),  # Store in cents/paisa
            "currency": request.currency,
            "status": "PROCESSING",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "processed_at": None,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }

        transactions_db[request.transaction_id] = transaction_data

        print(f'Transaction {request.transaction_id} inserted successfully, starting background processing')

        # Start background processing
        background_tasks.add_task(process_transaction_in_background, request.transaction_id)

        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        print(f'Webhook processed in {processing_time}ms')

        # Return 202 Accepted as required
        return WebhookResponse(
            acknowledged=True,
            transaction_id=request.transaction_id,
            status="processing"
        )

    except Exception as error:
        print(f'Webhook processing error: {error}')
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "processing_time": f"{processing_time}ms"
            }
        )

@router.options("/webhooks/transactions")
async def webhook_options():
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
    )