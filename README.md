# AI Email Agent

An intelligent email assistant that generates personalized emails using local AI, matching your writing style.

## Features

- 🤖 Local AI (Ollama) - runs on your machine, no cloud
- 📝 Learns your writing style
- 🎯 Understands email intent
- 📋 Multiple templates
- 💬 Simple CLI interface

## Setup

### Requirements

1. Python 3.8+
2. Ollama installed and running
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama serve
   ollama pull llama2
   ```

### Install

```bash
git clone <repository-url>
cd email-agent
pip install -r requirements.txt
pip install -e .
```

## Quick Start

```bash
# Start Ollama (if not running)
ollama serve

# Generate an email
email-agent draft --user your-email@example.com

# Learn from your emails
email-agent learn from-emails --user your-email@example.com --email-dir ./emails/
```

## Common Commands

```bash
# Draft an email with specific details
email-agent draft --user you@example.com --topic "Follow up" --recipient "john@example.com"

# Learn your writing style
email-agent learn interactive --user you@example.com

# List templates
email-agent template list

# View your profile
email-agent profile show you@example.com
```

## Templates

- Business formal/inquiry
- Casual/friendly
- Sales outreach/follow-up

## Privacy

All processing happens locally on your machine. Your emails never leave your computer.

## Troubleshooting

**Ollama not connecting?**
```bash
curl http://localhost:11434/api/tags
```

**Model missing?**
```bash
ollama pull llama2
```

Made with Love 
Arnav Eluri 
