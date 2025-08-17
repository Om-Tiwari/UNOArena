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
        this.llmBackendUrl = "http://localhost:8000";
        this.llmTimeout = 15000; 
        this.llmUsage = true; // Enabled by default
        this.apiProvider = "gemini"; // Default provider
        this.model = ""; // Default model
    }

    /**
     * Enable or disable LLM usage for bot players
     */
    setLLMUsage(enabled: boolean): void {
        this.llmUsage = enabled;
        console.log(`LLM usage ${enabled ? 'enabled' : 'disabled'} for bot players`);
    }

    /**
     * Set the LLM backend URL
     */
    setLLMBackendUrl(url: string): void {
        this.llmBackendUrl = url;
        console.log(`LLM backend URL set to: ${url}`);
    }

    /**
     * Set the LLM timeout in milliseconds
     */
    setLLMTimeout(timeout: number): void {
        this.llmTimeout = timeout;
        console.log(`LLM timeout set to: ${timeout}ms`);
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
        console.log(`LLM provider set to: ${provider} with model: ${this.model || 'default'}`);
    }

    /**
     * Get an intelligent move from the LLM backend
     */
    async getLLMMove(gameState: any, playerCards: any[]): Promise<LLMMoveResponse> {
        if (!this.llmUsage) {
            console.log("LLM usage disabled, falling back to simple bot logic");
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

            console.log("Requesting LLM move from backend...");
            
            const response = await fetch(`${this.llmBackendUrl}/move`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request),
                // signal: AbortSignal.timeout(this.llmTimeout)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const moveResponse: LLMMoveResponse = await response.json();
            
            console.log("LLM move received:", moveResponse);
            
            if (!moveResponse.isValid) {
                console.warn("LLM returned invalid move:", moveResponse.validationMessage);
                // Fall back to simple bot logic if LLM move is invalid
                return this.fallbackMoveBot(gameState, playerCards);
            }

            return moveResponse;

        } catch (error) {
            console.error("Error getting LLM move:", error);
            console.log("Falling back to simple bot logic");
            return this.fallbackMoveBot(gameState, playerCards);
        }
    }

    /**
     * Format game state for the LLM backend
     */
    private getGameStateForLLM(gameState: any): LLMMoveRequest['gameState'] {
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
    private fallbackMoveBot(gameState: any, playerCards: any[]): LLMMoveResponse {
        console.log("Using fallback bot logic");
        
        const topCard = gameState.tableStack?.[0];

        // Find playable cards
        const playableCards = playerCards.filter(card => 
            this.canPlayCard(topCard, card, gameState.lastPlayerDrew)
        );

        if (playableCards.length > 0) {
            const bestCard = playableCards[0]; // Simplistic choice
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
