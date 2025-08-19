import { LLMEnhancedBotsServer, LLMMoveResponse } from "../LLMBot";

const gameState = {
  currentPlayer: { id: "bot", name: "LLM Bot", cards: [] },
  tableStack: [{ id: "top", digit: 5, color: "blue" }],
  otherPlayers: [{ name: "Opponent", cards: 3 }],
  direction: 1,
  sumDrawing: 0,
  lastPlayerDrew: false,
  gamePhase: "playing",
};

const playerCards = [
  { id: "card_1", digit: 5, color: "red" },
  { id: "card_2", action: "wild", color: "black" },
];

describe("LLMEnhancedBotsServer integration behavior", () => {
  let server: LLMEnhancedBotsServer;
  const originalFetch = global.fetch as any;

  beforeEach(() => {
    server = new LLMEnhancedBotsServer();
    // Ensure LLM usage is on and endpoint set
    server.setLLMUsage(true);
    server.setLLMBackendUrl("http://localhost:8000");
  });

  afterEach(() => {
    jest.resetAllMocks();
    (global as any).fetch = originalFetch;
  });

  it("returns backend move when valid", async () => {
    const responseBody: LLMMoveResponse = {
      action: "play",
      card_id: "card_1",
      color: "red",
      reasoning: "Test reasoning",
      isValid: true,
      provider: "gemini",
      model: "gemini-2.5-pro",
    };

    (global as any).fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => responseBody,
    });

    const res = await server.getLLMMove(gameState, playerCards);
    expect(res).toEqual(responseBody);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/move$/),
      expect.objectContaining({ method: "POST" })
    );
  });

  it("falls back when backend returns invalid move", async () => {
    (global as any).fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        action: "play",
        card_id: "unknown",
        reasoning: "Invalid",
        isValid: false,
        provider: "gemini",
        model: "gemini-2.5-pro",
      }),
    });

    const res = await server.getLLMMove(gameState, playerCards);
    expect(res.isValid).toBe(true);
    expect(res.provider).toBe("fallback");
  });

  it("falls back on network error", async () => {
    (global as any).fetch = jest.fn().mockRejectedValue(new Error("Network"));

    const res = await server.getLLMMove(gameState, playerCards);
    expect(res.isValid).toBe(true);
    expect(res.provider).toBe("fallback");
  });
});
