"""
Intent Detector - Handles interactive intent recognition and clarification.

This module provides functionality to detect user intent for email generation
through interactive questioning, context analysis, and AI-powered classification.
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import re
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

console = Console()


class IntentType(Enum):
    """Enumeration of email intent types."""
    INFORMATION_REQUEST = "information_request"
    ACTION_REQUIRED = "action_required"
    FOLLOW_UP = "follow_up"
    INTRODUCTION = "introduction"
    APOLOGY = "apology"
    THANK_YOU = "thank_you"
    SALES_PITCH = "sales_pitch"
    ANNOUNCEMENT = "announcement"
    INQUIRY = "inquiry"
    FEEDBACK = "feedback"
    REQUEST = "request"
    UPDATE = "update"
    OTHER = "other"


class UrgencyLevel(Enum):
    """Enumeration of urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class FormalityLevel(Enum):
    """Enumeration of formality levels."""
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FORMAL = "formal"


class EmailType(Enum):
    """Enumeration of email types/categories."""
    BUSINESS = "business"
    CASUAL = "casual"
    SALES = "sales"


@dataclass
class IntentResult:
    """Result of intent detection and classification."""
    primary_intent: IntentType
    secondary_intents: List[IntentType]
    urgency: UrgencyLevel
    formality: FormalityLevel
    email_type: EmailType
    confidence: float  # 0-1
    context: Dict[str, Any]
    questions_asked: List[str]
    user_responses: Dict[str, Any]


class IntentDetector:
    """Detects user intent through interactive questioning and analysis."""
    
    def __init__(self, ai_engine=None):
        self.ai_engine = ai_engine
        self.console = console
        
        # Question templates for intent clarification
        self.intent_questions = {
            IntentType.INFORMATION_REQUEST: [
                "Are you asking for information or clarification?",
                "Do you need specific details or explanations?",
                "Is this a general question or specific inquiry?"
            ],
            IntentType.ACTION_REQUIRED: [
                "Do you need the recipient to take any action?",
                "Is there a deadline or timeline involved?",
                "What specific action do you need them to perform?"
            ],
            IntentType.FOLLOW_UP: [
                "Are you following up on a previous conversation?",
                "Was there a prior discussion or meeting?",
                "Do you need to check on progress or status?"
            ],
            IntentType.INTRODUCTION: [
                "Are you introducing yourself or someone else?",
                "Is this a professional or personal introduction?",
                "What is the purpose of this introduction?"
            ],
            IntentType.APOLOGY: [
                "Are you apologizing for something?",
                "Is this related to a mistake or issue?",
                "Do you need to make amends or correct something?"
            ],
            IntentType.THANK_YOU: [
                "Are you expressing gratitude?",
                "What are you thankful for?",
                "Is this for help, support, or something else?"
            ],
            IntentType.SALES_PITCH: [
                "Are you promoting a product or service?",
                "Are you trying to make a sale?",
                "Is this about business development?"
            ],
            IntentType.ANNOUNCEMENT: [
                "Are you making an announcement?",
                "Is this about news, updates, or changes?",
                "Who needs to know about this?"
            ],
            IntentType.INQUIRY: [
                "Are you inquiring about something specific?",
                "Is this about availability, pricing, or services?",
                "What information do you need?"
            ]
        }
        
        # Keywords for initial intent detection
        self.intent_keywords = {
            IntentType.INFORMATION_REQUEST: [
                'information', 'clarify', 'explain', 'details', 'question',
                'know', 'understand', 'learn', 'find out'
            ],
            IntentType.ACTION_REQUIRED: [
                'action', 'do', 'complete', 'send', 'provide', 'submit',
                'deadline', 'due', 'required', 'need', 'must'
            ],
            IntentType.FOLLOW_UP: [
                'follow up', 'checking in', 'status', 'progress', 'update',
                'previous', 'meeting', 'discussion', 'last time'
            ],
            IntentType.INTRODUCTION: [
                'introduce', 'meet', 'new', 'welcome', 'presentation',
                'first time', 'get to know', 'introduction'
            ],
            IntentType.APOLOGY: [
                'sorry', 'apologize', 'apology', 'mistake', 'error',
                'problem', 'issue', 'incorrect', 'wrong'
            ],
            IntentType.THANK_YOU: [
                'thank', 'thanks', 'grateful', 'appreciate', 'gratitude',
                'help', 'support', 'assistance', 'kindness'
            ],
            IntentType.SALES_PITCH: [
                'buy', 'purchase', 'sale', 'offer', 'deal', 'price',
                'product', 'service', 'promotion', 'discount'
            ],
            IntentType.ANNOUNCEMENT: [
                'announce', 'announcement', 'news', 'update', 'change',
                'launch', 'release', 'new', 'inform'
            ],
            IntentType.INQUIRY: [
                'inquire', 'inquiry', 'available', 'price', 'cost',
                'interested', 'considering', 'option'
            ]
        }
    
    def detect_intent(self, user_request: str, context: str = "", 
                      recipient: str = "", interactive: bool = True) -> IntentResult:
        """
        Detect user intent through analysis and interactive questioning.
        
        Args:
            user_request: The user's request for email generation
            context: Additional context about the situation
            recipient: The intended recipient of the email
            interactive: Whether to ask interactive questions
        
        Returns:
            IntentResult with classified intent and metadata
        """
        self.console.print("[bold blue] Detecting Email Intent[/bold blue]")
        
        # Step 1: Initial keyword-based analysis
        initial_intents = self._analyze_keywords(user_request)
        
        # Step 2: Use AI if available for more sophisticated analysis
        primary_intent = initial_intents[0] if initial_intents else IntentType.OTHER
        confidence = 0.5
        urgency = UrgencyLevel.MEDIUM
        formality = FormalityLevel.PROFESSIONAL
        email_type = EmailType.BUSINESS
        
        if self.ai_engine:
            try:
                ai_analysis = self.ai_engine.classify_intent(user_request, context, recipient)
                primary_intent = self._map_ai_intent(ai_analysis.get("intent", "information_request"))
                confidence = ai_analysis.get("confidence", 0.7)
                
                # Extract other information from AI analysis
                urgency = self._map_urgency(ai_analysis.get("urgency", "medium"))
                formality = self._map_formality(ai_analysis.get("formality", "professional"))
                email_type = self._map_email_type(ai_analysis.get("email_type", "business"))
            except Exception as e:
                self.console.print(f"[yellow]AI intent analysis failed: {e}. Falling back to keyword/interactive mode.[/yellow]")
                confidence = 0.3  # Force interactive mode
        
        # Step 3: Interactive clarification if enabled
        questions_asked = []
        user_responses = {}
        
        if interactive and confidence < 0.8:
            self.console.print("[yellow]Let me ask a few questions to better understand your intent...[/yellow]")
            
            # Clarify primary intent if confidence is low
            if confidence < 0.6:
                clarified_intent = self._clarify_intent(primary_intent, user_request)
                if clarified_intent != primary_intent:
                    primary_intent = clarified_intent
                    confidence = min(0.8, confidence + 0.2)
            
            # Ask specific questions based on the determined intent
            intent_questions = self.intent_questions.get(primary_intent, [])
            
            for question in intent_questions[:2]:  # Limit to 2 questions
                response = Prompt.ask(f"\n[blue]Q:[/blue] {question}", default="")
                if response.strip():
                    questions_asked.append(question)
                    user_responses[question] = response
            
            # Determine urgency
            urgency = self._determine_urgency(user_request, user_responses)
            
            # Determine formality
            formality = self._determine_formality(recipient, user_request, user_responses)
        
        # Step 4: Determine email type based on intent and formality
        email_type = self._determine_email_type(primary_intent, formality, recipient)
        
        # Build result
        result = IntentResult(
            primary_intent=primary_intent,
            secondary_intents=initial_intents[1:3] if len(initial_intents) > 1 else [],
            urgency=urgency,
            formality=formality,
            email_type=email_type,
            confidence=confidence,
            context={
                "user_request": user_request,
                "context": context,
                "recipient": recipient
            },
            questions_asked=questions_asked,
            user_responses=user_responses
        )
        
        # Display summary
        self._display_intent_summary(result)
        
        return result
    
    def _analyze_keywords(self, text: str) -> List[IntentType]:
        """Analyze text for keyword-based intent detection."""
        text_lower = text.lower()
        intent_scores = {}
        
        for intent_type, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                intent_scores[intent_type] = score
        
        # Sort by score and return top intents
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        return [intent for intent, score in sorted_intents]
    
    def _clarify_intent(self, suggested_intent: IntentType, user_request: str) -> IntentType:
        """Ask user to clarify the primary intent."""
        intent_options = [
            ("Information Request", IntentType.INFORMATION_REQUEST),
            ("Action Required", IntentType.ACTION_REQUIRED),
            ("Follow Up", IntentType.FOLLOW_UP),
            ("Introduction", IntentType.INTRODUCTION),
            ("Thank You", IntentType.THANK_YOU),
            ("Apology", IntentType.APOLOGY),
            ("Sales/Promotional", IntentType.SALES_PITCH),
            ("Announcement", IntentType.ANNOUNCEMENT),
            ("Inquiry", IntentType.INQUIRY),
            ("Other", IntentType.OTHER)
        ]
        
        self.console.print(f"\n[yellow]I think your intent is: {suggested_intent.value.replace('_', ' ').title()}[/yellow]")
        self.console.print("Is this correct, or would you like to choose a different intent?")
        
        choice = Prompt.ask(
            "Select intent",
            choices=[str(i) for i in range(1, len(intent_options) + 1)],
            default=str(1)
        )
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(intent_options):
                return intent_options[index][1]
        except (ValueError, IndexError):
            pass
        
        return suggested_intent
    
    def _determine_urgency(self, user_request: str, user_responses: Dict[str, str]) -> UrgencyLevel:
        """Determine urgency level from request and responses."""
        request_lower = user_request.lower()
        responses_text = " ".join(user_responses.values()).lower()
        combined_text = f"{request_lower} {responses_text}"
        
        # Urgency indicators
        urgent_keywords = ['urgent', 'asap', 'immediately', 'emergency', 'critical', 'deadline today']
        high_keywords = ['soon', 'quickly', 'promptly', 'as soon as possible', 'this week', 'few days']
        low_keywords = ['when you have time', 'no rush', 'whenever', 'eventually', 'next month']
        
        if any(keyword in combined_text for keyword in urgent_keywords):
            return UrgencyLevel.URGENT
        elif any(keyword in combined_text for keyword in high_keywords):
            return UrgencyLevel.HIGH
        elif any(keyword in combined_text for keyword in low_keywords):
            return UrgencyLevel.LOW
        else:
            return UrgencyLevel.MEDIUM
    
    def _determine_formality(self, recipient: str, user_request: str, 
                           user_responses: Dict[str, str]) -> FormalityLevel:
        """Determine formality level based on recipient and content."""
        recipient_lower = recipient.lower()
        request_lower = user_request.lower()
        responses_text = " ".join(user_responses.values()).lower()
        
        # Formality indicators
        formal_indicators = [
            'dear', 'sincerely', 'regards', 'professional', 'formal', 'respectfully',
            'mr.', 'mrs.', 'ms.', 'dr.', 'professor', 'manager', 'director', 'ceo'
        ]
        
        casual_indicators = [
            'hi', 'hey', 'hello', 'thanks', 'cheers', 'best', 'friend', 'buddy',
            'lol', 'haha', 'cool', 'awesome', 'great'
        ]
        
        # Check recipient
        formal_recipient = any(indicator in recipient_lower for indicator in formal_indicators)
        casual_recipient = any(indicator in recipient_lower for indicator in casual_indicators)
        
        # Check content
        formal_content = any(indicator in f"{request_lower} {responses_text}" for indicator in formal_indicators)
        casual_content = any(indicator in f"{request_lower} {responses_text}" for indicator in casual_indicators)
        
        if formal_recipient or formal_content:
            return FormalityLevel.FORMAL
        elif casual_recipient or casual_content:
            return FormalityLevel.CASUAL
        else:
            return FormalityLevel.PROFESSIONAL
    
    def _determine_email_type(self, intent: IntentType, formality: FormalityLevel, 
                            recipient: str) -> EmailType:
        """Determine email type based on intent and formality."""
        # Sales-related intents
        if intent == IntentType.SALES_PITCH:
            return EmailType.SALES
        
        # High formality suggests business
        if formality == FormalityLevel.FORMAL:
            return EmailType.BUSINESS
        
        # Very casual interactions
        if formality == FormalityLevel.CASUAL and intent in [IntentType.THANK_YOU, IntentType.INFORMATION_REQUEST]:
            return EmailType.CASUAL
        
        # Default to business for professional contexts
        return EmailType.BUSINESS
    
    def _map_ai_intent(self, ai_intent: str) -> IntentType:
        """Map AI intent string to IntentType enum."""
        intent_mapping = {
            "information_request": IntentType.INFORMATION_REQUEST,
            "action_required": IntentType.ACTION_REQUIRED,
            "follow_up": IntentType.FOLLOW_UP,
            "introduction": IntentType.INTRODUCTION,
            "apology": IntentType.APOLOGY,
            "thank_you": IntentType.THANK_YOU,
            "sales_pitch": IntentType.SALES_PITCH,
            "announcement": IntentType.ANNOUNCEMENT,
            "inquiry": IntentType.INQUIRY,
            "other": IntentType.OTHER
        }
        
        return intent_mapping.get(ai_intent, IntentType.OTHER)
    
    def _map_urgency(self, urgency_str: str) -> UrgencyLevel:
        """Map urgency string to UrgencyLevel enum."""
        urgency_mapping = {
            "low": UrgencyLevel.LOW,
            "medium": UrgencyLevel.MEDIUM,
            "high": UrgencyLevel.HIGH,
            "urgent": UrgencyLevel.URGENT
        }
        
        return urgency_mapping.get(urgency_str.lower(), UrgencyLevel.MEDIUM)
    
    def _map_formality(self, formality_str: str) -> FormalityLevel:
        """Map formality string to FormalityLevel enum."""
        formality_mapping = {
            "casual": FormalityLevel.CASUAL,
            "professional": FormalityLevel.PROFESSIONAL,
            "formal": FormalityLevel.FORMAL
        }
        
        return formality_mapping.get(formality_str.lower(), FormalityLevel.PROFESSIONAL)
    
    def _map_email_type(self, email_type_str: str) -> EmailType:
        """Map email type string to EmailType enum."""
        type_mapping = {
            "business": EmailType.BUSINESS,
            "casual": EmailType.CASUAL,
            "sales": EmailType.SALES
        }
        
        return type_mapping.get(email_type_str.lower(), EmailType.BUSINESS)
    
    def _display_intent_summary(self, result: IntentResult):
        """Display a summary of the detected intent."""
        summary = f"""
[bold green]+ Intent Analysis Complete[/bold green]

Primary Intent: [cyan]{result.primary_intent.value.replace('_', ' ').title()}[/cyan]
Urgency: [yellow]{result.urgency.value.upper()}[/yellow]
Formality: [blue]{result.formality.value.title()}[/blue]
Email Type: [magenta]{result.email_type.value.title()}[/magenta]
Confidence: [green]{result.confidence:.1%}[/green]

"""
        
        if result.questions_asked:
            summary += "Questions Asked:\n"
            for i, question in enumerate(result.questions_asked, 1):
                summary += f"  {i}. {question}\n"
            summary += "\n"
        
        self.console.print(Panel(
            summary.strip(),
            title="Intent Detection Results",
            border_style="green"
        ))
    
    def get_intent_recommendations(self, intent: IntentType) -> List[str]:
        """Get template recommendations based on intent."""
        recommendations = {
            IntentType.INFORMATION_REQUEST: [
                "business_inquiry",
                "business_formal_standard"
            ],
            IntentType.ACTION_REQUIRED: [
                "business_formal_standard",
                "business_inquiry"
            ],
            IntentType.FOLLOW_UP: [
                "business_formal_standard",
                "casual_check_in"
            ],
            IntentType.INTRODUCTION: [
                "business_formal_standard",
                "casual_friendly"
            ],
            IntentType.APOLOGY: [
                "business_formal_standard"
            ],
            IntentType.THANK_YOU: [
                "business_formal_standard",
                "casual_friendly"
            ],
            IntentType.SALES_PITCH: [
                "sales_persuasive",
                "sales_follow_up"
            ],
            IntentType.ANNOUNCEMENT: [
                "business_formal_standard"
            ],
            IntentType.INQUIRY: [
                "business_inquiry",
                "casual_friendly"
            ]
        }
        
        return recommendations.get(intent, ["business_formal_standard"])
    
    def suggest_email_parameters(self, intent_result: IntentResult) -> Dict[str, Any]:
        """Suggest email parameters based on intent analysis."""
        suggestions = {
            "subject_tone": "Professional" if intent_result.formality != FormalityLevel.CASUAL else "Friendly",
            "opening_style": "Direct" if intent_result.urgency in [UrgencyLevel.HIGH, UrgencyLevel.URGENT] else "Warm",
            "closing_style": "Formal" if intent_result.formality == FormalityLevel.FORMAL else "Casual",
            "length_preference": "Concise" if intent_result.urgency == UrgencyLevel.URGENT else "Detailed",
            "include_call_to_action": intent_result.primary_intent in [IntentType.ACTION_REQUIRED, IntentType.SALES_PITCH]
        }
        
        return suggestions