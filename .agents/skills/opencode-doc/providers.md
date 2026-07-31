# Providers

OpenCode uses the [AI SDK](https://ai-sdk.dev/) and [Models.dev](https://models.dev/) to support **75+ LLM providers** and it supports running local models.

To add a provider you need to:

1. Add the API keys for the provider using the `/connect` command.
2. Configure the provider in your OpenCode config.

---

## Credentials

When you add a provider's API keys with the `/connect` command, they are stored in `~/.local/share/opencode/auth.json`.

---

## Config

You can customize the providers through the `provider` section in your OpenCode config.

### Base URL

You can customize the base URL for any provider by setting the `baseURL` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "anthropic": {
      "options": {
        "baseURL": "https://api.anthropic.com/v1"
      }
    }
  }
}
```

---

## OpenCode Zen

OpenCode Zen is a list of models provided by the OpenCode team that have been tested and verified to work well with OpenCode.

1. Run the `/connect` command in the TUI, select opencode, and head to [opencode.ai/auth](https://opencode.ai/auth).
2. Sign in, add your billing details, and copy your API key.
3. Paste your API key.
4. Run `/models` in the TUI to see the list of models we recommend.

---

## Directory

### Anthropic

We recommend signing up for [Claude Pro](https://www.anthropic.com/news/claude-pro) or [Max](https://www.anthropic.com/max).

1. Run the `/connect` command and select Anthropic.
2. Select the **Claude Pro/Max** option or **Create an API Key** or **Manually enter API Key**.
3. All Anthropic models should be available when you use the `/models` command.

### OpenAI

We recommend signing up for [ChatGPT Plus or Pro](https://chatgpt.com/pricing).

1. Run the `/connect` command and select OpenAI.
2. Select the **ChatGPT Plus/Pro** option.
3. All OpenAI models should be available when you use the `/models` command.

### Amazon Bedrock

1. Head over to the **Model catalog** in the Amazon Bedrock console and request access to the models you want.
2. Configure authentication using environment variables or configuration file.
3. Run the `/models` command to select the model you want.

### Azure OpenAI

1. Create an **Azure OpenAI** resource in the Azure portal.
2. Deploy a model in Azure AI Foundry.
3. Run the `/connect` command and search for **Azure**.
4. Set your resource name as an environment variable: `AZURE_RESOURCE_NAME=XXX`

### GitHub Copilot

1. Run the `/connect` command and search for GitHub Copilot.
2. Navigate to [github.com/login/device](https://github.com/login/device) and enter the code.
3. Run the `/models` command to select the model you want.

### Google Vertex AI

1. Head over to the **Model Garden** in the Google Cloud Console.
2. Set required environment variables: `GOOGLE_APPLICATION_CREDENTIALS` and `GOOGLE_CLOUD_PROJECT`.
3. Run the `/models` command to select the model you want.

### Groq

1. Head over to the [Groq console](https://console.groq.com/), click **Create API Key**.
2. Run the `/connect` command and search for Groq.
3. Enter the API key and run `/models`.

### OpenRouter

1. Head over to the [OpenRouter dashboard](https://openrouter.ai/settings/keys), click **Create API Key**.
2. Run the `/connect` command and search for OpenRouter.
3. Many OpenRouter models are preloaded by default.

### DeepSeek

1. Head over to the [DeepSeek console](https://platform.deepseek.com/), create an account, and click **Create new API key**.
2. Run the `/connect` command and search for **DeepSeek**.
3. Run the `/models` command to select a model like *DeepSeek Reasoner*.

### Local Models (Ollama, LM Studio, llama.cpp)

You can configure OpenCode to use local models:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama (local)",
      "options": {
        "baseURL": "http://localhost:11434/v1"
      },
      "models": {
        "llama2": {
          "name": "Llama 2"
        }
      }
    }
  }
}
```

---

## Custom provider

To add any **OpenAI-compatible** provider that's not listed in the `/connect` command:

1. Run the `/connect` command and scroll down to **Other**.
2. Enter a unique ID for the provider.
3. Enter your API key for the provider.
4. Create or update your `opencode.json` file:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "myprovider": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "My AI Provider Display Name",
      "options": {
        "baseURL": "https://api.myprovider.com/v1"
      },
      "models": {
        "my-model-name": {
          "name": "My Model Display Name"
        }
      }
    }
  }
}
```

---

## Troubleshooting

If you are having trouble with configuring a provider, check the following:

1. **Check the auth setup**: Run `opencode auth list` to see if the credentials for the provider are added to your config.
2. For custom providers, check the opencode config and:
   - Make sure the provider ID used in the `/connect` command matches the ID in your opencode config.
   - The right npm package is used for the provider.
   - Check correct API endpoint is used in the `options.baseURL` field.
