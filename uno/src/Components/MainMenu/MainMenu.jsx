import React, { useEffect, useState } from "react";
import Grid from "@mui/material/Grid";
import Paper from "../Shared/Paper/Paper";
import Button from "../Shared/Button/Button";
import Typography from "../Shared/Typography/Typography";
import { Link, useNavigate } from "react-router-dom";
import API from "../../api/API";
import { useDispatch } from "../../utils/hooks";
import { setInLobby, setPlayerId } from "../../stores/features/gameSlice";
import {
  loadLLMConfig,
  saveLLMConfig,
  getDefaultConfig,
  getAvailableProviders,
  loadProvidersFromBackend,
} from "../../utils/llmConfig";
const style = {
  color: "#fff",
};

const MainMenu = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [mode, setMode] = useState('play');
  const [cfg, setCfg] = useState(getDefaultConfig().play);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Sync providers from backend then load config for current mode
    (async () => {
      await loadProvidersFromBackend();
      setCfg(loadLLMConfig(mode));
    })();
  }, [mode]);

  const onPlayOnline = () => {
    API.playOnline();
  };

  const onPlayOffline = async () => {
    API.playOnline();
    const playerId = await API.joinServer();
    dispatch(setPlayerId(playerId));
    dispatch(setInLobby(true));
    navigate("/waiting-lobby");
  };

  const onPlayArena = async () => {
    // Start Arena: all four players are LLMs
    const spectatorId = await API.startArena();
    dispatch(setPlayerId(spectatorId));
    dispatch(setInLobby(true));
    navigate("/waiting-lobby");
  };

  const toggleProvider = (provider) => {
    const meta = getAvailableProviders()[provider];
    setCfg((prev) => {
      const existing = prev.providers.find((p) => p.provider === provider);
      if (existing) {
        return {
          ...prev,
          providers: prev.providers.map((p) =>
            p.provider === provider ? { ...p, enabled: !p.enabled } : p
          ),
        };
      }
      // If provider not in config yet, add it with toggled state (user clicked to change from default true)
      return {
        ...prev,
        providers: [
          ...prev.providers,
          {
            provider,
            enabled: false,
            model: meta?.models?.[0] || "",
          },
        ],
      };
    });
  };

  const changeModel = (provider, model) => {
    setCfg((prev) => ({
      ...prev,
      providers: prev.providers.map((p) =>
        p.provider === provider ? { ...p, model } : p
      ),
    }));
  };

  const onSaveLLMConfig = () => {
    setSaving(true);
    try {
      // Ensure all providers exist in config
      const normalized = {
        providers: Object.keys(getAvailableProviders()).map((prov) => {
          const found = cfg.providers.find((p) => p.provider === prov);
          return (
            found || {
              provider: prov,
              enabled: true,
              model: getAvailableProviders()[prov].models[0],
            }
          );
        }),
      };
      saveLLMConfig(mode, normalized);
    } finally {
      setTimeout(() => setSaving(false), 300);
    }
  };

  return (
    <Paper key="main-menu">
      <Grid container alignItems="center" justifyContent="center" spacing={4}>
        <Grid item xs={10}>
          <Typography fontSize={22}>Start Playing</Typography>
        </Grid>
        <Grid
          item
          container
          alignItems="center"
          justifyContent="center"
          spacing={2}
          xs={12}
        >
          <Grid item xs={12} md={5} mt={3}>
            <Button style={{ width: "80%" }} onClick={onPlayOffline}>
              <img src="assets/icons/tv.svg" alt="" />
              <Typography>Play with LLM</Typography>
            </Button>
          </Grid>
          <Grid item xs={12} md={5} mt={3}>
            <Button style={{ width: "80%" }} onClick={onPlayArena}>
              <img src="assets/icons/tv.svg" alt="" />
              <Typography>Arena (All LLMs)</Typography>
            </Button>
          </Grid>
        </Grid>
        <Grid item xs={10} mt={6}>
          <Typography fontSize={20}>LLM Configuration</Typography>
        </Grid>
        <Grid item xs={10}>
          <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
            <Button onClick={() => setMode('play')} style={{ opacity: mode==='play'?1:0.7 }}>
              <Typography>Play Mode</Typography>
            </Button>
            <Button onClick={() => setMode('arena')} style={{ opacity: mode==='arena'?1:0.7 }}>
              <Typography>Arena Mode</Typography>
            </Button>
          </div>
          {Object.keys(getAvailableProviders()).map((prov) => {
            const meta = getAvailableProviders()[prov];
            const row = cfg.providers.find((p) => p.provider === prov) || {
              provider: prov,
              enabled: true,
              model: meta.models[0],
            };
            return (
              <div key={prov} style={{ display: "flex", alignItems: "center", margin: "8px 0" }}>
                <input
                  type="checkbox"
                  checked={!!row.enabled}
                  onChange={() => toggleProvider(prov)}
                  style={{ marginRight: 8 }}
                  id={`prov-${prov}`}
                />
                <label htmlFor={`prov-${prov}`} style={{ width: 140 }}>{meta.label}</label>
                <select
                  value={row.model}
                  onChange={(e) => changeModel(prov, e.target.value)}
                  style={{ marginLeft: 16 }}
                >
                  {meta.models.map((m) => (
                    <option value={m} key={m}>{m}</option>
                  ))}
                </select>
              </div>
            );
          })}
          <div style={{ marginTop: 12 }}>
            <Button onClick={onSaveLLMConfig} disabled={saving}>
              <Typography>{saving ? "Saving..." : "Save LLM Config"}</Typography>
            </Button>
          </div>
        </Grid>
        <Grid item container alignItems="center" justifyContent="center" mt={6}>
          <Grid item xs={6}>
            <Link style={style} to="/create-user">
              Profile Setting
            </Link>
          </Grid>
        </Grid>
        <Grid
          item
          container
          alignItems="center"
          justifyContent="center"
          xs={12}
        >
          <Grid item xs={6}>
            <a
              style={style}
              href="https://www.ultraboardgames.com/uno/game-rules.php"
              target="_blank"
              rel="noreferrer"
            >
              Game Rules
            </a>
          </Grid>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default MainMenu;
