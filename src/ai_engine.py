"""
AI Engine - Handles integration with Ollama and AI-powered text generation.

This module provides the interface for communicating with local LLM models
through Ollama, including prompt management, response processing, and error handling.
"""

import json
import time
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import yaml
import requests
from pydantic import BaseModel, Field
from rich.console import Console

console = Console()


class OllamaConfig(BaseModel):
    """Configuration for Ollama connection."""
    host: str = "http://localhost:11434"
    model: str = "qwen2.5:7b"
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0


class PromptTemplate(BaseModel):
    """Represents a prompt template with variables."""
    name: str
    template: str
    variables: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class AIEngine:
    """Main AI engine for email generation and analysis."""
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        if config is None:
            # Try to load from config file
            config = self._load_config()
        
        self.config = config or OllamaConfig()
        self.prompts: Dict[str, PromptTemplate] = {}
        self.console = console
        self._load_prompts()
        self._test_connection()
    
    def _load_config(self) -> Optional[OllamaConfig]:
        """Load configuration from YAML file."""
        try:
            config_path = Path("config/settings.yaml")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    if 'ollama' in config_data:
                        ollama_config = config_data['ollama']
                        return OllamaConfig(**ollama_config)
        except Exception:
            pass
        return None
    
    def _load_prompts(self):
        """Load prompt templates from configuration."""
        # Built-in prompts
        self.prompts = {
            "email_generation": PromptTemplate(
                name="email_generation",
                template="""You are an expert email writer. Analyze the information below and generate a natural email in the FIRST PERSON.

CONTEXT: {context}
RECIPIENT: {recipient}
TOPIC: {topic}
INTENT: {intent}
WRITING STYLE: {style_profile}
SENDER: {sender_name}

Requirements:
1. Write as {sender_name} using "I", "my", and "me".
2. Address {recipient} as "you". 
3. DO NOT use the names "{sender_name}" or "{recipient}" in the content.
4. Transform all instructions into direct actions (e.g., "Ask him" -> "I'd like to ask you").
5. IMPORTANT: Only return the JSON object. Do not add any preamble or postscript text. 
6. Use valid JSON syntax (no trailing commas, escape-quotes correctly).

JSON:
{{
  "purpose": "professional reason for writing",
  "body": "a creative, professional rewrite of the context in FIRST PERSON",
  "opening": "a polite opening sentence",
  "next_step": "a clear call to action or closing thought"
}}""",
                variables=["context", "recipient", "topic", "intent", "style_profile", "sender_name"]
            ),
            
            "style_analysis": PromptTemplate(
                name="style_analysis",
                template="""Analyze this email for writing style characteristics:

EMAIL CONTENT:
{email_content}

Please extract and rate the following characteristics (0-1 scale):
1. Formality level (0=very casual, 1=very formal)
2. Sentence complexity (0=simple, 1=complex)
3. Vocabulary sophistication (0=basic, 1=advanced)
4. Emotional tone (negative=0, neutral=0.5, positive=1)
5. Greeting patterns (identify patterns)
6. Signature patterns (identify patterns)
7. Common phrases used

Also identify:
- Average sentence length
- Tendency for direct vs indirect communication
- Use of bullet points or structured formatting

Respond in JSON format with numeric scores and descriptive patterns:""",
                variables=["email_content"]
            ),
            
            "intent_classification": PromptTemplate(
                name="intent_classification",
                template="""Classify the user's intent for this email request:

REQUEST: {user_request}
CONTEXT: {context}
RECIPIENT: {recipient}

Classify the intent into one of these categories:
- information_request: Asking for information or clarification
- action_required: Requesting action or response
- follow_up: Following up on previous communication
- introduction: Introducing something or someone
- apology: Apologizing or addressing issues
- thank_you: Expressing gratitude
- sales_pitch: Promotional or sales related
- announcement: Making announcements
- inquiry: General inquiry or question
- other: Other specific intent

Also provide:
1. Urgency level (low/medium/high/urgent)
2. Formality level (casual/professional/formal)
3. Recommended email type (business/casual/sales)

Respond in JSON format:""",
                variables=["user_request", "context", "recipient"]
            )
        }
    
    def _test_connection(self):
        """Test connection to Ollama server."""
        try:
            response = requests.get(f"{self.config.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                if self.config.model not in model_names:
                    self.console.print(f"[yellow]Warning: Model '{self.config.model}' not found. Available models: {model_names}[/yellow]")
                else:
                    self.console.print(f"[green]+ Connected to Ollama with model: {self.config.model}[/green]")
            else:
                self.console.print(f"[red]Error: Ollama server returned status {response.status_code}[/red]")
        except requests.exceptions.RequestException as e:
            self.console.print(f"[red]Error connecting to Ollama: {e}[/red]")
            self.console.print("[yellow]Make sure Ollama is running locally[/yellow]")
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama with retry logic."""
        for attempt in range(self.config.max_retries):
            try:
                payload = {
                    "model": self.config.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.7),
                        "top_p": kwargs.get("top_p", 0.9),
                        "max_tokens": kwargs.get("max_tokens", 1000)
                    }
                }
                
                response = requests.post(
                    f"{self.config.host}/api/generate",
                    json=payload,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("response", "").strip()
                
            except requests.exceptions.Timeout:
                self.console.print(f"[yellow]Timeout (attempt {attempt + 1}/{self.config.max_retries})[/yellow]")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                    continue
                raise Exception("AI generation timeout after all retries")
                
            except requests.exceptions.RequestException as e:
                self.console.print(f"[red]Request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}[/red]")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                    continue
                raise Exception(f"AI generation failed: {e}")
        
        raise Exception("AI generation failed after all retries")
    
    def generate_email(self, context: str, recipient: str, topic: str, 
                      intent: str, style_profile: str, sender_name: str) -> str:
        """Generate an email based on provided parameters."""
        template = self.prompts["email_generation"]
        prompt = template.template.format(
            context=context,
            recipient=recipient,
            topic=topic,
            intent=intent,
            style_profile=style_profile,
            sender_name=sender_name
        )
        
        return self.generate_text(prompt, temperature=0.7)
    
    def analyze_style(self, email_content: str) -> Dict[str, Any]:
        """Analyze writing style from email content."""
        template = self.prompts["style_analysis"]
        prompt = template.template.format(email_content=email_content)
        
        response = self.generate_text(prompt, temperature=0.3)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback to basic analysis if JSON parsing fails
            return {
                "formality": 0.5,
                "complexity": 0.5,
                "vocabulary": 0.5,
                "tone": "neutral",
                "error": "Failed to parse AI response"
            }
    
    def classify_intent(self, user_request: str, context: str = "", 
                       recipient: str = "") -> Dict[str, Any]:
        """Classify user intent for email generation."""
        template = self.prompts["intent_classification"]
        prompt = template.template.format(
            user_request=user_request,
            context=context,
            recipient=recipient
        )
        
        response = self.generate_text(prompt, temperature=0.3)
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback classification
            return {
                "intent": "information_request",
                "urgency": "medium",
                "formality": "professional",
                "email_type": "business",
                "error": "Failed to parse AI response"
            }
    
    def add_custom_prompt(self, name: str, template: str, 
                         variables: List[str], description: str = ""):
        """Add a custom prompt template."""
        self.prompts[name] = PromptTemplate(
            name=name,
            template=template,
            variables=variables,
            description=description
        )
    
    def list_available_prompts(self) -> List[str]:
        """List all available prompt templates."""
        return list(self.prompts.keys())
    
    def get_prompt_info(self, name: str) -> Optional[PromptTemplate]:
        """Get information about a specific prompt template."""
        return self.prompts.get(name)
    
    def test_model(self, test_text: str = "Hello, how are you?") -> str:
        """Test the AI model with a simple prompt."""
        return self.generate_text(f"Respond to: {test_text}", temperature=0.5)