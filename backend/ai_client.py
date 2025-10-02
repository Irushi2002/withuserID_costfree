import google.generativeai as genai
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class AIClientWrapper:
    """
    Unified wrapper for multiple AI providers (Gemini, Groq, Hugging Face)
    Provides consistent interface regardless of underlying provider
    """
    
    def __init__(self, provider_config: Dict[str, str]):
        """
        Initialize AI client for specific provider
        
        Args:
            provider_config: Dict containing provider, api_key, model, name
        """
        self.provider = provider_config["provider"]
        self.api_key = provider_config["api_key"]
        self.model = provider_config["model"]
        self.name = provider_config["name"]
        
        # Initialize provider-specific clients
        if self.provider == "gemini":
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        elif self.provider == "groq":
            self.base_url = "https://api.groq.com/openai/v1/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        elif self.provider == "huggingface":
            self.base_url = f"https://api-inference.huggingface.co/models/{self.model}"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        
        logger.info(f"AI client initialized for {self.name} ({self.provider})")
    
    async def generate_content(self, prompt: str) -> Optional[str]:
        """
        Generate content using the configured provider
        
        Args:
            prompt: The input prompt
            
        Returns:
            Generated text or None if failed
        """
        try:
            if self.provider == "gemini":
                return await self._generate_gemini(prompt)
            elif self.provider == "groq":
                return await self._generate_groq(prompt)
            elif self.provider == "huggingface":
                return await self._generate_huggingface(prompt)
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating content with {self.name}: {e}")
            return None
    
    async def _generate_gemini(self, prompt: str) -> Optional[str]:
        """Generate content using Gemini"""
        try:
            response = self.client.generate_content(prompt)
            if response.text and response.text.strip():
                logger.info(f"Gemini ({self.name}) generated response: {len(response.text)} chars")
                return response.text.strip()
            else:
                logger.warning(f"Gemini ({self.name}) returned empty response")
                return None
        except Exception as e:
            logger.error(f"Gemini ({self.name}) generation failed: {e}")
            return None
    
    async def _generate_groq(self, prompt: str) -> Optional[str]:
        """Generate content using Groq"""
        try:
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                if content and content.strip():
                    logger.info(f"Groq ({self.name}) generated response: {len(content)} chars")
                    return content.strip()
                else:
                    logger.warning(f"Groq ({self.name}) returned empty content")
                    return None
            else:
                logger.error(f"Groq ({self.name}) API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Groq ({self.name}) generation failed: {e}")
            return None
    
    # async def _generate_huggingface(self, prompt: str) -> Optional[str]:
    #     """Generate content using Hugging Face"""
    #     try:
    #         # Format prompt for better question generation
    #         formatted_prompt = f"Generate 3 follow-up questions based on this work update:\n\n{prompt}\n\nQuestions:\n1."
            
    #         # Different models need different formatting
    #         if "flan-t5" in self.model.lower():
    #             data = {
    #                 "inputs": formatted_prompt,
    #                 "parameters": {
    #                     "max_new_tokens": 200,
    #                     "temperature": 0.7,
    #                     "do_sample": True
    #                 }
    #             }
    #         elif "dialogpt" in self.model.lower():
    #             data = {
    #                 "inputs": formatted_prompt,
    #                 "parameters": {
    #                     "max_length": 300,
    #                     "temperature": 0.8,
    #                     "pad_token_id": 50256
    #                 }
    #             }
    #         elif "blenderbot" in self.model.lower():
    #             data = {
    #                 "inputs": formatted_prompt,
    #                 "parameters": {
    #                     "max_length": 250,
    #                     "temperature": 0.7
    #                 }
    #             }
    #         else:
    #             # Generic approach
    #             data = {"inputs": formatted_prompt}
            
    #         response = requests.post(
    #             self.base_url,
    #             headers=self.headers,
    #             json=data,
    #             timeout=30
    #         )
            
    #         if response.status_code == 200:
    #             result = response.json()
                
    #             # Handle different response formats from HuggingFace
    #             content = None
    #             if isinstance(result, list) and len(result) > 0:
    #                 if "generated_text" in result[0]:
    #                     content = result[0]["generated_text"]
    #                 elif "translation_text" in result[0]:
    #                     content = result[0]["translation_text"]
    #                 else:
    #                     content = str(result[0])
    #             elif isinstance(result, dict):
    #                 content = result.get("generated_text") or result.get("translation_text") or str(result)
    #             else:
    #                 content = str(result)
                
    #             if content and content.strip():
    #                 # Clean up the response (remove the original prompt if included)
    #                 if content.startswith(formatted_prompt):
    #                     content = content[len(formatted_prompt):].strip()
    #                 elif content.startswith(prompt):
    #                     content = content[len(prompt):].strip()
                    
    #                 logger.info(f"HuggingFace ({self.name}) generated response: {len(content)} chars")
    #                 return content
    #             else:
    #                 logger.warning(f"HuggingFace ({self.name}) returned empty content")
    #                 return None
    #         elif response.status_code == 503:
    #             logger.warning(f"HuggingFace ({self.name}) model loading: {response.json().get('error', 'Unknown error')}")
    #             return None
    #         else:
    #             logger.error(f"HuggingFace ({self.name}) API error: {response.status_code} - {response.text}")
    #             return None
                
    #     except Exception as e:
    #         logger.error(f"HuggingFace ({self.name}) generation failed: {e}")
    #         return None
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the AI provider
        
        Returns:
            Dict with test results
        """
        test_prompt = "Generate a simple test response: 'AI connection working'"
        
        try:
            result = await self.generate_content(test_prompt)
            
            if result and "working" in result.lower():
                return {
                    "status": "working",
                    "provider": self.provider,
                    "name": self.name,
                    "response": result[:100] + "..." if len(result) > 100 else result
                }
            else:
                return {
                    "status": "failed",
                    "provider": self.provider,
                    "name": self.name,
                    "error": "Invalid response or connection failed",
                    "response": result[:50] + "..." if result else None
                }
                
        except Exception as e:
            return {
                "status": "error",
                "provider": self.provider,
                "name": self.name,
                "error": str(e)
            }

class AIProviderManager:
    """
    Manages multiple AI provider clients
    """
    
    def __init__(self, providers_config: list):
        """
        Initialize manager with list of provider configurations
        """
        self.clients = {}
        
        for provider_config in providers_config:
            client = AIClientWrapper(provider_config)
            self.clients[provider_config["name"]] = client
        
        logger.info(f"AI Provider Manager initialized with {len(self.clients)} providers")
    
    def get_client(self, provider_name: str) -> Optional[AIClientWrapper]:
        """Get AI client by provider name"""
        return self.clients.get(provider_name)
    
    async def test_all_connections(self) -> Dict[str, Any]:
        """Test connections to all providers"""
        results = {}
        
        for name, client in self.clients.items():
            results[name] = await client.test_connection()
        
        return results