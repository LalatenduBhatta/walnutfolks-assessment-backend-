# app/database.py
import os
from supabase import create_client, Client
from typing import Optional

class Database:
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Supabase credentials not found in environment variables")
            
            cls._instance = create_client(supabase_url, supabase_key)
        return cls._instance

    @classmethod
    async def health_check(cls) -> bool:
        try:
            client = cls.get_client()
            # Simple query to check database connection
            result = client.table('transactions').select('count', count='exact').limit(1).execute()
            return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False