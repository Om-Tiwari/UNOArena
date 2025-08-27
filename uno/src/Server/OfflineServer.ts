import type { GameServer, Player, Card } from "../utils/interfaces";
import { ServerInterface } from "./ServerInterface";
import BotsServer from "../BotsServer/BotsServer";

export class OfflineServer implements ServerInterface {
  player?: Player;

  _botsServer: BotsServer;

  /**
   *
   */
  constructor() {
    this._botsServer = new BotsServer();
  }

  async getServers(): Promise<GameServer[]> {
    return [];
  }

  async getServerPlayers(): Promise<Player[]> {
    return this._botsServer.players.map((p) => ({ ...p, cards: [] }));
  }

  async createServer(
    serverName: string,
    serverPassword?: string
  ): Promise<string> {
    // Offline mode: no actual server is created. Return a synthetic id.
    const syntheticId = "offline_server";
    return Promise.resolve(syntheticId);
  }

  async joinServer(serverId: string, serverPassword?: string): Promise<string> {
    this._botsServer = new BotsServer();
    this._botsServer.init();
    const playerId = this._botsServer.joinPlayer(this.getPlayer());
    setTimeout(() => this._botsServer.addBots('play'), 2000);
    return playerId;
  }

  /**
   * Arena mode: start a game with 4 LLM bots and no human player.
   * Returns a synthetic playerId used only for UI state.
   */
  async startArena(): Promise<string> {
    this._botsServer = new BotsServer();
    this._botsServer.init();
    // Directly add bots (no human join)
    setTimeout(() => {
      this._botsServer.addBots('arena');
      // After bots are added, BotsServer will call start() ~1s later.
      // Schedule ready() to kick off bot turns automatically.
      setTimeout(() => this._botsServer.ready(), 1500);
    }, 500);
    // Synthetic spectator id that won't match any player; UI will still render game state
    return Promise.resolve("arena_spectator");
  }

  emitReady(): void {
    this._botsServer.ready();
  }

  leaveServer(): void {
    // Safely remove all listeners; keep instance to avoid null deref in unsubscribe closures
    if (this._botsServer) {
      try {
        this._botsServer.removeAllListeners();
      } catch (_) {
        // ignore
      }
    }
  }
  async move(draw: boolean | null, cardId: string): Promise<void> {
    this._botsServer.move(draw, cardId);
  }

  onPlayersUpdated(cb: (players: Player[]) => void): () => void {
    this._botsServer?.addEventListener("players-changed", cb);
    return () => this._botsServer?.removeEventListener("players-changed", cb);
  }

  onGameInit(
    cb: (data: { players: Player[]; cards: Card[] }) => void
  ): () => void {
    this._botsServer?.addEventListener("game-init", cb);
    return () => this._botsServer?.removeEventListener("game-init", cb);
  }

  onMove(
    cb: (data: {
      nxtPlayer: number;
      card: Card;
      draw?: number | undefined;
      cardsToDraw?: Card[] | undefined;
    }) => void
  ): () => void {
    this._botsServer?.addEventListener("move", cb);
    return () => this._botsServer?.removeEventListener("move", cb);
  }

  onPlayerLeft(cb: () => void): () => void {
    this._botsServer?.addEventListener("player-left", cb);
    return () => this._botsServer?.removeEventListener("player-left", cb);
  }

  onFinishGame(cb: (playersOrdered: Player[]) => void): () => void {
    this._botsServer?.addEventListener("finish-game", cb);
    return () => this._botsServer?.removeEventListener("finish-game", cb);
  }

  removeAllListeners() {
    this._botsServer?.removeAllListeners();
  }

  getPlayer(): Player {
    if (this.player) return this.player;
    this.player = {} as Player;
    this.player.name = localStorage.getItem("playerName") as string;
    this.player.img = localStorage.getItem("playerImg") as string;
    return this.player;
  }
}
