#!/usr/bin/env python3
"""
Simple test script to generate an email without unicode issues.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.email_generator import EmailGenerator
from src.ai_engine import AIEngine
from src.template_manager import TemplateManager
from src.style_analyzer import StyleAnalyzer
from src.intent_detector import IntentDetector

def main():
    print("=== AI Email Agent Test ===")
    
    # Initialize components
    print("Initializing components...")
    ai_engine = AIEngine()
    template_manager = TemplateManager()
    style_analyzer = StyleAnalyzer()
    intent_detector = IntentDetector(ai_engine)
    
    # Create generator
    generator = EmailGenerator(ai_engine, template_manager, style_analyzer, intent_detector)
    
    # Test email generation
    print("\nGenerating test email...")
    try:
        result = generator.generate_email(
            topic="Project Update",
            recipient="team@example.com",
            context="Weekly status update on our progress",
            user_profile=None,
            template_name=None,
            interactive=False
        )
        
        print("\n=== GENERATED EMAIL ===")
        print(f"Subject: {result['subject']}")
        print(f"Body: {result['body']}")
        print("===================")
        
        # Save to file
        with open("test_email.txt", "w", encoding="utf-8") as f:
            f.write(f"Subject: {result['subject']}\n\n{result['body']}")
        
        print("\nEmail saved to: test_email.txt")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()