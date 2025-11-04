# app/utils.py
import asyncio
import uuid
from typing import Set
from app.database import Database

# In-memory store for tracking processing transactions
processing_transactions: Set[str] = set()

async def process_transaction_in_background(transaction_id: str):
    """
    Process transaction in background with 30-second delay
    """
    try:
        print(f"Starting background processing for transaction: {transaction_id}")
        
        # Add to processing set
        processing_transactions.add(transaction_id)
        
        # Simulate 30-second delay for external API calls
        await asyncio.sleep(30)
        
        print(f"Completing processing for transaction: {transaction_id}")
        
        # Update transaction status to PROCESSED
        client = Database.get_client()
        result = client.table('transactions').update({
            'status': 'PROCESSED',
            'processed_at': 'now()',
            'updated_at': 'now()'
        }).eq('transaction_id', transaction_id).execute()
        
        if result.error:
            print(f"Error updating transaction status: {result.error}")
            raise Exception(result.error)
            
        print(f"Transaction {transaction_id} processed successfully")
        
    except Exception as e:
        print(f"Background processing error for {transaction_id}: {e}")
        
        # Update transaction with error status
        try:
            client = Database.get_client()
            client.table('transactions').update({
                'status': 'PROCESSING',  # Keep as processing for retry
                'updated_at': 'now()'
            }).eq('transaction_id', transaction_id).execute()
        except Exception as update_error:
            print(f"Failed to update transaction status after error: {update_error}")
            
    finally:
        # Remove from processing set
        processing_transactions.discard(transaction_id)

def generate_transaction_id() -> str:
    """Generate a unique transaction ID"""
    return f"txn_{uuid.uuid4().hex[:16]}"

def is_processing(transaction_id: str) -> bool:
    """Check if transaction is currently being processed"""
    return transaction_id in processing_transactions