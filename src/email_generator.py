"""
Email Generator - Main orchestrator for email generation.

This module coordinates all components to generate emails based on user input,
style analysis, intent detection, template selection, and AI-powered content generation.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from rich.console import Console

from .ai_engine import AIEngine
from .style_analyzer import StyleAnalyzer, UserProfile
from .template_manager import TemplateManager, EmailTemplate
from .intent_detector import IntentDetector, IntentResult, IntentType, EmailType

console = Console()


@dataclass
class EmailGenerationRequest:
    """Request object for email generation."""
    topic: str
    recipient: str
    context: str = ""
    user_profile: Optional[UserProfile] = None
    template_name: Optional[str] = None
    interactive: bool = True
    additional_variables: Dict[str, Any] = None


@dataclass
class EmailGenerationResult:
    """Result object for email generation."""
    subject: str
    body: str
    template_used: str
    intent_result: IntentResult
    style_applied: bool
    variables_used: Dict[str, Any]
    generation_time: float
    confidence_score: float


class EmailGenerator:
    """Main orchestrator for email generation."""
    
    def __init__(self, ai_engine: AIEngine, template_manager: TemplateManager,
                 style_analyzer: StyleAnalyzer, intent_detector: IntentDetector):
        self.ai_engine = ai_engine
        self.template_manager = template_manager
        self.style_analyzer = style_analyzer
        self.intent_detector = intent_detector
        self.console = console
    
    def _generate_email_internal(self, request: EmailGenerationRequest) -> EmailGenerationResult:
        """Generate an email based on the request."""
        import time
        start_time = time.time()
        
        self.console.print("[bold blue] Generating Email...[/bold blue]")
        
        # Step 1: Detect intent
        self.console.print(" Analyzing intent...")
        intent_result = self.intent_detector.detect_intent(
            user_request=request.topic,
            context=request.context,
            recipient=request.recipient,
            interactive=request.interactive
        )
        
        # Step 2: Select appropriate template
        self.console.print(" Selecting template...")
        template = self._select_template(
            intent_result, 
            request.template_name,
            request.user_profile
        )
        
        # Step 3: Prepare variables for template rendering
        self.console.print("Preparing content...")
        template_variables = self._prepare_template_variables(
            request, intent_result, template
        )
        
        # Step 4: Generate AI content if needed
        ai_content = self._generate_ai_content(request, intent_result, template_variables)
        
        # Step 5: Render template
        self.console.print(" Rendering email...")
        rendered_email = self._render_template(template, ai_content, template_variables)
        
        # Step 6: Apply style adjustments
        if request.user_profile and request.user_profile.confidence_score > 0.3:
            self.console.print(" Applying style adjustments...")
            rendered_email = self._apply_style_adjustments(
                rendered_email, request.user_profile, intent_result
            )
        
        generation_time = time.time() - start_time
        
        result = EmailGenerationResult(
            subject=rendered_email["subject"],
            body=rendered_email["body"],
            template_used=template.name,
            intent_result=intent_result,
            style_applied=request.user_profile is not None and request.user_profile.confidence_score > 0.3,
            variables_used=template_variables,
            generation_time=generation_time,
            confidence_score=self._calculate_confidence_score(intent_result, request.user_profile)
        )
        
        self.console.print(f"[green]+ Email generated in {generation_time:.2f}s[/green]")
        
        return result
    
    def generate_email(self, topic: str, recipient: str, context: str = "",
                      user_profile: Optional[UserProfile] = None, 
                      template_name: Optional[str] = None,
                      interactive: bool = True,
                      additional_variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Simplified interface for email generation.
        
        Returns a dictionary with 'subject' and 'body' keys.
        """
        request = EmailGenerationRequest(
            topic=topic,
            recipient=recipient,
            context=context,
            user_profile=user_profile,
            template_name=template_name,
            interactive=interactive,
            additional_variables=additional_variables or {}
        )
        
        result = self._generate_email_internal(request)
        
        return {
            "subject": result.subject,
            "body": result.body,
            "metadata": {
                "template_used": result.template_used,
                "intent": result.intent_result.primary_intent.value,
                "style_applied": result.style_applied,
                "generation_time": result.generation_time,
                "confidence": result.confidence_score
            }
        }
    
    def _select_template(self, intent_result: IntentResult, 
                        preferred_template: Optional[str],
                        user_profile: Optional[UserProfile]) -> EmailTemplate:
        """Select the most appropriate template for the email."""
        # If user specified a template, try to use it
        if preferred_template:
            template = self.template_manager.get_template(preferred_template)
            if template:
                return template
            else:
                self.console.print(f"[yellow]Template '{preferred_template}' not found, selecting automatically[/yellow]")
        
        # Get recommendations based on intent
        recommended_templates = self.intent_detector.get_intent_recommendations(
            intent_result.primary_intent
        )
        
        # Try recommended templates in order
        for template_name in recommended_templates:
            template = self.template_manager.get_template(template_name)
            if template:
                # Check if template matches email type
                if self._template_matches_type(template, intent_result.email_type):
                    return template
        
        # Fallback: find any template that matches the email type
        all_templates = self.template_manager.list_templates()
        for template in all_templates:
            if self._template_matches_type(template, intent_result.email_type):
                return template
        
        # Last resort: use a default template
        default_template = self.template_manager.get_template("business_formal_standard")
        if default_template:
            return default_template
        
        # If no templates available, create a basic one
        return self._create_basic_template()
    
    def _template_matches_type(self, template: EmailTemplate, email_type: EmailType) -> bool:
        """Check if template matches the email type."""
        return template.category == email_type.value
    
    def _prepare_template_variables(self, request: EmailGenerationRequest,
                                  intent_result: IntentResult,
                                  template: EmailTemplate) -> Dict[str, Any]:
        """Prepare variables for template rendering."""
        # Base variables
        variables = {
            "recipient_name": self._extract_recipient_name(request.recipient),
            "sender_name": "User",  # Default to User
            "subject": request.topic,
            "topic": request.topic,
            "context": request.context,
            "urgency": intent_result.urgency.value,
            "formality": intent_result.formality.value
        }
        
        # Add user profile specific variables
        if request.user_profile:
            style = request.user_profile.style_metrics
            variables.update({
                "signature": self._select_signature(style.signature_patterns, intent_result.formality),
                "greeting": self._select_greeting(style.greeting_patterns, intent_result.formality),
                "closing": self._select_closing(style.signature_patterns, intent_result.formality),
                "sender_name": request.user_profile.user_id if "@" not in request.user_profile.user_id else "User"
            })
            
            # Add preference-based variables (like sender_role, sender_company)
            if request.user_profile.preferences:
                variables.update(request.user_profile.preferences)
        
        # Add intent-specific variables
        intent_suggestions = self.intent_detector.suggest_email_parameters(intent_result)
        variables.update(intent_suggestions)
        
        # Final cleanup: Remove empty strings, spaces, or single dots from variables
        # to prevent them from triggering {% if variable %} in templates
        keys_to_clean = ["sender_role", "sender_company", "inquiry_purpose", "call_to_action", "contact_info"]
        for key in keys_to_clean:
            if key in variables:
                val = str(variables[key]).strip()
                if not val or val.lower() in [".", "n/a", "none", "(role)", "(company)"]:
                    del variables[key]
        
        return variables
    
    def _generate_ai_content(self, request: EmailGenerationRequest,
                           intent_result: IntentResult,
                           template_variables: Dict[str, Any]) -> Dict[str, str]:
        """Generate AI content for specific parts of the email."""
        ai_content = {}
        
        # Get style profile text if available
        style_profile = ""
        if request.user_profile:
            style_profile = self.style_analyzer.get_style_profile_as_text(request.user_profile)
        
        # Generate main content
        try:
            ai_generated = self.ai_engine.generate_email(
                context=request.context,
                recipient=request.recipient,
                topic=request.topic,
                intent=intent_result.primary_intent.value,
                style_profile=style_profile,
                sender_name=template_variables.get("sender_name", "User")
            )
            
            # Parse AI generated content
            parsed_result = self._parse_ai_response(ai_generated)
            ai_content.update(parsed_result)
            
            # Sanitize and map new simplified keys to template variables
            for key in ["purpose", "body", "next_step", "sender_role", "sender_company"]:
                if key in ai_content:
                    val = str(ai_content[key]).strip()
                    # Sanitize: If the AI returned a dummy value or placeholders, clear it
                    if val.lower() in [".", "n/a", "none", "(role)", "(company)"]:
                        val = ""
                    
                    if key == "purpose":
                        # Strip leading "to " if it exists to avoid "I am writing to to ..."
                        if val.lower().startswith("to "):
                            val = val[3:].strip()
                        ai_content["inquiry_purpose"] = val
                    elif key == "body":
                        ai_content["context"] = val
                    elif key == "next_step":
                        ai_content["call_to_action"] = val
                    elif key == "sender_role":
                        ai_content["sender_role"] = val
                    elif key == "sender_company":
                        ai_content["sender_company"] = val
            
            # Map main_content to context if AI used that key (support old/hallucinated keys)
            if "main_content" in ai_content and "context" not in ai_content:
                ai_content["context"] = ai_content["main_content"]
            
            # If JSON parsing failed and fallback returned main_content, 
            # ensure it doesn't contain raw JSON characters if it's very short or looks like JSON
            if "main_content" in ai_content and not any(k in ai_content for k in ["body", "context"]):
                content = ai_content["main_content"]
                if content.strip().startswith('{') or '"purpose":' in content:
                    # It's likely a failed JSON parse that leaked into the content
                    ai_content["context"] = self._parse_ai_generated_content(content.replace('{', '').replace('}', ''))
                else:
                    ai_content["context"] = content

            # If we have context, try to clean it up for first-person
            if ai_content.get("context"):
                ai_content["context"] = self._ensure_first_person(
                    ai_content["context"], 
                    request.recipient,
                    template_variables.get("sender_name", "")
                )
            
            # Final safety check: if context still missing, use raw AI content but cleaned
            if not ai_content.get("context"):
                ai_content["context"] = self._ensure_first_person(
                    self._parse_ai_generated_content(ai_generated), 
                    request.recipient,
                    template_variables.get("sender_name", "")
                )
                
            # Populate inquiry_purpose if missing but we have a topic
            if not ai_content.get("inquiry_purpose"):
                ai_content["inquiry_purpose"] = f"discuss {request.topic}"
            
        except Exception as e:
            self.console.print(f"[yellow]AI generation failed: {e}. Using fallback logic...[/yellow]")
            # Fallback to basic content
            raw_context = request.context or request.topic
            
            # Apply advanced cleanup even in fallback mode
            cleaned_context = self._ensure_first_person(
                raw_context, 
                request.recipient,
                template_variables.get("sender_name", "")
            )
            
            ai_content["main_content"] = cleaned_context
            ai_content["inquiry_purpose"] = f"discuss {request.topic}"
            ai_content["context"] = cleaned_context
        
        # Generate opening if not in template
        if "opening" not in template_variables:
            ai_content["opening"] = self._generate_opening(request, intent_result)
        
        # Generate call to action if needed
        if intent_result.primary_intent in [IntentType.ACTION_REQUIRED, IntentType.SALES_PITCH]:
            if "call_to_action" not in template_variables:
                ai_content["call_to_action"] = self._generate_call_to_action(request, intent_result)
        
        return ai_content
    
    def _render_template(self, template: EmailTemplate, 
                         ai_content: Dict[str, str],
                         variables: Dict[str, Any]) -> Dict[str, str]:
        """Render the email template with content and variables."""
        # Combine AI content with template variables
        render_variables = {**variables, **ai_content}
        
        # Aggressive cleanup one last time
        keys_to_clean = ["sender_role", "sender_company", "inquiry_purpose", "call_to_action", "contact_info"]
        for key in keys_to_clean:
            if key in render_variables:
                val = str(render_variables[key]).strip()
                if not val or val.lower() in [".", "n/a", "none", "(role)", "(company)"]:
                    del render_variables[key]
        
        # Render template
        try:
            result = self.template_manager.render_template(template.name, render_variables)
            return result
        except Exception as e:
            self.console.print(f"[yellow]Template rendering failed: {e}[/yellow]")
            # Fallback rendering
            return self._fallback_rendering(template, ai_content, render_variables)
    
    def _apply_style_adjustments(self, rendered_email: Dict[str, str],
                                user_profile: UserProfile,
                                intent_result: IntentResult) -> Dict[str, str]:
        """Apply user's writing style to the generated email."""
        # This is a simplified style adjustment
        # In a more advanced implementation, you could use AI to rewrite the content
        
        style = user_profile.style_metrics
        
        # Adjust formality level
        if style.formality_score > 0.7:
            # Make more formal
            rendered_email["body"] = self._make_more_formal(rendered_email["body"])
        elif style.formality_score < 0.3:
            # Make more casual
            rendered_email["body"] = self._make_more_casual(rendered_email["body"])
        
        # Adjust directness
        if style.directness_score < 0.4:
            # Make less direct (add hedging language)
            rendered_email["body"] = self._make_less_direct(rendered_email["body"])
        
        return rendered_email
    
    def _extract_recipient_name(self, recipient: str) -> str:
        """Extract the recipient's name from email address."""
        if "@" in recipient:
            return recipient.split("@")[0].replace(".", " ").title()
        return recipient
    
    def _select_signature(self, signatures: List[str], formality) -> str:
        """Select an appropriate signature based on formality."""
        if not signatures:
            return "Best regards"
        
        # Select signature based on formality level
        formality_level = formality.value
        
        if formality_level == "formal":
            formal_signatures = [s for s in signatures if any(
                word in s.lower() for word in ["sincerely", "regards", "respectfully"]
            )]
            if formal_signatures:
                return formal_signatures[0]
        
        if formality_level == "casual":
            casual_signatures = [s for s in signatures if any(
                word in s.lower() for word in ["best", "thanks", "cheers", "talk soon"]
            )]
            if casual_signatures:
                return casual_signatures[0]
        
        # Default to first signature
        return signatures[0]
    
    def _select_greeting(self, greetings: List[str], formality) -> str:
        """Select an appropriate greeting based on formality."""
        if not greetings:
            return "Hi"
        
        # Select greeting based on formality level
        formality_level = formality.value
        
        if formality_level == "formal":
            formal_greetings = [s for s in greetings if any(
                word in s.lower() for word in ["dear", "sir", "madam"]
            )]
            if formal_greetings:
                return formal_greetings[0]
        
        # Default to first greeting
        return greetings[0]
    
    def _select_closing(self, signatures: List[str], formality) -> str:
        """Select an appropriate closing based on formality."""
        return self._select_signature(signatures, formality)
    
    def _parse_ai_response(self, ai_content: str) -> Dict[str, str]:
        """Parse AI response, attempting to extract JSON data."""
        import json
        import re
        
        # 1. Try to find content inside markdown code blocks first
        code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_content, re.DOTALL)
        if code_block_match:
            json_str = code_block_match.group(1)
            try:
                return json.loads(json_str)
            except Exception:
                # Fall through to more aggressive methods
                pass

        # 2. Try to find the first '{' and last '}'
        start_idx = ai_content.find('{')
        end_idx = ai_content.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = ai_content[start_idx:end_idx+1]
            
            # Basic repairs for common AI JSON mistakes
            # Remove trailing commas before closing braces
            json_str = re.sub(r',\s*\}', '}', json_str)
            json_str = re.sub(r',\s*\]', ']', json_str)
            
            try:
                return json.loads(json_str)
            except Exception:
                # Try a more extreme cleanup: keep only what's needed for json.loads
                try:
                    # Replace smart quotes with straight quotes
                    json_str = json_str.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
                    return json.loads(json_str)
                except Exception:
                    pass
            
        # Fallback to string parsing if JSON fails
        return {"main_content": self._parse_ai_generated_content(ai_content)}

    def _ensure_first_person(self, text: str, recipient: str, sender_name: str = "") -> str:
        """Improve the text to ensure it's in first person and addresses recipient as 'you'."""
        import re
        recipient_name = self._extract_recipient_name(recipient)
        
        # 1. Strip redundant sender introductions (e.g., "I'm User...")
        if sender_name:
            # Matches "I'm User", "I am User", "User here", etc.
            text = re.sub(rf"^(I'm|I am|My name is)?\s*{sender_name}[\s,.]*", "", text, flags=re.IGNORECASE)
            # Remove "an AI Engineer" if it follows
            text = re.sub(r"^(an|a)?\s*AI Engineer[\s,.]*", "", text, flags=re.IGNORECASE)

        # 2. Fix third-person recipient references
        if recipient_name:
            # Fix "Ask Ravi if he" -> "I'd like to ask you if you"
            text = re.sub(rf'\bAsk {recipient_name} if (he|she) (has|can|is)\b', r'I would like to ask you if you \2', text, flags=re.IGNORECASE)
            text = re.sub(rf'\bAsk {recipient_name} if (he|she)\b', 'I would like to ask you if you', text, flags=re.IGNORECASE)
            text = re.sub(rf'\bAsk {recipient_name}\b', "I'd like to ask you", text, flags=re.IGNORECASE)
            text = re.sub(rf'\bTell {recipient_name}\b', "I'd like to tell you", text, flags=re.IGNORECASE)
            text = re.sub(rf'\bShow {recipient_name}\b', 'show you', text, flags=re.IGNORECASE)
            text = re.sub(rf'\bInvite {recipient_name}\b', 'invite you', text, flags=re.IGNORECASE)
            
            # General name-to-you replacement
            text = re.sub(rf'\b{recipient_name}\b', 'you', text, flags=re.IGNORECASE)

        # 3. Clean up generic phrases
        text = re.sub(r'\bAsk you if (he|she)\b', 'ask you if you', text, flags=re.IGNORECASE)
        text = re.sub(r'\bI want to show you how (he|she)\b', 'I want to show you how I', text, flags=re.IGNORECASE)
        
        # Ensure it doesn't start with a lowercase word if we stripped the start
        text = text.strip()
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
            
        return text

    def _parse_ai_generated_content(self, ai_content: str) -> str:
        """Parse AI generated content to extract the main body."""
        lines = ai_content.strip().split('\n')
        content_lines = []
        
        # Look for email body content
        in_body = False
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip obvious headers
            if any(header in line.lower() for header in ['subject:', 'from:', 'to:', 'date:']):
                continue
            
            # Start collecting body content
            if not in_body and len(line) > 10:
                in_body = True
            
            if in_body:
                content_lines.append(line)
        
        return '\n'.join(content_lines)
    
    def _generate_opening(self, request: EmailGenerationRequest, intent_result: IntentResult) -> str:
        """Generate an appropriate opening for the email."""
        opennings = {
            IntentType.INFORMATION_REQUEST: f"I hope this email finds you well. I'm writing to inquire about {request.topic}.",
            IntentType.ACTION_REQUIRED: f"I hope this email finds you well. I'm writing to request your assistance with {request.topic}.",
            IntentType.FOLLOW_UP: f"I'm following up on our previous discussion regarding {request.topic}.",
            IntentType.INTRODUCTION: f"I hope this email finds you well. I'd like to introduce you to {request.topic}.",
            IntentType.APOLOGY: f"I'm writing to apologize for the issue regarding {request.topic}.",
            IntentType.THANK_YOU: f"I'm writing to express my gratitude regarding {request.topic}.",
            IntentType.SALES_PITCH: f"I'm excited to share with you information about {request.topic}.",
            IntentType.ANNOUNCEMENT: f"I'm pleased to announce {request.topic}.",
            IntentType.INQUIRY: f"I'm writing to inquire about {request.topic}."
        }
        
        return opennings.get(intent_result.primary_intent, f"I hope this email finds you well. I'm writing to you about {request.topic}.")
    
    def _generate_call_to_action(self, request: EmailGenerationRequest, intent_result: IntentResult) -> str:
        """Generate an appropriate call to action."""
        if intent_result.primary_intent == IntentType.ACTION_REQUIRED:
            return f"Please let me know if you can assist with this by the end of this week."
        elif intent_result.primary_intent == IntentType.SALES_PITCH:
            return "Would you be available for a brief call next week to discuss this further?"
        else:
            return "I look forward to hearing from you soon."
    
    def _make_more_formal(self, text: str) -> str:
        """Make text more formal."""
        formal_replacements = {
            "hi": "Dear",
            "hey": "Dear",
            "thanks": "Thank you",
            "thanks a lot": "Thank you very much",
            "cool": "excellent",
            "awesome": "excellent",
            "gonna": "going to",
            "wanna": "want to",
            "kinda": "somewhat",
            "sorta": "somewhat"
        }
        
        text_lower = text.lower()
        for informal, formal in formal_replacements.items():
            text_lower = text_lower.replace(informal, formal)
        
        return text_lower
    
    def _make_more_casual(self, text: str) -> str:
        """Make text more casual."""
        casual_replacements = {
            "dear": "Hi",
            "sincerely": "Best",
            "regards": "Best",
            "thank you very much": "Thanks a lot",
            "i would appreciate": "I'd appreciate",
            "i am": "I'm",
            "you are": "you're",
            "we are": "we're"
        }
        
        for formal, casual in casual_replacements.items():
            text = text.replace(formal, casual)
        
        return text
    
    def _make_less_direct(self, text: str) -> str:
        """Make text less direct by adding hedging language."""
        hedges = [
            "I was wondering if you might",
            "Perhaps you could consider",
            "It might be helpful to",
            "You may want to think about"
        ]
        
        # This is a simple implementation
        # A more sophisticated version would use NLP to identify direct statements
        return text
    
    def _fallback_rendering(self, template: EmailTemplate,
                           ai_content: Dict[str, str],
                           variables: Dict[str, Any]) -> Dict[str, str]:
        """Fallback rendering if template rendering fails."""
        subject = variables.get("subject", "No Subject")
        body = ai_content.get("main_content", "")
        
        # Add basic structure
        if variables.get("greeting"):
            body = f"{variables['greeting']} {variables.get('recipient_name', '')},\n\n{body}"
        
        if variables.get("signature"):
            body = f"{body}\n\n{variables['signature']}"
        
        return {"subject": subject, "body": body}
    
    def _create_basic_template(self) -> EmailTemplate:
        """Create a basic fallback template."""
        return EmailTemplate(
            name="basic_fallback",
            category="business",
            description="Basic fallback template",
            subject_template="{{ subject }}",
            body_template="{{ main_content }}",
            variables=["subject", "main_content"]
        )
    
    def _calculate_confidence_score(self, intent_result: IntentResult,
                                   user_profile: Optional[UserProfile]) -> float:
        """Calculate overall confidence score for the generated email."""
        scores = [intent_result.confidence]
        
        if user_profile:
            scores.append(user_profile.confidence_score)
        else:
            scores.append(0.3)  # Low confidence without user profile
        
        return sum(scores) / len(scores)