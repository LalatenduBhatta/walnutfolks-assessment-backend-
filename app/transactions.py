# app/routes/transactions.py
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Pydantic models
class TransactionResponse(BaseModel):
    transaction_id: str
    source_account: str
    destination_account: str
    amount: float
    currency: str
    status: str
    created_at: str
    processed_at: Optional[str]
    updated_at: str

# Mock database
transactions_db = {
    "txn_123": {
        "transaction_id": "txn_123",
        "source_account": "acc_123",
        "destination_account": "acc_456",
        "amount": 10000,  # stored in cents
        "currency": "INR",
        "status": "PROCESSED",
        "created_at": "2024-01-01T00:00:00Z",
        "processed_at": "2024-01-01T00:00:30Z",
        "updated_at": "2024-01-01T00:00:30Z"
    }
}

@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str = Path(..., description="The ID of the transaction to retrieve")
):
    try:
        if not transaction_id:
            raise HTTPException(
                status_code=400,
                detail="Transaction ID is required"
            )

        transaction = transactions_db.get(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found"
            )

        # Convert amount back from cents to main unit
        response_data = TransactionResponse(
            transaction_id=transaction["transaction_id"],
            source_account=transaction["source_account"],
            destination_account=transaction["destination_account"],
            amount=transaction["amount"] / 100,  # Convert back from cents
            currency=transaction["currency"],
            status=transaction["status"],
            created_at=transaction["created_at"],
            processed_at=transaction["processed_at"],
            updated_at=transaction["updated_at"]
        )

        return response_data

    except HTTPException:
        raise
    except Exception as error:
        print(f'Error fetching transaction: {error}')
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )