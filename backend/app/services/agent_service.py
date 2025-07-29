"""Agent service for LLM interactions and test generation."""

import logging
from typing import Dict, Any, Optional, List
import openai
import anthropic

from app.config import settings
from app.prompts.test_generation import (
    TEST_GENERATION_TEMPLATE,
    PLAYWRIGHT_TEMPLATE,
    ENGLISH_TEMPLATE
)

logger = logging.getLogger(__name__)

class AgentService:
    """Service for handling LLM interactions and test generation."""
    
    def __init__(self):
        """Initialize the AgentService with configured LLM clients."""
        self.openai_client = None
        self.anthropic_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients based on available API keys."""
        try:
            if settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here":
                self.openai_client = openai.OpenAI(
                    api_key=settings.openai_api_key
                )
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OpenAI API key not configured")
                
            if settings.anthropic_api_key and settings.anthropic_api_key != "your_anthropic_api_key_here":
                self.anthropic_client = anthropic.Anthropic(
                    api_key=settings.anthropic_api_key
                )
                logger.info("Anthropic client initialized successfully")
            else:
                logger.warning("Anthropic API key not configured")
                
        except Exception as e:
            logger.error(f"Error initializing LLM clients: {e}")
    
    def _get_primary_client(self):
        """Get the primary LLM client, preferring Anthropic if available."""
        if self.anthropic_client:
            return "anthropic"
        elif self.openai_client:
            return "openai"
        else:
            raise RuntimeError("No LLM clients available. Please configure API keys.")
    
    def _call_openai(self, prompt: str, model: str = "gpt-4") -> str:
        """Make a call to OpenAI API."""
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert QA engineer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _call_anthropic(self, prompt: str, model: str = "claude-3-sonnet-20240229") -> str:
        """Make a call to Anthropic API."""
        try:
            response = self.anthropic_client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _call_llm(self, prompt: str) -> str:
        """Call the appropriate LLM based on availability."""
        client_type = self._get_primary_client()
        
        if client_type == "anthropic":
            return self._call_anthropic(prompt)
        elif client_type == "openai":
            return self._call_openai(prompt)
        else:
            raise RuntimeError("No LLM clients available")
    
    def generate_test_cases(
        self, 
        specification: str, 
        framework: str = "playwright", 
        language: str = "javascript"
    ) -> Dict[str, Any]:
        """
        Generate test cases from product specification.
        
        Args:
            specification: Product specification text
            framework: Testing framework (playwright, selenium, etc.)
            language: Programming language (javascript, python, etc.)
            
        Returns:
            Dictionary containing generated test cases and metadata
        """
        try:
            # Format the prompt using the template
            prompt = TEST_GENERATION_TEMPLATE.format(
                specification=specification,
                framework=framework,
                language=language
            )
            
            # Call the LLM
            result = self._call_llm(prompt)
            
            return {
                "success": True,
                "test_cases": result,
                "framework": framework,
                "language": language,
                "model_used": self._get_primary_client()
            }
            
        except Exception as e:
            logger.error(f"Error generating test cases: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_cases": None
            }
    
    def generate_playwright_script(
        self, 
        test_case: str, 
        base_url: str = "http://localhost:3000"
    ) -> Dict[str, Any]:
        """
        Generate Playwright test script from test case description.
        
        Args:
            test_case: Test case description
            base_url: Base URL for the application
            
        Returns:
            Dictionary containing generated Playwright script
        """
        try:
            # Format the prompt using the template
            prompt = PLAYWRIGHT_TEMPLATE.format(
                test_case=test_case,
                base_url=base_url
            )
            
            # Call the LLM
            result = self._call_llm(prompt)
            
            return {
                "success": True,
                "script": result,
                "base_url": base_url,
                "model_used": self._get_primary_client()
            }
            
        except Exception as e:
            logger.error(f"Error generating Playwright script: {e}")
            return {
                "success": False,
                "error": str(e),
                "script": None
            }
    
    def generate_english_description(self, test_case: str) -> Dict[str, Any]:
        """
        Generate human-readable English description of a test case.
        
        Args:
            test_case: Test case to describe
            
        Returns:
            Dictionary containing English description
        """
        try:
            # Format the prompt using the template
            prompt = ENGLISH_TEMPLATE.format(test_case=test_case)
            
            # Call the LLM
            result = self._call_llm(prompt)
            
            return {
                "success": True,
                "description": result,
                "model_used": self._get_primary_client()
            }
            
        except Exception as e:
            logger.error(f"Error generating English description: {e}")
            return {
                "success": False,
                "error": str(e),
                "description": None
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of LLM services.
        
        Returns:
            Dictionary containing health status of each service
        """
        health_status = {
            "openai": {
                "available": self.openai_client is not None,
                "configured": bool(settings.openai_api_key and settings.openai_api_key != "your_openai_api_key_here")
            },
            "anthropic": {
                "available": self.anthropic_client is not None,
                "configured": bool(settings.anthropic_api_key and settings.anthropic_api_key != "your_anthropic_api_key_here")
            }
        }
        
        # Test a simple query if clients are available
        if self.openai_client or self.anthropic_client:
            try:
                test_result = self.generate_english_description("Test health check")
                health_status["test_query"] = test_result["success"]
            except Exception as e:
                health_status["test_query"] = False
                health_status["test_error"] = str(e)
        else:
            health_status["test_query"] = False
            
        return health_status 