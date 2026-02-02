"""
AI Email Agent - An intelligent email drafting assistant.

This package provides a CLI tool for drafting emails based on:
- User writing style analysis
- Interactive intent detection
- Multiple email templates
- Local AI integration via Ollama
"""

__version__ = "1.0.0"
__author__ = "AI Email Agent Team"
__email__ = "support@emailagent.ai"

from .cli import cli
from .email_generator import EmailGenerator
from .style_analyzer import StyleAnalyzer
from .template_manager import TemplateManager
from .intent_detector import IntentDetector
from .ai_engine import AIEngine

__all__ = [
    "cli",
    "EmailGenerator", 
    "StyleAnalyzer",
    "TemplateManager",
    "IntentDetector",
    "AIEngine",
]