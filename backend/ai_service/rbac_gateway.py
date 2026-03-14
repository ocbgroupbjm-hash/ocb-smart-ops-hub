# OCB TITAN ERP - AI RBAC Gateway
# =====================================
# Version: 1.0.0

"""
AI RBAC GATEWAY

Access control for AI endpoints:
- OWNER: Full access
- SUPER_ADMIN: Full access
- AUDITOR: Read insights only
- MANAGER: Read insights only

Other roles: NO ACCESS
"""

from fastapi import HTTPException
from typing import List


# Allowed roles for AI Engine
AI_ALLOWED_ROLES = ["owner", "super_admin", "auditor", "manager"]

# Role permissions
AI_ROLE_PERMISSIONS = {
    "owner": ["sales", "inventory", "finance", "ceo", "logs", "config"],
    "super_admin": ["sales", "inventory", "finance", "ceo", "logs", "config"],
    "auditor": ["sales", "inventory", "finance", "logs"],
    "manager": ["sales", "inventory", "ceo"]
}


class AIRBACGateway:
    """
    RBAC Gateway for AI Engine
    """
    
    @staticmethod
    def check_access(user: dict, module: str = None) -> bool:
        """
        Check if user has access to AI Engine
        
        Args:
            user: User dict from JWT
            module: Optional specific module to check
        
        Returns:
            True if access granted
        
        Raises:
            HTTPException if access denied
        """
        role = user.get("role_code") or user.get("role") or ""
        role = role.lower()
        
        if role not in AI_ALLOWED_ROLES:
            raise HTTPException(
                status_code=403,
                detail=f"AI Engine access denied. Role '{role}' tidak memiliki akses. "
                       f"Roles yang diizinkan: {', '.join(AI_ALLOWED_ROLES)}"
            )
        
        if module:
            allowed_modules = AI_ROLE_PERMISSIONS.get(role, [])
            if module not in allowed_modules:
                raise HTTPException(
                    status_code=403,
                    detail=f"AI module '{module}' tidak diizinkan untuk role '{role}'"
                )
        
        return True
    
    @staticmethod
    def get_allowed_modules(user: dict) -> List[str]:
        """Get list of allowed AI modules for user"""
        role = user.get("role_code") or user.get("role") or ""
        role = role.lower()
        
        return AI_ROLE_PERMISSIONS.get(role, [])
    
    @staticmethod
    def is_admin(user: dict) -> bool:
        """Check if user is admin (owner/super_admin)"""
        role = user.get("role_code") or user.get("role") or ""
        role = role.lower()
        
        return role in ["owner", "super_admin"]
