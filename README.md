# AI Email Agent

An intelligent email drafting assistant that uses local AI to generate personalized emails based on your writing style, intent, and context.

## Features

- 🤖 **Local AI Integration**: Uses Ollama for privacy-focused email generation
- 📝 **Style Learning**: Analyzes your writing patterns to match your personal style
- 🎯 **Intent Detection**: Interactive questioning to understand email purpose
- 📋 **Template System**: Multiple built-in templates for different email types
- 🎨 **Personalization**: Adapts to your writing preferences over time
- 💬 **CLI Interface**: Rich command-line interface with interactive prompts

## Installation

### Prerequisites

1. **Python 3.8+** installed
2. **Ollama** installed and running locally
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Start Ollama server
   ollama serve
   
   # Download a model (recommended: llama2)
   ollama pull llama2
   ```

### Install Email Agent

```bash
# Clone the repository
git clone <repository-url>
cd email-agent

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Quick Start

1. **Start Ollama server** (if not already running):
   ```bash
   ollama serve
   ```

2. **Create a user profile** (optional but recommended):
   ```bash
   email-agent learn interactive --user your-email@example.com
   ```

3. **Learn from existing emails** (optional):
   ```bash
   email-agent learn from-emails --user your-email@example.com --email-dir ./my-emails/
   ```

4. **Generate your first email**:
   ```bash
   email-agent draft --user your-email@example.com
   ```

## Usage

### Drafting Emails

```bash
# Interactive mode with all prompts
email-agent draft --user your-email@example.com

# With specific parameters
email-agent draft \
  --user your-email@example.com \
  --topic "Follow up on meeting" \
  --recipient "john@example.com" \
  --context "We discussed the project timeline"

# Using a specific template
email-agent draft \
  --template sales_persuasive \
  --topic "Product demo request"
```

### Managing Writing Styles

```bash
# Learn from email files
email-agent learn from-emails \
  --user your-email@example.com \
  --email-file ./sample-email.txt

# Interactive style setup
email-agent learn interactive --user your-email@example.com

# Learn from directory of emails
email-agent learn from-emails \
  --user your-email@example.com \
  --email-dir ./emails/
```

### Managing Templates

```bash
# List available templates
email-agent template list

# Preview a template
email-agent template preview business_formal_standard --show-variables

# Create custom template
email-agent template create my_template business "My custom template"
```

### Managing Profiles

```bash
# List all user profiles
email-agent profile list

# Show profile details
email-agent profile show your-email@example.com

# Delete a profile
email-agent profile delete your-email@example.com
```

## Template Categories

### Business Formal
- `business_formal_standard` - Standard formal business communication
- `business_formal_inquiry` - Professional inquiry emails

### Casual Informal
- `casual_informal_friendly` - Friendly casual communication
- `casual_informal_check_in` - Casual follow-up messages

### Sales Outreach
- `sales_outreach_persuasive` - Persuasive sales emails
- `sales_outreach_follow_up` - Sales follow-up communications

## Configuration

The application uses YAML configuration files in the `config/` directory:

- `settings.yaml` - Main application settings
- `prompts.yaml` - AI prompt templates

Key configuration options:

```yaml
ollama:
  host: "http://localhost:11434"
  model: "llama2"
  timeout: 30

style:
  min_emails_for_analysis: 5
  learning_rate: 0.3
  confidence_threshold: 0.4

generation:
  temperature: 0.7
  max_tokens: 1000
```

## How It Works

1. **Intent Detection**: Analyzes your request and asks clarifying questions to understand the email's purpose
2. **Template Selection**: Chooses the most appropriate template based on intent and context
3. **Style Application**: Adapts the email to match your personal writing style
4. **AI Generation**: Uses local LLM to generate content that matches your style and intent
5. **Template Rendering**: Combines AI content with professional email templates

## Privacy & Security

- **Local Processing**: All AI processing happens locally on your machine
- **No Cloud Dependency**: Your email content never leaves your computer
- **Configurable Models**: Use any compatible local model through Ollama
- **Data Control**: All profiles and templates stored locally

## Advanced Usage

### Custom Templates

Create custom email templates with Jinja2 syntax:

```jinja2
{% if greeting %}{{ greeting }} {{ recipient_name }},{% endif %}

{{ opening }}

{% if context %}{{ context }}

{% endif %}{{ call_to_action }}

{{ signature }}
```

### Style Profile Customization

Your style profile tracks:
- Formality level (casual to formal)
- Sentence complexity
- Vocabulary sophistication
- Communication directness
- Common phrases and patterns

### Integration

The email agent can be integrated into other applications:

```python
from src.email_generator import EmailGenerator
from src.ai_engine import AIEngine
from src.template_manager import TemplateManager
from src.style_analyzer import StyleAnalyzer
from src.intent_detector import IntentDetector

# Initialize components
ai_engine = AIEngine()
template_manager = TemplateManager()
style_analyzer = StyleAnalyzer()
intent_detector = IntentDetector(ai_engine)

# Create email generator
generator = EmailGenerator(ai_engine, template_manager, style_analyzer, intent_detector)

# Generate email
result = generator.generate_email(
    topic="Project update",
    recipient="team@example.com",
    context="Weekly status update"
)
```

## Troubleshooting

### Common Issues

**Ollama Connection Error**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama if needed
ollama serve
```

**Model Not Found**
```bash
# List available models
ollama list

# Download a model
ollama pull llama2
```

**Low Style Confidence**
- The system needs at least 5 emails to build a reliable style profile
- Use the `learn interactive` command to set manual preferences

### Performance Tips

- Use a lighter model like `llama2:7b` for faster generation
- Limit the number of analyzed emails for better performance
- Use specific templates instead of auto-selection for faster results

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the configuration documentation

---

Made with ❤️ by the AI Email Agent team