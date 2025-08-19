import { OfflineServer } from "../Server/OfflineServer";
import { ServerInterface } from "../Server/ServerInterface";
import { Player, GameServer, Card } from "../utils/interfaces";

export class _API implements ServerInterface {
  _server: ServerInterface;
  player?: Player;

  constructor() {
    this._server = new OfflineServer();
  }

  playOnline() {
    this._server = new OfflineServer();
  }

  /**
   * Start Arena mode: all 4 players are LLMs (no human-controlled player).
   * Returns a synthetic playerId representing the spectator/bot slot so the UI can proceed.
   */
  startArena(): Promise<string> {
    // OfflineServer knows how to initialize Arena mode
    return (this._server as OfflineServer).startArena();
  }

  getServers(): Promise<GameServer[]> {
    console.log(this._server);

    return this._server.getServers();
  }

  getServerPlayers(): Promise<Player[]> {
    return this._server.getServerPlayers();
  }

  createServer(serverName: string, serverPassword?: string): Promise<string> {
    return this._server.createServer(serverName, serverPassword);
  }

  joinServer(serverId: string, serverPassword?: string): Promise<string> {
    return this._server.joinServer(serverId, serverPassword);
  }

  emitReady(): void {
    this._server.emitReady();
  }

  leaveServer(): void {
    this._server.leaveServer();
  }

  move(draw: boolean | null, cardId: string): Promise<void> {
    return this._server.move(draw, cardId);
  }

  onPlayersUpdated(cb: (players: Player[]) => void): () => void {
    return this._server.onPlayersUpdated(cb);
  }

  onGameInit(
    cb: (data: { players: Player[]; cards: Card[] }) => void
  ): () => void {
    const unsub = this._server.onGameInit(cb);
    console.log(this._server);
    return unsub;
  }

  onMove(
    cb: (data: {
      nxtPlayer: number;
      card: Card;
      draw?: number | undefined;
      cardsToDraw?: Card[] | undefined;
    }) => void
  ): () => void {
    return this._server.onMove(cb);
  }

  onPlayerLeft(cb: () => void): () => void {
    return this._server.onPlayerLeft(cb);
  }

  onFinishGame(cb: (playersOrdered: Player[]) => void): () => void {
    return this._server.onFinishGame(cb);
  }

  getPlayer(): Player {
    return this._server.getPlayer();
  }
  
}

const API = new _API();

export default API;
