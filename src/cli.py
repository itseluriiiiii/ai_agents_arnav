"""
Command Line Interface for AI Email Agent.

This module provides a comprehensive CLI interface using Click for all email agent
functionalities including drafting, learning, template management, and profile management.
"""

import click
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
import sys

from .ai_engine import AIEngine, OllamaConfig
from .style_analyzer import StyleAnalyzer
from .template_manager import TemplateManager
from .intent_detector import IntentDetector
from .email_generator import EmailGenerator

console = Console()


# Global context for CLI
class CLIContext:
    def __init__(self):
        self.ai_engine: Optional[AIEngine] = None
        self.style_analyzer: Optional[StyleAnalyzer] = None
        self.template_manager: Optional[TemplateManager] = None
        self.intent_detector: Optional[IntentDetector] = None
        self.email_generator: Optional[EmailGenerator] = None
        self.current_user: Optional[str] = None


# Create context object
ctx_obj = CLIContext()


@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--user', '-u', help='User ID or email address')
@click.version_option(version='1.0.0', prog_name='Email Agent')
@click.pass_context
def cli(ctx, config, user):
    """AI Email Agent - Intelligent email drafting assistant."""
    global ctx_obj
    
    ctx.ensure_object(dict)
    
    # Initialize components
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Initializing AI Email Agent...", total=100)
        
        try:
            # Initialize AI Engine
            progress.update(task, advance=20)
            ctx_obj.ai_engine = AIEngine()
            
            # Initialize Style Analyzer
            progress.update(task, advance=20)
            ctx_obj.style_analyzer = StyleAnalyzer()
            
            # Initialize Template Manager
            progress.update(task, advance=20)
            ctx_obj.template_manager = TemplateManager()
            
            # Initialize Intent Detector
            progress.update(task, advance=20)
            ctx_obj.intent_detector = IntentDetector(ctx_obj.ai_engine)
            
            # Initialize Email Generator
            progress.update(task, advance=20)
            ctx_obj.email_generator = EmailGenerator(
                ctx_obj.ai_engine,
                ctx_obj.template_manager,
                ctx_obj.style_analyzer,
                ctx_obj.intent_detector
            )
            
            # Set current user
            if user:
                ctx_obj.current_user = user
            
            progress.update(task, completed=100)
            
        except Exception as e:
            console.print(f"[red]Error initializing Email Agent: {e}[/red]")
            sys.exit(1)
    
    ctx.obj['cli_context'] = ctx_obj
    console.print("[green]+ AI Email Agent initialized successfully[/green]")


@cli.command()
@click.option('--topic', '-t', help='Email topic or subject')
@click.option('--recipient', '-r', help='Email recipient')
@click.option('--context', '-c', help='Additional context for the email')
@click.option('--template', help='Specific template to use')
@click.option('--style-profile', help='User style profile to use')
@click.option('--no-interactive', is_flag=True, help='Skip interactive prompts')
@click.pass_context
def draft(ctx, topic, recipient, context, template, style_profile, no_interactive):
    """Draft an email using AI assistance."""
    cli_ctx = ctx.obj['cli_context']
    if style_profile:
        cli_ctx.current_user = style_profile

    
    console.print("[bold blue] Email Drafting Assistant[/bold blue]")
    console.print()
    
    # Collect information
    if not topic:
        topic = Prompt.ask("What is the main topic or purpose of this email?")
    
    if not recipient:
        recipient = Prompt.ask("Who is the recipient?", default="")
    
    if not context:
        context = Prompt.ask("Any additional context or details?", default="")
    
    # Get user profile
    user_profile = None
    if cli_ctx.current_user:
        user_profile = cli_ctx.style_analyzer.load_profile(cli_ctx.current_user)
        if not user_profile:
            console.print(f"[yellow]No profile found for {cli_ctx.current_user}[/yellow]")
            if Confirm.ask("Would you like to use a default profile?"):
                user_profile = cli_ctx.style_analyzer.create_profile(
                    cli_ctx.current_user, 
                    cli_ctx.current_user
                )
    
    try:
        # Generate email - feedback is handled internally by EmailGenerator
        result = cli_ctx.email_generator.generate_email(
            topic=topic,
            recipient=recipient,
            context=context,
            user_profile=user_profile,
            template_name=template,
            interactive=not no_interactive
        )
        
        # Display result
        console.print()
        console.print(Panel(
            f"Subject: {result['subject']}\n\n{result['body']}",
            title="Generated Email",
            border_style="green"
        ))
        
        # Offer to save
        if Confirm.ask("Save this email draft?"):
            save_path = Prompt.ask("Save to file (default: email_draft.txt)", default="email_draft.txt")
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"Subject: {result['subject']}\n\n{result['body']}")
            console.print(f"[green]Email saved to {save_path}[/green]")
            
    except Exception as e:
        console.print(f"[red]Error generating email: {e}[/red]")


@cli.group()
def learn():
    """Learn and manage user writing styles."""
    pass


@learn.command()
@click.option('--email-file', '-f', help='Single email file to analyze')
@click.option('--email-dir', '-d', help='Directory containing email files')
@click.option('--text', help='Email text content directly')
@click.option('--user-id', help='User ID for the profile (defaults to current user)')
@click.pass_context
def from_emails(ctx, email_file, email_dir, text, user_id):
    """Learn writing style from email examples."""
    cli_ctx = ctx.obj['cli_context']
    
    target_user = user_id or cli_ctx.current_user
    if not target_user:
        console.print("[red]Error: User ID required. Use --user-id or --user flag on main command[/red]")
        return
    
    email_contents = []
    
    # Collect email content from different sources
    if text:
        email_contents.append(text)
    
    if email_file:
        try:
            with open(email_file, 'r', encoding='utf-8') as f:
                email_contents.append(f.read())
            console.print(f"[green]+ Loaded email from {email_file}[/green]")
        except Exception as e:
            console.print(f"[red]Error reading email file: {e}[/red]")
            return
    
    if email_dir:
        email_dir_path = Path(email_dir)
        if email_dir_path.exists():
            for email_file in email_dir_path.glob('*.txt'):
                try:
                    with open(email_file, 'r', encoding='utf-8') as f:
                        email_contents.append(f.read())
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not read {email_file}: {e}[/yellow]")
            
            console.print(f"[green]+ Loaded {len(email_contents)} emails from directory[/green]")
        else:
            console.print(f"[red]Error: Directory {email_dir} not found[/red]")
            return
    
    if not email_contents:
        console.print("[red]Error: No email content provided[/red]")
        return
    
    # Learn from emails
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Analyzing writing styles...", total=100)
        
        # Load or create profile
        profile = cli_ctx.style_analyzer.load_profile(target_user)
        if not profile:
            profile = cli_ctx.style_analyzer.create_profile(target_user, f"{target_user}@example.com")
        
        progress.update(task, advance=50)
        
        # Learn from emails
        updated_profile = cli_ctx.style_analyzer.learn_from_emails(profile, email_contents)
        
        progress.update(task, advance=50)
        
        # Save profile
        cli_ctx.style_analyzer.save_profile(updated_profile)
        
        progress.update(task, completed=100)
    
    console.print(f"[green]+ Successfully updated writing style profile for {target_user}[/green]")
    console.print(f"Analyzed {len(email_contents)} emails")
    console.print(f"Profile confidence: {updated_profile.confidence_score:.1%}")
    
    # Display style summary
    style_text = cli_ctx.style_analyzer.get_style_profile_as_text(updated_profile)
    console.print(Panel(style_text[:500] + "..." if len(style_text) > 500 else style_text,
                        title="Style Profile Summary",
                        border_style="blue"))


@learn.command()
@click.option('--user-id', help='User ID for the profile')
@click.pass_context
def interactive(ctx, user_id):
    """Create or update writing style profile interactively."""
    cli_ctx = ctx.obj['cli_context']
    
    target_user = user_id or cli_ctx.current_user
    if not target_user:
        console.print("[red]Error: User ID required[/red]")
        return
    
    console.print("[bold blue] Interactive Style Profile Setup[/bold blue]")
    console.print()
    
    # Collect style preferences
    console.print("Let's set up your writing style preferences...")
    
    formality = Prompt.ask(
        "How formal do you typically write?",
        choices=["casual", "professional", "formal"],
        default="professional"
    )
    
    tone = Prompt.ask(
        "What's your typical tone?",
        choices=["friendly", "neutral", "serious", "enthusiastic"],
        default="neutral"
    )
    
    directness = Prompt.ask(
        "How direct is your communication?",
        choices=["very direct", "moderately direct", "indirect"],
        default="moderately direct"
    )
    
    greeting = Prompt.ask(
        "What's your typical greeting?",
        default="Hi"
    )
    
    signature = Prompt.ask(
        "What's your typical closing/signature?",
        default="Best regards"
    )
    
    # Create or update profile
    profile = cli_ctx.style_analyzer.load_profile(target_user)
    if not profile:
        email_addr = Prompt.ask("What's your email address?")
        profile = cli_ctx.style_analyzer.create_profile(target_user, email_addr)
    
    # Update profile with preferences
    formality_score = {"casual": 0.2, "professional": 0.6, "formal": 0.9}[formality]
    directness_score = {"very direct": 0.9, "moderately direct": 0.6, "indirect": 0.3}[directness]
    
    profile.style_metrics.formality_score = formality_score
    profile.style_metrics.directness_score = directness_score
    profile.style_metrics.greeting_patterns = [greeting]
    profile.style_metrics.signature_patterns = [signature]
    
    cli_ctx.style_analyzer.save_profile(profile)
    
    console.print(f"[green]+ Style profile created for {target_user}[/green]")


@cli.group()
def template():
    """Manage email templates."""
    pass


@template.command()
@click.option('--category', help='Filter by template category')
@click.option('--tag', help='Filter by template tag (can be used multiple times)', multiple=True)
@click.pass_context
def list(ctx, category, tag):
    """List available email templates."""
    cli_ctx = ctx.obj['cli_context']
    
    templates = cli_ctx.template_manager.list_templates(category, list(tag) if tag else None)
    
    if not templates:
        console.print("[yellow]No templates found matching the criteria[/yellow]")
        return
    
    table = Table(title="Available Email Templates")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Description", style="green")
    table.add_column("Tags", style="yellow")
    table.add_column("Variables", style="blue")
    
    for template in templates:
        table.add_row(
            template.name,
            template.category,
            template.description[:50] + "..." if len(template.description) > 50 else template.description,
            ", ".join(template.tags[:3]),
            str(len(template.variables))
        )
    
    console.print(table)


@template.command()
@click.argument('name')
@click.option('--show-variables', is_flag=True, help='Show template variables')
@click.pass_context
def preview(ctx, name, show_variables):
    """Preview a template structure."""
    cli_ctx = ctx.obj['cli_context']
    
    template = cli_ctx.template_manager.get_template(name)
    if not template:
        console.print(f"[red]Template '{name}' not found[/red]")
        return
    
    console.print(Panel(
        f"Name: {template.name}\n"
        f"Category: {template.category}\n"
        f"Description: {template.description}\n"
        f"Tags: {', '.join(template.tags)}",
        title="Template Information",
        border_style="blue"
    ))
    
    if show_variables:
        console.print("\n[bold]Variables:[/bold]")
        for var in template.variables:
            console.print(f"  • {var}")
    
    console.print(f"\n[bold]Subject Template:[/bold]")
    console.print(Syntax(template.subject_template, "jinja2", theme="monokai", line_numbers=False))
    
    console.print(f"\n[bold]Body Template:[/bold]")
    console.print(Syntax(template.body_template, "jinja2", theme="monokai", line_numbers=True))


@template.command()
@click.argument('name')
@click.argument('category')
@click.argument('description')
@click.option('--subject', default="{{ subject }}", help='Subject template')
@click.pass_context
def create(ctx, name, category, description, subject):
    """Create a new custom template interactively."""
    cli_ctx = ctx.obj['cli_context']
    
    console.print("[bold blue] Create Custom Template[/bold blue]")
    console.print(f"Name: {name}")
    console.print(f"Category: {category}")
    console.print(f"Description: {description}")
    console.print()
    
    # Get template body
    console.print("Enter the template body (press Enter twice to finish):")
    body_lines = []
    while True:
        line = Prompt.ask("")
        if line == "" and len(body_lines) > 0 and body_lines[-1] == "":
            break
        body_lines.append(line)
    
    body = "\n".join(body_lines[:-1])  # Remove the last empty line
    
    # Create template
    template = cli_ctx.template_manager.create_custom_template(
        name=name,
        category=category,
        description=description,
        subject_template=subject,
        body_template=body
    )
    
    console.print(f"[green]+ Template '{name}' created successfully[/green]")
    
    # Offer to save
    if Confirm.ask("Save this template to file?"):
        cli_ctx.template_manager.save_template_to_file(name)
        console.print("[green]Template saved to file[/green]")


@cli.group()
def profile():
    """Manage user writing style profiles."""
    pass


@profile.command()
@click.pass_context
def list(ctx):
    """List all user profiles."""
    cli_ctx = ctx.obj['cli_context']
    
    profiles = cli_ctx.style_analyzer.list_profiles()
    
    if not profiles:
        console.print("[yellow]No profiles found[/yellow]")
        return
    
    table = Table(title="User Profiles")
    table.add_column("User ID", style="cyan", no_wrap=True)
    table.add_column("Email", style="green")
    table.add_column("Analyzed Emails", style="yellow")
    table.add_column("Confidence", style="magenta")
    table.add_column("Last Updated", style="blue")
    
    for profile_id in profiles:
        profile = cli_ctx.style_analyzer.load_profile(profile_id)
        if profile:
            table.add_row(
                profile.user_id,
                profile.email_address,
                str(profile.analyzed_emails),
                f"{profile.confidence_score:.1%}",
                profile.updated_at.strftime("%Y-%m-%d %H:%M")
            )
    
    console.print(table)


@profile.command()
@click.argument('user_id')
@click.pass_context
def show(ctx, user_id):
    """Show detailed information about a user profile."""
    cli_ctx = ctx.obj['cli_context']
    
    profile = cli_ctx.style_analyzer.load_profile(user_id)
    if not profile:
        console.print(f"[red]Profile '{user_id}' not found[/red]")
        return
    
    # Display profile details
    style_text = cli_ctx.style_analyzer.get_style_profile_as_text(profile)
    console.print(Panel(style_text, title=f"Profile: {user_id}", border_style="green"))


@profile.command()
@click.argument('user_id')
@click.pass_context
def delete(ctx, user_id):
    """Delete a user profile."""
    cli_ctx = ctx.obj['cli_context']
    
    if not Confirm.ask(f"Are you sure you want to delete profile '{user_id}'?"):
        return
    
    profile_file = Path("profiles") / f"{user_id}.json"
    if profile_file.exists():
        profile_file.unlink()
        console.print(f"[green]+ Profile '{user_id}' deleted[/green]")
    else:
        console.print(f"[red]Profile '{user_id}' not found[/red]")


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and configuration."""
    cli_ctx = ctx.obj['cli_context']
    
    console.print("[bold blue]AI Email Agent Status[/bold blue]")
    console.print()
    
    # Check AI Engine
    try:
        test_response = cli_ctx.ai_engine.test_model("Hello")
        console.print("[green]+ AI Engine: Connected and responsive[/green]")
        console.print(f"  Model: {cli_ctx.ai_engine.config.model}")
        console.print(f"  Host: {cli_ctx.ai_engine.config.host}")
    except Exception as e:
        console.print(f"[red]X AI Engine: {e}[/red]")
    
    # Check templates
    template_count = len(cli_ctx.template_manager.templates)
    console.print(f"[green]+ Templates: {template_count} loaded[/green]")
    
    # Check profiles
    profile_count = len(cli_ctx.style_analyzer.list_profiles())
    console.print(f"[green]+ Profiles: {profile_count} user profiles[/green]")
    
    # Current user
    if cli_ctx.current_user:
        profile = cli_ctx.style_analyzer.load_profile(cli_ctx.current_user)
        if profile:
            console.print(f"[green]+ Current User: {cli_ctx.current_user} (confidence: {profile.confidence_score:.1%})[/green]")
        else:
            console.print(f"[yellow]! Current User: {cli_ctx.current_user} (no profile found)[/yellow]")
    else:
        console.print("[yellow]! No current user specified[/yellow]")


if __name__ == '__main__':
    cli()