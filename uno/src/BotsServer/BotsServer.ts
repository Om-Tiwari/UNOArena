import { EventsObject } from "../utils/EventsObject";
import { shuffle, wrapMod } from "../utils/helpers";
import { Card, Player } from "../utils/interfaces";
import data from "./data.json";
import { LLMEnhancedBotsServer } from './LLMBot';
import { getEnabledProviders } from "../utils/llmConfig";

export interface IMoveEvent {
  curPlayer: number;
  nxtPlayer: number;
  card?: Card;
  draw?: number;
  cardsToDraw?: Card[];
}

export interface IStartEvent {
  cards: Card[];
  players: Player[];
  playerId: string;
}

export default class BotsServer extends EventsObject {
  players: Player[] = [];
  curPlayer = 0;
  direction = 1;
  tableStk: Card[] = [];
  drawingStk: Card[] = [];
  sumDrawing = 0;
  lastPlayerDrew = false;
  playersFinished: number[] = [];
  gameRunning = false;
  numberOfPlayers = 4;

  botTimeout = null;
  llmBot: LLMEnhancedBotsServer;

  constructor(numberOfPlayers = 4) {
    super();
    this.numberOfPlayers = numberOfPlayers;
    this.llmBot = new LLMEnhancedBotsServer();
    this.llmBot.setLLMUsage(true);
    this.llmBot.setLLMProvider('cerebras');
  }

  init() {
    this.players = [];
    this.curPlayer = 0;
    this.direction = 1;
    this.tableStk = [];
    this.drawingStk = [];
    this.sumDrawing = 0;
    this.playersFinished = [];
    this.lastPlayerDrew = false;
    this.gameRunning = false;
  }

  joinPlayer(player: Player) {
    const playerId = this.players.length.toString();

    this.players.push({
      ...player,
      id: playerId,
      cards: [],
    });

    return playerId;
  }

  addBots(mode: 'play' | 'arena' = 'play') {
    const numToAdd = this.numberOfPlayers - this.players.length;
    // Load experiment config
    let llmConfigs = getEnabledProviders(mode);
    if (!llmConfigs || llmConfigs.length === 0) {
      // Fallback to defaults if nothing enabled
      llmConfigs = [
        { provider: 'cerebras', model: 'qwen-3-235b-a22b-thinking-2507' },
        { provider: 'groq', model: 'openai/gpt-oss-120b' },
        { provider: 'gemini', model: 'gemini-2.5-pro' },
        { provider: 'sambanova', model: 'DeepSeek-R1-0528' },
      ];
    }
    for (let i = 0; i < numToAdd; i++) {
      const bot = data.players[i];
      const playerId = this.players.length.toString();
      const cfg = llmConfigs[i % llmConfigs.length];
      this.players.push({
        ...bot,
        id: playerId,
        cards: [],
        isBot: true,
        llmProvider: cfg.provider,
        llmModel: cfg.model,
      });
    }
    this.fireEvent("players-changed", this.players);
    if (this.players.length === this.numberOfPlayers)
      setTimeout(() => {
        this.start();
      }, 1000);
  }

  start() {
    const cards = [...data.cards] as Card[];
    shuffle(cards);
    shuffle(this.players);
    const NUM_CARDS = 7;
    this.players.forEach((player, idx) => {
      player.cards = cards.slice(idx * NUM_CARDS, (idx + 1) * NUM_CARDS);
    });
    this.drawingStk = cards.slice(this.players.length * NUM_CARDS, cards.length);

    // Flip the first table card (prefer a non-black card)
    let idx = 0;
    while (idx < this.drawingStk.length && this.drawingStk[idx].color === "black") idx++;
    const firstTableCard = this.drawingStk.splice(idx, 1)[0] || this.drawingStk.shift();
    if (firstTableCard) this.tableStk.unshift(firstTableCard as Card);

    // In Arena mode (all bots), pick the first player's cards so UI has a hand to render
    const humanOrFirst = this.players.find((p) => !p.isBot) || this.players[0];
    this.fireEvent("game-init", {
      cards: humanOrFirst?.cards || [],
      players: this.players.map((p) => ({ ...p, cards: [] })),
    });
    // Auto-start turns; if current player is a bot, it will move
    this.ready();
  }

  ready() {
    if (this.players[this.curPlayer].isBot) this.moveBot();
  }

  move(draw: boolean | null, cardId: string | null) {
    let moveEventObj: IMoveEvent = { nxtPlayer: 0, curPlayer: 0 };
    let card: Card | undefined;

    if (cardId) card = getCardById(cardId) as Card;

    if (card && !canPlayCard(this.tableStk[0], card, this.lastPlayerDrew))
      return false;

    if (draw) {
      let drawCnt = 1;
      if (this.sumDrawing) {
        drawCnt = this.sumDrawing;
        this.sumDrawing = 0;
      }

      moveEventObj.draw = drawCnt;
      if (drawCnt + 1 > this.drawingStk.length) {
        this.drawingStk = shuffle(this.tableStk.slice(5, this.tableStk.length));
        this.tableStk = this.tableStk.slice(0, 5);
      }

      moveEventObj.cardsToDraw = this.drawingStk.slice(0, drawCnt);
      this.players[this.curPlayer].cards = this.drawingStk
        .slice(0, drawCnt)
        .concat(this.players[this.curPlayer].cards);

      this.drawingStk = this.drawingStk.slice(drawCnt, this.drawingStk.length);
      this.lastPlayerDrew = true;
    }

    let nxtPlayer = this.getNextPlayer(card);

    moveEventObj.curPlayer = this.curPlayer;
    moveEventObj.nxtPlayer = nxtPlayer;

    if (card) {
      if (card.action === "draw two") this.sumDrawing += 2;
      if (card.action === "draw four") this.sumDrawing += 4;

      this.tableStk.unshift(card);
      moveEventObj.card = card;
      this.players[this.curPlayer].cards = this.players[
        this.curPlayer
      ].cards.filter((c) => c.id !== card?.id);
      this.lastPlayerDrew = false;

      // Check if game finished
      if (this.players[this.curPlayer].cards.length === 0)
        this.playersFinished.push(this.curPlayer);
      if (this.playersFinished.length === this.players.length - 1) {
        this.playersFinished.push(nxtPlayer);
        this.finishGame();
        this.fireEvent("move", moveEventObj as IMoveEvent);
        return;
      }
    }

    this.curPlayer = nxtPlayer;

    this.fireEvent("move", moveEventObj as IMoveEvent);

    if (this.players[this.curPlayer].isBot) this.moveBot();
  }

  getNextPlayer(card?: Card) {
    let nxtPlayer = this.curPlayer;

    if (card?.action === "reverse") this.direction *= -1;

    const moveForward = (steps: number = 1) => {
      while (steps--) {
        nxtPlayer = wrapMod(
          nxtPlayer + 1 * this.direction,
          this.players.length
        );
        while (this.players[nxtPlayer].cards.length === 0)
          nxtPlayer = wrapMod(
            nxtPlayer + 1 * this.direction,
            this.players.length
          );
      }
    };

    //Move to next player ( if not wild card )
    if (card?.action === "skip") {
      moveForward(2);
    } else if (card?.action !== "wild") moveForward();

    return nxtPlayer;
  }

  async moveBot() {
    const currentPlayer = this.players[this.curPlayer];
    const gameState = {
        currentPlayer: {
            id: currentPlayer.id,
            name: currentPlayer.name,
            cards: currentPlayer.cards,
        },
        tableStack: this.tableStk,
        otherPlayers: this.players.filter(p => p.id !== currentPlayer.id).map(p => ({ name: p.name, cards: p.cards.length })),
        direction: this.direction,
        sumDrawing: this.sumDrawing,
        lastPlayerDrew: this.lastPlayerDrew,
        gamePhase: "playing",
    };

    try {
        // Apply per-bot LLM settings before requesting a move
        if (currentPlayer.llmProvider || currentPlayer.llmModel || currentPlayer.llmBaseUrl || currentPlayer.llmApiKey) {
            this.llmBot.setLLMProvider(
              currentPlayer.llmProvider || 'cerebras',
              currentPlayer.llmModel,
              currentPlayer.llmBaseUrl,
              currentPlayer.llmApiKey,
            );
        }
        const llmMove = await this.llmBot.getLLMMove(gameState, currentPlayer.cards);
        if (llmMove.action === 'play' && llmMove.card_id) {
            this.move(false, llmMove.card_id);
        } else {
            this.move(true, null);
        }
    } catch (error) {
        console.error("Error in moveBot:", error);
        // Fallback to original simple bot logic on error
        for (let i = 0; i < this.players[this.curPlayer].cards.length; i++) {
            const card = this.players[this.curPlayer].cards[i];
            if (canPlayCard(this.tableStk[0], card, this.lastPlayerDrew))
                return this.move(false, card.id as string);
        }
        return this.move(true, null);
    }
}

  finishGame() {
    const playersFinishingOrder = this.playersFinished.map(
      (idx) => this.players[idx]
    );

    this.init();
    this.fireEvent("finish-game", playersFinishingOrder);
  }
}

export function canPlayCard(
  oldCard: Card,
  newCard: Card,
  lastPlayerDrew: boolean
) {
  const isOldDawingCard =
    oldCard?.action && oldCard.action.indexOf("draw") !== -1;
  const haveToDraw = isOldDawingCard && !lastPlayerDrew;
  const isNewDawingCard =
    newCard?.action && newCard.action.indexOf("draw") !== -1;

  //No Card Played Yet
  if (!oldCard) return true;

  if (!haveToDraw && newCard.action === "wild") return true;

  if (newCard.action === "draw four") return true;

  if (oldCard.color === "black" && !haveToDraw) return true;

  if (haveToDraw && isNewDawingCard) return true;

  if (!haveToDraw && oldCard.color === newCard.color) return true;

  if (oldCard.digit !== undefined && oldCard.digit === newCard.digit)
    return true;

  return false;
}

const getCardById = (id: string) => data.cards.find((c) => c.id === id);
