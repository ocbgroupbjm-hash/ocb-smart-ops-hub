from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
from typing import Optional, List
from datetime import datetime, timezone

class AIService:
    def __init__(self, company_id: str, agent_mode: str = "customer_service"):
        self.api_key = os.getenv("EMERGENT_LLM_KEY")
        self.company_id = company_id
        self.agent_mode = agent_mode
        
    def get_system_message(self, language: str = "en", knowledge_context: str = "") -> str:
        """Generate system prompt based on agent mode and language"""
        
        base_context = f"""Context: {knowledge_context}""" if knowledge_context else ""
        
        if self.agent_mode == "customer_service":
            if language == "id":
                return f"""Anda adalah AI Customer Service yang profesional dan ramah. 
                Tugas Anda:
                - Menjawab pertanyaan pelanggan dengan jelas dan akurat
                - Memberikan informasi produk
                - Menangani keluhan dengan empati
                - Merekomendasikan solusi yang tepat
                - Eskalasi ke manusia jika diperlukan
                
                {base_context}
                
                Berikan respon yang membantu, sopan, dan profesional."""
            else:
                return f"""You are a professional and friendly AI Customer Service agent.
                Your tasks:
                - Answer customer questions clearly and accurately
                - Provide product information
                - Handle complaints with empathy
                - Recommend appropriate solutions
                - Escalate to human if needed
                
                {base_context}
                
                Provide helpful, polite, and professional responses."""
        
        elif self.agent_mode == "sales":
            if language == "id":
                return f"""Anda adalah AI Sales Agent yang persuasif dan berorientasi hasil.
                Tugas Anda:
                - Merekomendasikan produk yang sesuai kebutuhan pelanggan
                - Melakukan upselling dan cross-selling
                - Menyampaikan promosi dan penawaran menarik
                - Membantu closing penjualan
                - Menciptakan urgency yang natural
                
                {base_context}
                
                Jadilah sales agent terbaik yang membantu pelanggan menemukan produk yang tepat."""
            else:
                return f"""You are a persuasive and results-oriented AI Sales Agent.
                Your tasks:
                - Recommend products matching customer needs
                - Perform upselling and cross-selling
                - Share promotions and attractive offers
                - Help close sales
                - Create natural urgency
                
                {base_context}
                
                Be the best sales agent helping customers find the right products."""
        
        else:  # marketing
            if language == "id":
                return f"""Anda adalah AI Marketing Agent yang kreatif dan engaging.
                Tugas Anda:
                - Memberikan informasi kampanye dan promosi
                - Menyampaikan penawaran khusus
                - Mengedukasi tentang produk baru
                - Mengumpulkan feedback pelanggan
                - Membangun engagement yang kuat
                
                {base_context}
                
                Ciptakan interaksi yang menarik dan memorable."""
            else:
                return f"""You are a creative and engaging AI Marketing Agent.
                Your tasks:
                - Share campaign and promotion information
                - Deliver special offers
                - Educate about new products
                - Collect customer feedback
                - Build strong engagement
                
                {base_context}
                
                Create attractive and memorable interactions."""
    
    async def chat(self, 
                   user_message: str, 
                   session_id: str,
                   language: str = "en",
                   knowledge_context: str = "",
                   model: str = "gpt-5.2") -> str:
        """Send message to AI and get response"""
        
        try:
            # Create new chat instance for this session
            system_message = self.get_system_message(language, knowledge_context)
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=system_message
            )
            
            # Configure model (default GPT-5.2, fallback to GPT-5.1 or GPT-4o)
            chat.with_model("openai", model)
            
            # Send message
            message = UserMessage(text=user_message)
            response = await chat.send_message(message)
            
            return response
            
        except Exception as e:
            # Fallback to GPT-5.1 if GPT-5.2 fails
            if model == "gpt-5.2":
                try:
                    return await self.chat(user_message, session_id, language, knowledge_context, "gpt-5.1")
                except:
                    # Final fallback to GPT-4o
                    return await self.chat(user_message, session_id, language, knowledge_context, "gpt-4o")
            
            raise Exception(f"AI service error: {str(e)}")