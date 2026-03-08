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
        self.timeout = 30.0
        self.session = "default"
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers - NO authentication required"""
        return {
            "Content-Type": "application/json"
        }
    
    def update_config(self, base_url: str = None, session: str = None):
        """Update WAHA configuration"""
        if base_url:
            self.base_url = base_url.rstrip('/')
        if session:
            self.session = session
    
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
        
        url = f"{self.base_url}/api/sendText"
        
        payload = {
            "chatId": chat_id,
            "text": text,
            "session": session
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers()
                )
                
                logger.info(f"WAHA Send: URL={url}, Status={response.status_code}")
                
                if response.status_code in [200, 201]:
                    logger.info(f"WAHA: Message sent successfully to {phone}")
                    return {
                        "success": True,
                        "chat_id": chat_id,
                        "response": response.json() if response.text else {}
                    }
                elif response.status_code == 401:
                    logger.error(f"WAHA: Authentication failed (401). Check API key.")
                    return {
                        "success": False,
                        "error": "WAHA authentication failed. API key may be incorrect.",
                        "status_code": 401,
                        "chat_id": chat_id
                    }
                else:
                    error_msg = f"Status {response.status_code}: {response.text}"
                    logger.error(f"WAHA send failed: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "status_code": response.status_code,
                        "chat_id": chat_id
                    }
                        
        except httpx.TimeoutException:
            logger.error(f"WAHA: Timeout sending message to {phone}")
            return {
                "success": False,
                "error": "WAHA server timeout"
            }
        except Exception as e:
            logger.error(f"WAHA: Exception sending message: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_send(self, phone: str, text: str) -> Dict[str, Any]:
        """Test send with detailed debugging"""
        chat_id = self.phone_to_chat_id(phone)
        url = f"{self.base_url}/api/sendText"
        
        headers = self._get_headers()
        payload = {
            "chatId": chat_id,
            "text": text,
            "session": self.session
        }
        
        result = {
            "url": url,
            "headers": {k: v[:20] + "..." if k == "X-Api-Key" else v for k, v in headers.items()},
            "payload": payload,
            "chat_id": chat_id
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                result["status_code"] = response.status_code
                result["response"] = response.text[:500]
                result["success"] = response.status_code in [200, 201]
                
                if result["success"]:
                    result["message"] = "Message sent successfully!"
                elif response.status_code == 401:
                    result["message"] = "Authentication failed. Please verify API key with WAHA admin."
                else:
                    result["message"] = f"Failed with status {response.status_code}"
                    
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
            result["message"] = f"Request failed: {str(e)}"
        
        return result
    
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
        url = f"{self.base_url}/api/sessions"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=self._get_headers())
                
                logger.info(f"WAHA status check: {response.status_code} - {response.text[:200]}")
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "connected": True,
                        "sessions": response.json() if response.text else [],
                        "message": "WAHA server connected"
                    }
                else:
                    return {
                        "success": False,
                        "connected": False,
                        "error": f"WAHA returned status {response.status_code}: {response.text[:100]}"
                    }
        except Exception as e:
            logger.error(f"WAHA connection check failed: {str(e)}")
            return {
                "success": False,
                "connected": False,
                "error": f"Cannot connect to WAHA: {str(e)}"
            }


# Global instance
waha_service = WAHAService()
