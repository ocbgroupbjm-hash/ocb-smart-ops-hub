# WAHA WhatsApp Integration Service
import httpx
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class WAHAService:
    """WAHA WhatsApp HTTP API Service for OCB AI"""
    
    def __init__(self):
        self.base_url = "https://waha-as0dv2f9yagn.cgk-hello.sumopod.my.id"
        self.api_key = "eHFxMagfx2s6BEp1sI909zPoomX2UouH"
        self.timeout = 30.0
        self.session = "default"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with multiple auth methods support"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number to international format"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle Indonesian numbers
        if digits.startswith('0'):
            digits = '62' + digits[1:]
        elif digits.startswith('8'):
            digits = '62' + digits
        elif not digits.startswith('62'):
            digits = '62' + digits
            
        return digits
    
    def phone_to_chat_id(self, phone: str) -> str:
        """Convert phone number to WAHA chat ID format"""
        normalized = self.normalize_phone(phone)
        return f"{normalized}@c.us"
    
    async def send_message(self, phone: str, text: str, session: str = None) -> Dict[str, Any]:
        """Send WhatsApp message via WAHA API"""
        chat_id = self.phone_to_chat_id(phone)
        session = session or self.session
        
        # Try multiple WAHA endpoints
        endpoints = [
            f"{self.base_url}/api/sendText",
            f"{self.base_url}/api/{session}/sendText",
            f"{self.base_url}/api/messages/send",
        ]
        
        payload = {
            "chatId": chat_id,
            "text": text,
            "session": session
        }
        
        last_error = None
        
        for url in endpoints:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers=self._get_headers()
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"WAHA: Message sent successfully to {phone} via {url}")
                        return {
                            "success": True,
                            "chat_id": chat_id,
                            "endpoint": url,
                            "response": response.json() if response.text else {}
                        }
                    else:
                        last_error = f"Status {response.status_code}: {response.text}"
                        logger.warning(f"WAHA endpoint {url} failed: {last_error}")
                        
            except httpx.TimeoutException:
                last_error = "Timeout"
                logger.warning(f"WAHA endpoint {url} timeout")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"WAHA endpoint {url} error: {last_error}")
        
        # All endpoints failed
        logger.error(f"WAHA: All endpoints failed for {phone}. Last error: {last_error}")
        return {
            "success": False,
            "error": f"WAHA send failed: {last_error}",
            "chat_id": chat_id
        }
    
    async def get_status(self, session: str = None) -> Dict[str, Any]:
        """Get WAHA session status"""
        session = session or self.session
        urls = [
            f"{self.base_url}/api/sessions/{session}",
            f"{self.base_url}/api/sessions",
            f"{self.base_url}/api/{session}/status",
        ]
        
        for url in urls:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=self._get_headers())
                    
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "status": response.json()
                        }
            except Exception as e:
                continue
        
        return {
            "success": False,
            "error": "Could not get WAHA status"
        }
    
    async def check_connection(self) -> Dict[str, Any]:
        """Check if WAHA server is reachable"""
        urls = [
            f"{self.base_url}/api/sessions",
            f"{self.base_url}/api/",
            f"{self.base_url}/health",
        ]
        
        for url in urls:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, headers=self._get_headers())
                    
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "connected": True,
                            "sessions": response.json() if response.text else [],
                            "message": "WAHA server connected"
                        }
                    elif response.status_code == 401:
                        # Server is reachable but needs auth
                        return {
                            "success": True,
                            "connected": True,
                            "auth_required": True,
                            "message": "WAHA server reachable (auth may need verification)"
                        }
            except Exception as e:
                continue
        
        return {
            "success": False,
            "connected": False,
            "error": "Cannot connect to WAHA server"
        }


# Global instance
waha_service = WAHAService()
