export type LLMExperimentConfig = {
  providers: Array<{
    provider: string;
    enabled: boolean;
    model: string;
  }>;
};

const STORAGE_KEY = "llmExperimentConfig";

// Mirror of backend providers for UI; keep in sync with uno_backend/config.py
export const AVAILABLE_PROVIDERS: Record<string, { label: string; models: string[] }> = {
  gemini: {
    label: "Gemini",
    models: ["gemini-2.5-pro", "gemma-3-12b-it", "gemini-2.5-flash"],
  },
  groq: {
    label: "Groq",
    models: ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "moonshotai/kimi-k2-instruct"],
  },
  cerebras: {
    label: "Cerebras",
    models: [
      "qwen-3-235b-a22b-thinking-2507",
      "gpt-oss-120b",
      "qwen-3-32b",
      "llama-4-maverick-17b-128e-instruct",
    ],
  },
  sambanova: {
    label: "SambaNova",
    models: [
      "DeepSeek-R1-0528",
      "Meta-Llama-3.3-70B-Instruct",
      "Llama-4-Maverick-17B-128E-Instruct",
    ],
  },
};

export function getDefaultConfig(): LLMExperimentConfig {
  return {
    providers: Object.keys(AVAILABLE_PROVIDERS).map((p) => ({
      provider: p,
      enabled: true,
      model: AVAILABLE_PROVIDERS[p].models[0],
    })),
  };
}

export function loadLLMConfig(): LLMExperimentConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return getDefaultConfig();
    const parsed = JSON.parse(raw);
    // Basic validation
    if (!parsed || !Array.isArray(parsed.providers)) return getDefaultConfig();
    return parsed as LLMExperimentConfig;
  } catch {
    return getDefaultConfig();
  }
}

export function saveLLMConfig(cfg: LLMExperimentConfig) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg));
}

export function getEnabledProviders(): Array<{ provider: string; model: string }> {
  const cfg = loadLLMConfig();
  return cfg.providers.filter((p) => p.enabled).map(({ provider, model }) => ({ provider, model }));
}
