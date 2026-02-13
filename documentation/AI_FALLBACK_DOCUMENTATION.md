# Multi-AI Fallback System

## Overview

CyberVantage now supports multiple AI providers with automatic fallback functionality. The system can use **Azure OpenAI** and **Google Gemini** interchangeably, providing resilience and flexibility.

## Supported AI Providers

1. **Azure OpenAI** - Microsoft's Azure-hosted OpenAI models
2. **Google Gemini** - Google's Gemini AI models

## Configuration

### Environment Variables

Configure your AI providers in your `.env` file (see `.env.example` for a template):

```bash
# Primary AI Model - Choose which provider to try first
PRIMARY_AI_MODEL=azure   # Options: "azure" or "gemini"

# Azure OpenAI credentials
AZURE_OPENAI_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/...
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-nano

# Google Gemini credentials
GOOGLE_API_KEY=your-google-gemini-api-key
```

### Primary Model Selection

The `PRIMARY_AI_MODEL` environment variable determines which AI provider is used first:

- **`PRIMARY_AI_MODEL=azure`** (default)
  - Primary: Azure OpenAI
  - Fallback: Google Gemini

- **`PRIMARY_AI_MODEL=gemini`**
  - Primary: Google Gemini
  - Fallback: Azure OpenAI

## How Fallback Works

The system automatically handles failures and switches to the backup provider:

1. **Attempt Primary Provider**: The system first tries to use the configured primary AI provider
2. **Detect Failure**: If the primary provider fails (rate limit, API error, timeout, etc.), the system detects the failure
3. **Automatic Fallback**: The system automatically switches to the fallback provider
4. **Transparent Operation**: The application continues working seamlessly

### Example Scenarios

**Scenario 1: Azure Primary, Gemini Fallback**
```
User submits email for evaluation
→ Try Azure OpenAI first
→ Azure rate limit exceeded
→ Automatically fallback to Google Gemini
→ Evaluation completes successfully using Gemini
```

**Scenario 2: Gemini Primary, Azure Fallback**
```
User requests AI-generated phishing email
→ Try Google Gemini first
→ Gemini API returns error
→ Automatically fallback to Azure OpenAI
→ Email generated successfully using Azure
```

## Features Using AI

The multi-AI fallback system is used in:

1. **Email Generation** (Phase 2 of simulations)
   - Generates realistic phishing and legitimate training emails
   - Uses AI to create diverse scenarios based on user performance

2. **Explanation Evaluation** (Phase 2 feedback)
   - Evaluates user explanations about why emails are phishing/legitimate
   - Provides detailed, constructive feedback
   - Scores user understanding (0-10 scale)

## Benefits

### 1. **Reliability**
- If one AI provider is down or rate-limited, the system automatically uses another
- Reduces service interruptions and improves uptime

### 2. **Cost Optimization**
- Choose a cheaper provider as primary
- Use more expensive provider only when needed as fallback

### 3. **Flexibility**
- Easy to switch primary providers via environment variable
- No code changes required to change AI strategy

### 4. **Redundancy**
- No single point of failure
- Business continuity even if one provider has issues

## Implementation Details

### Architecture

The system uses a unified AI provider interface (`pyFunctions/ai_provider.py`) that:

1. Abstracts provider-specific implementations
2. Handles automatic retries with exponential backoff
3. Manages fallback logic transparently
4. Logs provider usage for monitoring

### Provider Integration

**Azure OpenAI Integration:**
- Uses `azure_openai_helper.py` for Azure-specific logic
- Supports chat completions with OpenAI SDK v1.x
- Handles Azure-specific authentication and endpoints

**Google Gemini Integration:**
- Uses `google-generativeai` SDK
- Supports Gemini Pro and other Gemini models
- Converts message formats for compatibility

## Monitoring and Logging

The system logs all AI operations:

```
[AI_PROVIDER] Attempting completion with primary provider: azure
[AI_PROVIDER] Success with primary provider: azure
```

or in case of fallback:

```
[AI_PROVIDER] Attempting completion with primary provider: gemini
[AI_PROVIDER] Primary provider gemini failed with status: RATE_LIMITED
[AI_PROVIDER] Attempting fallback to: azure
[AI_PROVIDER] Success with fallback provider: azure
```

## Troubleshooting

### Both Providers Failing

If both providers fail, the system falls back to:
- Template emails (for email generation)
- Rule-based evaluation (for explanation evaluation)

### Configuration Issues

Check that:
1. API keys are valid and not expired
2. Environment variables are properly set
3. Network connectivity to AI provider APIs
4. Rate limits not exceeded on both providers

### Testing Configuration

Test your AI configuration by:
1. Starting the application
2. Check startup logs for "✓ Azure OpenAI API key loaded" and "✓ Google Gemini API key loaded"
3. Run a simulation and check Phase 2 email generation
4. Review logs for successful provider usage

## Future Enhancements

Potential improvements for the multi-AI system:

- Add more AI providers (Claude, Mistral, etc.)
- Implement smart routing based on cost/performance
- Add provider health monitoring and automatic circuit breaking
- Support custom fallback order preferences
- Add telemetry for provider performance tracking

## Related Files

- `config/ai_config.py` - AI provider configuration
- `pyFunctions/ai_provider.py` - Unified AI interface with fallback
- `pyFunctions/azure_openai_helper.py` - Azure OpenAI implementation
- `pyFunctions/email_generation.py` - Uses multi-AI for email generation and evaluation
- `.env.example` - Environment variable template
