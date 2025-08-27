/**
 * BotsServer Integration with LangChain LLM Backend
 *
 * This file contains the logic to integrate the TypeScript BotsServer
 * with the Python LangChain LLM backend for intelligent UNO bot players.
 */

import { EventsObject } from '../utils/EventsObject';

// Interfaces for API communication with LangChain backend
export interface LLMMoveRequest {
    gameState: {
        currentPlayer: {
            id: string;
            name: string;
            cards: Array<{
                id: string;
                digit?: number;
                color: string;
                action?: string;
            }>;
        };
        tableStack: Array<{
            id: string;
            digit?: number;
            color: string;
            action?: string;
        }>;
        otherPlayers: Array<{
            name: string;
            cards: number | Array<any>;
        }>;
        direction: number;
        sumDrawing: number;
        lastPlayerDrew: boolean;
        gamePhase: string;
    };
    playerCards: Array<{
        id: string;
        digit?: number;
        color: string;
        action?: string;
    }>;
    provider: string;
    model?: string;
    baseUrl?: string;
    apiKey?: string;
}

// Basic debug switch for logging (disable in production builds automatically if desired)
const DEBUG_LLM = process.env.NODE_ENV !== 'production' && false;

export interface LLMMoveResponse {
    action: "play" | "draw";
    card_id?: string;
    color?: "red" | "blue" | "green" | "yellow";
    reasoning: string;
    isValid: boolean;
    validationMessage?: string;
    provider: string;
    model: string;
}

/**
 * Enhanced BotsServer with LangChain LLM Integration
 *
 * This class extends the base BotsServer functionality to use
 * intelligent LLM-powered bot players instead of simple rule-based logic.
 */
export class LLMEnhancedBotsServer extends EventsObject {
    private llmBackendUrl: string;
    private llmTimeout: number;
    private llmUsage: boolean;
    private apiProvider: string;
    private model: string;
    private baseUrl?: string;
    private apiKey?: string;

    constructor() {
        super();
        
        // Default configuration
        // Allow overriding via env for deployments (CRA uses REACT_APP_*, Next uses NEXT_PUBLIC_*)
        this.llmBackendUrl =
            (process.env.REACT_APP_LLM_BACKEND_URL as string) ||
            (process.env.NEXT_PUBLIC_LLM_BACKEND_URL as string) ||
            "http://localhost:8000";
        this.llmTimeout = 15000; 
        this.llmUsage = true; 
        this.apiProvider = "";
        this.model = "";
    }

    /**
     * Enable or disable LLM usage for bot players
     */
    setLLMUsage(enabled: boolean): void {
        this.llmUsage = enabled;
        if (DEBUG_LLM) console.log(`LLM usage ${enabled ? 'enabled' : 'disabled'} for bot players`);
    }

    /**
     * Set the LLM backend URL
     */
    setLLMBackendUrl(url: string): void {
        this.llmBackendUrl = url;
        if (DEBUG_LLM) console.log(`LLM backend URL set to: ${url}`);
    }

    /**
     * Set the LLM timeout in milliseconds
     */
    setLLMTimeout(timeout: number): void {
        this.llmTimeout = timeout;
        if (DEBUG_LLM) console.log(`LLM timeout set to: ${timeout}ms`);
    }

    /**
     * Set the LLM provider and model
     */
    setLLMProvider(provider: string, model?: string, baseUrl?: string, apiKey?: string): void {
        this.apiProvider = provider;
        if (model) {
            this.model = model;
        }
        if (baseUrl) {
            this.baseUrl = baseUrl;
        }
        if (apiKey) {
            this.apiKey = apiKey;
        }
        if (DEBUG_LLM) console.log(`LLM provider set to: ${provider} with model: ${this.model || 'default'}`);
    }

    /**
     * Get an intelligent move from the LLM backend
     */
    async getLLMMove(
        gameState: LLMMoveRequest['gameState'],
        playerCards: LLMMoveRequest['playerCards']
    ): Promise<LLMMoveResponse> {
        if (!this.llmUsage) {
            if (DEBUG_LLM) console.log("LLM usage disabled, falling back to simple bot logic");
            return this.fallbackMoveBot(gameState, playerCards);
        }

        try {
            const request: LLMMoveRequest = {
                gameState: this.getGameStateForLLM(gameState),
                playerCards: playerCards,
                provider: this.apiProvider,
                model: this.model,
                baseUrl: this.baseUrl,
                apiKey: this.apiKey
            };

            if (DEBUG_LLM) console.log("Requesting LLM move from backend...");
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.llmTimeout);
            const response = await fetch(`${this.llmBackendUrl}/move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
                signal: controller.signal,
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                let detail = '';
                try {
                    const errJson = await response.json();
                    detail = errJson?.detail ? ` - ${JSON.stringify(errJson.detail)}` : '';
                } catch {}
                throw new Error(`HTTP ${response.status}: ${response.statusText}${detail}`);
            }

            const moveResponse: LLMMoveResponse = await response.json();
            
            if (DEBUG_LLM) console.log("LLM move received:", moveResponse);
            
            if (!moveResponse.isValid) {
                if (DEBUG_LLM) console.warn("LLM returned invalid move:", moveResponse.validationMessage);
                // Fall back to simple bot logic if LLM move is invalid
                return this.fallbackMoveBot(gameState, playerCards);
            }

            return moveResponse;

        } catch (error) {
            if (DEBUG_LLM) console.error("Error getting LLM move:", error);
            if (DEBUG_LLM) console.log("Falling back to simple bot logic");
            return this.fallbackMoveBot(gameState, playerCards);
        }
    }

    /**
     * Format game state for the LLM backend
     */
    private getGameStateForLLM(gameState: LLMMoveRequest['gameState']): LLMMoveRequest['gameState'] {
        return {
            currentPlayer: {
                id: gameState.currentPlayer?.id || "bot_player",
                name: gameState.currentPlayer?.name || "LLM Bot",
                cards: gameState.currentPlayer?.cards || []
            },
            tableStack: gameState.tableStack || [],
            otherPlayers: gameState.otherPlayers || [],
            direction: gameState.direction || 1,
            sumDrawing: gameState.sumDrawing || 0,
            lastPlayerDrew: gameState.lastPlayerDrew || false,
            gamePhase: gameState.gamePhase || "playing"
        };
    }

    /**
     * Fallback bot logic when LLM is unavailable or disabled
     */
    private fallbackMoveBot(
        gameState: LLMMoveRequest['gameState'],
        playerCards: LLMMoveRequest['playerCards']
    ): LLMMoveResponse {
        if (DEBUG_LLM) console.log("Using fallback bot logic");
        
        const topCard = gameState.tableStack?.[0];

        // Find playable cards
        const playableCards = playerCards.filter(card => 
            this.canPlayCard(topCard, card, gameState.lastPlayerDrew)
        );

        if (playableCards.length > 0) {
            // Prefer matching color, then action cards, else first
            const sameColor = topCard ? playableCards.find(c => c.color === topCard.color) : undefined;
            const actionCard = playableCards.find(c => !!c.action && c.action !== 'wild');
            const bestCard = sameColor || actionCard || playableCards[0];
            return {
                action: "play",
                card_id: bestCard.id,
                color: bestCard.color === "black" ? "red" : undefined,
                reasoning: `Playing ${bestCard.color} ${bestCard.action || bestCard.digit} as best available option`,
                isValid: true,
                provider: "fallback",
                model: "simple_bot"
            };
        }

        // No playable cards, must draw
        return {
            action: "draw",
            reasoning: "No playable cards available, must draw from deck",
            isValid: true,
            provider: "fallback",
            model: "simple_bot"
        };
    }

    /**
     * Check if a card can be played according to UNO rules
     */
    private canPlayCard(oldCard: any, newCard: any, lastPlayerDrew: boolean): boolean {
        const isOldDawingCard =
            oldCard?.action && oldCard.action.indexOf("draw") !== -1;
        const haveToDraw = isOldDawingCard && !lastPlayerDrew;
        const isNewDawingCard =
            newCard?.action && newCard.action.indexOf("draw") !== -1;

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
}
