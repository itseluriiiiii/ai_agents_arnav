"""
Template Manager - Handles email templates with Jinja2.

This module provides functionality to manage, render, and validate email templates
using Jinja2 templating engine with support for multiple template categories
and dynamic content insertion.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from jinja2 import Environment, FileSystemLoader, Template, TemplateError
from pydantic import BaseModel, Field, validator
from rich.console import Console

console = Console()


class EmailTemplate(BaseModel):
    """Represents an email template with metadata."""
    name: str
    category: str  # business, casual, sales
    description: str
    subject_template: str
    body_template: str
    variables: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    @validator('variables', pre=True, always=True)
    def extract_variables(cls, v, values):
        """Extract variables from templates."""
        variables = set()
        
        # Extract from subject template
        if 'subject_template' in values:
            subject_vars = [
                var for var in values['subject_template'].split()
                if var.startswith('{{') and var.endswith('}}')
            ]
            variables.update([var.strip('{} ') for var in subject_vars])
        
        # Extract from body template
        if 'body_template' in values:
            body_vars = [
                var for var in values['body_template'].split()
                if var.startswith('{{') and var.endswith('}}')
            ]
            variables.update([var.strip('{} ') for var in body_vars])
        
        return list(variables)


class TemplateManager:
    """Manages email templates using Jinja2."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path("templates")
        self.templates: Dict[str, EmailTemplate] = {}
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.console = console
        self._load_builtin_templates()
        self._load_custom_templates()
    
    def _load_builtin_templates(self):
        """Load built-in email templates."""
        builtin_templates = {
            "business_formal_standard": EmailTemplate(
                name="business_formal_standard",
                category="business",
                description="Standard formal business email template",
                subject_template="{{ subject }}",
                body_template="""{% if greeting %}{{ greeting }} {{ recipient_name }},{% endif %}

{{ opening }}

{% if context %}{{ context }}

{% endif %}{% if call_to_action %}{{ call_to_action }}

{% endif %}{% if closing %}{{ closing }}

{% endif %}{{ signature }}""",
                variables=["subject", "greeting", "recipient_name", "opening", "context", "call_to_action", "closing", "signature"],
                tags=["formal", "professional", "standard"]
            ),
            
            "business_inquiry": EmailTemplate(
                name="business_inquiry",
                category="business",
                description="Business inquiry email template",
                subject_template="Inquiry: {{ subject }}",
                body_template="""Dear {{ recipient_name }},

I hope this email finds you well. My name is {{ sender_name }}{% if sender_role is defined and sender_role and sender_role|trim %} and I am {{ sender_role }}{% endif %}{% if sender_company is defined and sender_company and sender_company|trim %} at {{ sender_company }}{% endif %}.

I am writing to {{ inquiry_purpose }}{% if context %}. {{ context }}{% endif %}

{% if call_to_action %}{{ call_to_action }}

{% endif %}Thank you for your time and consideration. I look forward to hearing from you.

Best regards,

{{ sender_name }}
{% if sender_role is defined and sender_role and sender_role|trim %}{{ sender_role }}{% endif %}
{% if sender_company is defined and sender_company and sender_company|trim %}{{ sender_company }}{% endif %}
{% if contact_info is defined and contact_info and contact_info|trim %}{{ contact_info }}{% endif %}""",
                variables=["subject", "recipient_name", "sender_name", "sender_role", "sender_company", "inquiry_purpose", "context", "call_to_action", "contact_info"],
                tags=["inquiry", "formal", "business"]
            ),
            
            "casual_friendly": EmailTemplate(
                name="casual_friendly",
                category="casual",
                description="Friendly casual email template",
                subject_template="{{ subject }}",
                body_template="""{% if greeting %}{{ greeting }} {{ recipient_name }},{% endif %}

{{ opening }}

{% if context %}{{ context }}

{% endif %}{% if call_to_action %}{{ call_to_action }}

{% endif %}Talk soon,

{{ signature }}""",
                variables=["subject", "greeting", "recipient_name", "opening", "context", "call_to_action", "signature"],
                tags=["casual", "friendly", "informal"]
            ),
            
"casual_check_in": EmailTemplate(
                name="casual_check_in",
                category="casual",
                description="Casual check-in email template",
                subject_template="Checking in: {{ subject }}",
                body_template="""Hi {{ recipient_name }},

Just wanted to check in and see how things are going{% if context %} regarding {{ context }}{% endif %}.

{% if question %}{{ question }}

{% endif %}Hope everything's going well on your end!

Best,

{{ sender_name }}""",
                tags=["check-in", "casual", "follow-up"]
            ),
            
            "sales_persuasive": EmailTemplate(
                name="sales_persuasive",
                category="sales",
                description="Persuasive sales email template",
                subject_template="{{ subject }}",
                body_template="""Dear {{ recipient_name }},

{{ hook }}

I'm {{ sender_name }} from {{ company_name }}, and I help {{ target_audience }} achieve {{ key_benefit }}.

{% if problem_statement %}{{ problem_statement }}

{% endif %}Our solution helps you:
{% if benefits %}{% for benefit in benefits %}• {{ benefit }}
{% endfor %}{% endif %}

{% if call_to_action %}{{ call_to_action }}

{% endif %}Would you be open to a brief {{ meeting_duration }}-minute call next week to discuss how we can help you {{ specific_outcome }}?

Best regards,

{{ sender_name }}
{% if sender_title is defined and sender_title and sender_title|trim %}{{ sender_title }}{% endif %}
{% if company_name is defined and company_name and company_name|trim %}{{ company_name }}{% endif %}
{% if contact_info is defined and contact_info and contact_info|trim %}{{ contact_info }}{% endif %}""",
                tags=["sales", "persuasive", "business"]
            ),
            
            "sales_follow_up": EmailTemplate(
                name="sales_follow_up",
                category="sales",
                description="Sales follow-up email template",
                subject_template="Following up: {{ subject }}",
                body_template="""Hi {{ recipient_name }},

Following up on my previous email{% if previous_context %} regarding {{ previous_context }}{% endif %}.

I wanted to {{ follow_up_reason }}{% if additional_value %} and share that {{ additional_value }}{% endif %}.

{% if question %}{{ question }}

{% endif %}Are you available for a quick chat this week?

Best,

{{ sender_name }}
{{ company_name }}""",
                tags=["sales", "follow-up", "business"]
            )
        }
        
        self.templates.update(builtin_templates)
    
    def _load_custom_templates(self):
        """Load custom templates from file system."""
        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True, exist_ok=True)
            return
        
        for template_file in self.template_dir.rglob("*.j2"):
            try:
                self._load_template_file(template_file)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to load {template_file}: {e}[/yellow]")
    
    def _load_template_file(self, file_path: Path):
        """Load a single template file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to extract metadata from JSON front matter
        metadata = {}
        template_content = content
        
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata = json.loads(parts[1])
                    template_content = parts[2]
                except json.JSONDecodeError:
                    template_content = content
        
        # Create template from file content
        category = file_path.parent.name
        template_name = file_path.stem
        
        template = EmailTemplate(
            name=template_name,
            category=category,
            description=metadata.get('description', f"Custom {category} template"),
            subject_template=metadata.get('subject_template', "{{ subject }}"),
            body_template=template_content,
            variables=metadata.get('variables', []),
            tags=metadata.get('tags', [])
        )
        
        self.templates[template_name] = template
    
    def render_template(self, template_name: str, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render an email template with provided variables."""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        
        try:
            # Render subject
            subject_template = self.jinja_env.from_string(template.subject_template)
            subject = subject_template.render(**variables)
            
            # Render body
            body_template = self.jinja_env.from_string(template.body_template)
            body = body_template.render(**variables)
            
            return {
                "subject": subject.strip(),
                "body": body.strip(),
                "template_name": template_name,
                "category": template.category
            }
            
        except TemplateError as e:
            raise ValueError(f"Template rendering error: {e}")
    
    def list_templates(self, category: Optional[str] = None, 
                      tags: Optional[List[str]] = None) -> List[EmailTemplate]:
        """List available templates with optional filtering."""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        return templates
    
    def get_template(self, name: str) -> Optional[EmailTemplate]:
        """Get a specific template by name."""
        return self.templates.get(name)
    
    def add_template(self, template: EmailTemplate):
        """Add a new template."""
        self.templates[template.name] = template
    
    def create_custom_template(self, name: str, category: str, description: str,
                             subject_template: str, body_template: str,
                             tags: Optional[List[str]] = None) -> EmailTemplate:
        """Create a new custom template."""
        template = EmailTemplate(
            name=name,
            category=category,
            description=description,
            subject_template=subject_template,
            body_template=body_template,
            tags=tags or []
        )
        
        self.add_template(template)
        return template
    
    def save_template_to_file(self, template_name: str, file_path: Optional[Path] = None):
        """Save a template to a file."""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        
        if not file_path:
            file_path = self.template_dir / template.category / f"{template.name}.j2"
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create JSON front matter
        metadata = {
            "description": template.description,
            "subject_template": template.subject_template,
            "variables": template.variables,
            "tags": template.tags
        }
        
        content = f"---\n{json.dumps(metadata, indent=2)}\n---\n\n{template.body_template}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def validate_template(self, template_name: str, 
                         variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate a template and check for missing variables."""
        if template_name not in self.templates:
            return {"valid": False, "error": "Template not found"}
        
        template = self.templates[template_name]
        
        try:
            # Test rendering with dummy variables
            test_vars = variables or {var: "test" for var in template.variables}
            result = self.render_template(template_name, test_vars)
            
            return {
                "valid": True,
                "subject_length": len(result["subject"]),
                "body_length": len(result["body"]),
                "required_variables": template.variables
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "required_variables": template.variables
            }
    
    def get_template_categories(self) -> List[str]:
        """Get all available template categories."""
        return list(set(template.category for template in self.templates.values()))
    
    def search_templates(self, query: str) -> List[EmailTemplate]:
        """Search templates by name, description, or tags."""
        query_lower = query.lower()
        results = []
        
        for template in self.templates.values():
            if (query_lower in template.name.lower() or 
                query_lower in template.description.lower() or
                any(query_lower in tag.lower() for tag in template.tags)):
                results.append(template)
        
        return results