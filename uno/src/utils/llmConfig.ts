export type LLMProviderEntry = { provider: string; enabled: boolean; model: string };
export type LLMExperimentConfig = { providers: LLMProviderEntry[] };
export type LLMExperimentConfigPerMode = { arena: LLMExperimentConfig; play: LLMExperimentConfig };
export type LLMMode = 'arena' | 'play';

const STORAGE_KEY = "llmExperimentConfig.v2";

// Providers come exclusively from the backend
let availableProviders: Record<string, { label: string; models: string[] }> = {};

export function getAvailableProviders() {
  return availableProviders;
}

export async function loadProvidersFromBackend(baseUrl?: string): Promise<Record<string, { label: string; models: string[] }>> {
  try {
    const resolvedBase =
      baseUrl ||
      (process.env.REACT_APP_LLM_BACKEND_URL as string) ||
      (process.env.NEXT_PUBLIC_LLM_BACKEND_URL as string) ||
      "http://localhost:8000";
    const res = await fetch(`${resolvedBase}/providers`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    // json.providers = { provider: { default_model, supported_models, ... } }
    const provs = json.providers || {};
    const mapped: Record<string, { label: string; models: string[] }> = {};
    Object.keys(provs).forEach((k) => {
      const entry = provs[k];
      const models: string[] = entry.supported_models || (entry.models || []);
      mapped[k] = { label: (entry.label || k).replace(/_/g, ' ').replace(/\b\w/g, (m: string) => m.toUpperCase()), models };
    });
    if (Object.keys(mapped).length > 0) {
      availableProviders = mapped;
    }
  } catch (e) {
    // ignore, keep current (possibly empty) list
  }
  return availableProviders;
}

export function getDefaultConfig(): LLMExperimentConfigPerMode {
  const provs = getAvailableProviders();
  const base = {
    providers: Object.keys(provs).map((p) => ({ provider: p, enabled: true, model: provs[p].models[0] })),
  };
  return { arena: base, play: base };
}

function migrateIfNeeded(raw: any): LLMExperimentConfigPerMode {
  const defaults = getDefaultConfig();
  if (!raw) return defaults;
  // v1 schema: { providers: [...] }
  if (raw.providers && Array.isArray(raw.providers)) {
    return { arena: raw as LLMExperimentConfig, play: raw as LLMExperimentConfig };
  }
  // v2 schema
  if (raw.arena && raw.play) return raw as LLMExperimentConfigPerMode;
  return defaults;
}

export function loadLLMConfig(mode: LLMMode = 'play'): LLMExperimentConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = migrateIfNeeded(raw ? JSON.parse(raw) : null);
    return (parsed?.[mode] as LLMExperimentConfig) || getDefaultConfig()[mode];
  } catch {
    return getDefaultConfig()[mode];
  }
}

export function saveLLMConfig(mode: LLMMode, cfg: LLMExperimentConfig) {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = migrateIfNeeded(raw ? JSON.parse(raw) : null);
    const next: LLMExperimentConfigPerMode = { ...parsed, [mode]: cfg } as LLMExperimentConfigPerMode;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    const init = getDefaultConfig();
    init[mode] = cfg;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(init));
  }
}

export function getEnabledProviders(mode: LLMMode = 'play'): Array<{ provider: string; model: string }> {
  const cfg = loadLLMConfig(mode);
  return cfg.providers.filter((p) => p.enabled).map(({ provider, model }) => ({ provider, model }));
}
