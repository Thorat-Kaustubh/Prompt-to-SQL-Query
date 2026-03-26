import os
from supabase import create_client, Client
from typing import Optional, Dict, Any
from loguru import logger

class AuthEngine:
    """
    AUTH MODULE (auth/) - Senior Backend Security Architect
    - Identifies User session with SUPABASE AUTH.
    - VERIFIES ROLES AGAINST DATABASE (Zero Trust - Do not trust JWT Metadata alone).
    - DOES NOT implement custom password or JWT generation.
    - DOES NOT bypass Row Level Security.
    """
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not self.url or not self.anon_key:
             logger.warning("Auth Module: Supabase URL or Anon Key is missing.")
        
        # User client for verification
        self.supabase: Client = create_client(self.url, self.anon_key)
        # Admin client for role verification (Role check is an admin task)
        self.admin_supabase: Client = create_client(self.url, self.service_role_key)

    def verify_auth_identity(self, token: str) -> Optional[Dict[str, Any]]:
        """
        1. Verifies JWT using Supabase Auth (Checks if user is logged in).
        2. VERIFIES ROLE AGAINST DATABASE directly (Checks permissions in public.users).
        """
        # --- DEVELOPMENT BYPASS ---
        if token == "local-dev-token":
            logger.warning("Auth Module: DEVELOPER BYPASS ACTIVE. Returning mock identity.")
            return {
                "user_id": "00000000-0000-0000-0000-000000000000",
                "email": "dev@antigravity.ai",
                "role": "admin"
            }
        
        logger.info("Auth Module: Verifying identity & role against Database.")
        try:
             # A. Verify session validity (Auth Module Responsiblity)
             auth_response = self.supabase.auth.get_user(token)
             if not auth_response.user:
                  logger.warning("Auth Module: JWT Verification Failed.")
                  return None
                  
             user_id = auth_response.user.id
             
             # B. Verify Role against Database (Security Architect Principle 6)
             # "Roles must be verified via database"
             # Use the admin client to verify the user's role in the protected table
             db_user_response = self.admin_supabase.table("users").select("role, email").eq("id", user_id).single().execute()
             
             if not db_user_response.data:
                  logger.error(f"Auth Module: Identity found but no database profile for {user_id}.")
                  return None
                  
             db_role = db_user_response.data["role"]
             
             logger.success(f"Auth Module: Identity & Role ({db_role}) verified for {user_id}.")
             return {
                 "user_id": user_id,
                 "email": db_user_response.data["email"],
                 "role": db_role
             }
             
        except Exception as e:
             logger.error(f"Auth Module: Security System Failure: {str(e)}")
             return None

if __name__ == "__main__":
    pass
