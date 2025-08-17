import logging
from typing import Dict, List, Optional, Literal
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from LLMPlayer import LLMPlayer, UNOMove, GameAnalysis
from config import PROVIDERS_CONFIG
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="UNO LLM Backend with LangChain",
    description="Backend service for UNO game with LangChain-powered LLM bot players using structured output",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for API requests/responses
class GameState(BaseModel):
    currentPlayer: Dict
    tableStack: List[Dict]
    otherPlayers: List[Dict]
    direction: int
    sumDrawing: int
    lastPlayerDrew: bool
    gamePhase: str


class MoveRequest(BaseModel):
    gameState: GameState
    playerCards: List[Dict]
    provider: Literal[tuple(PROVIDERS_CONFIG.keys())]
    model: Optional[str] = None
    baseUrl: Optional[str] = None
    apiKey: Optional[str] = None


class MoveResponse(BaseModel):
    action: str
    card_id: Optional[str] = None
    color: Optional[str] = None
    reasoning: str
    isValid: bool
    validationMessage: Optional[str] = None
    provider: str
    model: str


class AnalysisRequest(BaseModel):
    gameState: GameState
    playerCards: List[Dict]
    provider: Literal[tuple(PROVIDERS_CONFIG.keys())]
    model: Optional[str] = None


class AnalysisResponse(BaseModel):
    analysis: GameAnalysis
    provider: str
    model: str


class GameSession(BaseModel):
    sessionId: str
    players: List[Dict]
    gameState: GameState


# Global storage for game sessions (use proper database in production)
game_sessions: Dict[str, GameSession] = {}

# Global storage for LLM players (cached for performance)
llm_player_cache: Dict[str, LLMPlayer] = {}


def get_llm_player(
    provider: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> LLMPlayer:
    """Get or create an LLM player with caching"""

    if not model:
        model = PROVIDERS_CONFIG.get(provider, {}).get("default_model")

    # Create cache key
    cache_key = f"{provider}:{model}:{base_url or 'default'}"

    if cache_key not in llm_player_cache:
        try:
            llm_player_cache[cache_key] = LLMPlayer(
                provider=provider, base_url=base_url, api_key=api_key, model=model
            )
        except Exception as e:
            logger.error(f"Failed to create LLM player for {provider}:{model}: {e}")
            raise HTTPException(
                status_code=400, detail=f"Failed to initialize LLM provider: {str(e)}"
            )

    return llm_player_cache[cache_key]


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "UNO LLM Backend API with LangChain",
        "version": "2.0.0",
        "features": [
            "Structured output using Pydantic models",
            "Multiple LLM provider support via LangChain",
            "Advanced game analysis",
            "Intelligent move prediction",
            "Move validation and retry logic",
        ],
        "endpoints": [
            "/docs - API documentation",
            "/health - Health check",
            "/providers - List supported providers",
            "/move - Get LLM move prediction",
            "/analysis - Get strategic game analysis",
            "/session - Game session management",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for frontend connection testing"""
    return {"status": "healthy", "message": "LLM Backend is running"}


@app.get("/providers")
async def list_providers():
    """List supported LLM providers and their default models"""
    return {
        "providers": PROVIDERS_CONFIG,
        "usage": "Specify provider and optionally model in your requests",
    }


@app.post("/move", response_model=MoveResponse)
async def get_llm_move(request: MoveRequest):
    """
    Get LLM move prediction for the current game state using structured output

    This endpoint uses LangChain with Pydantic models for structured output generation.
    """
    try:
        # Get the appropriate LLM player
        llm_player = get_llm_player(
            provider=request.provider,
            model=request.model,
            base_url=request.baseUrl,
            api_key=request.apiKey,
        )

        # Convert Pydantic models to dictionaries for LLMPlayer
        game_state_dict = request.gameState.model_dump()
        player_cards = request.playerCards

        # Get intelligent move from LLM with structured output
        predicted_move = llm_player.get_intelligent_move(game_state_dict, player_cards)

        # Validate the move
        is_valid, validation_message = llm_player.validate_move(
            UNOMove(**predicted_move), game_state_dict, player_cards
        )

        # Create response
        response = MoveResponse(
            action=predicted_move.get("action", "draw"),
            card_id=predicted_move.get("card_id"),
            color=predicted_move.get("color"),
            reasoning=predicted_move.get("reasoning", "No reasoning provided"),
            isValid=is_valid,
            validationMessage=validation_message if not is_valid else None,
            provider=request.provider,
            model=request.model or llm_player.model_name,
        )

        logger.info(f"LLM move generated: {response}")
        return response

    except Exception as e:
        logger.error(f"Error generating LLM move: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analysis", response_model=AnalysisResponse)
async def get_game_analysis(request: AnalysisRequest):
    """
    Get strategic game analysis using structured output

    This endpoint provides detailed strategic insights about the current game state.
    """
    try:
        # Get the appropriate LLM player
        llm_player = get_llm_player(provider=request.provider, model=request.model)

        # Convert Pydantic models to dictionaries
        game_state_dict = request.gameState.model_dump()
        player_cards = request.playerCards

        # Get game analysis using structured output
        analysis = llm_player.get_game_analysis(game_state_dict, player_cards)

        # Create response
        response = AnalysisResponse(
            analysis=analysis,
            provider=request.provider,
            model=request.model or llm_player.model_name,
        )

        logger.info(f"Game analysis generated: {response}")
        return response

    except Exception as e:
        logger.error(f"Error generating game analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/session")
async def create_game_session(session: GameSession):
    """Create a new game session"""
    try:
        game_sessions[session.sessionId] = session
        logger.info(f"Game session created: {session.sessionId}")
        return {
            "message": "Session created successfully",
            "sessionId": session.sessionId,
        }
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_game_session(session_id: str):
    """Get game session by ID"""
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return game_sessions[session_id]


@app.delete("/session/{session_id}")
async def delete_game_session(session_id: str):
    """Delete game session by ID"""
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del game_sessions[session_id]
    logger.info(f"Game session deleted: {session_id}")
    return {"message": "Session deleted successfully"}


@app.post("/session/{session_id}/move")
async def make_move_in_session(session_id: str, move_request: MoveRequest):
    """Make a move within a specific game session"""
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the move from LLM
    move_response = await get_llm_move(move_request)

    # Update the session's game state if move is valid
    if move_response.isValid:
        session = game_sessions[session_id]
        # You would integrate with your game logic here to update the session
        logger.info(f"Move executed in session {session_id}: {move_response}")

    return move_response


@app.post("/session/{session_id}/analysis")
async def get_session_analysis(session_id: str, analysis_request: AnalysisRequest):
    """Get game analysis for a specific session"""
    if session_id not in game_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get analysis from LLM
    analysis_response = await get_game_analysis(analysis_request)

    logger.info(f"Analysis generated for session {session_id}")
    return analysis_response


# Example integration with BotsServer
class BotsServerIntegration:
    """Helper class to integrate LangChain LLMPlayer with BotsServer"""

    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        self.provider = provider
        self.model = model
        self.llm_player = get_llm_player(provider, model)

    def get_bot_move(self, game_state: Dict, player_cards: List[Dict]) -> Dict:
        """
        Get a move for a bot player using the LLM with structured output

        This method can be called from BotsServer.ts to replace the simple bot logic
        """
        return self.llm_player.get_intelligent_move(game_state, player_cards)

    def validate_bot_move(
        self, move: Dict, game_state: Dict, player_cards: List[Dict]
    ) -> tuple[bool, str]:
        """Validate a bot move"""
        uno_move = UNOMove(**move)
        return self.llm_player.validate_move(uno_move, game_state, player_cards)

    def get_bot_analysis(
        self, game_state: Dict, player_cards: List[Dict]
    ) -> GameAnalysis:
        """Get strategic analysis for the bot"""
        return self.llm_player.get_game_analysis(game_state, player_cards)


# Advanced example endpoints
@app.post("/example/structured-output")
async def example_structured_output():
    """Example showing structured output capabilities"""
    try:
        # Example game state
        example_game_state = {
            "currentPlayer": {
                "id": "llm_bot",
                "name": "LangChain Bot",
                "cards": [
                    {"id": "card_1", "digit": 7, "color": "red"},
                    {"id": "card_2", "action": "skip", "color": "blue"},
                    {"id": "card_3", "action": "wild", "color": "black"},
                    {"id": "card_4", "digit": 3, "color": "green"},
                ],
            },
            "tableStack": [{"id": "top_card", "digit": 7, "color": "yellow"}],
            "otherPlayers": [
                {"name": "Human Player", "cards": 8},
                {"name": "Simple Bot", "cards": 3},
            ],
            "direction": 1,
            "sumDrawing": 0,
            "lastPlayerDrew": False,
            "gamePhase": "playing",
        }

        # Test multiple providers
        results = {}

        for provider in PROVIDERS_CONFIG.keys():
            try:
                llm_player = get_llm_player(provider)

                # Get structured move
                move = llm_player.predict_move(example_game_state)

                # Get structured analysis
                analysis = llm_player.get_game_analysis(
                    example_game_state, example_game_state["currentPlayer"]["cards"]
                )

                results[provider] = {
                    "move": move.model_dump(),
                    "analysis": analysis.model_dump(),
                    "model": llm_player.model_name,
                }

            except Exception as e:
                results[provider] = {"error": str(e)}

        return {
            "example": "Structured Output with LangChain",
            "gameState": example_game_state,
            "results": results,
            "notes": [
                "Each provider returns structured Pydantic models",
                "Move predictions include validation and reasoning",
                "Analysis provides strategic insights",
                "All responses conform to predefined schemas",
            ],
        }

    except Exception as e:
        logger.error(f"Error in structured output example: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/example/multi-provider")
async def example_multi_provider():
    """Example comparing multiple LLM providers"""
    try:
        example_game_state = {
            "currentPlayer": {
                "id": "test_bot",
                "name": "Test Bot",
                "cards": [
                    {"id": "card_1", "digit": 2, "color": "red"},
                    {"id": "card_2", "action": "reverse", "color": "green"},
                    {"id": "card_3", "action": "draw four", "color": "black"},
                ],
            },
            "tableStack": [{"id": "top", "digit": 5, "color": "blue"}],
            "otherPlayers": [{"name": "Opponent", "cards": 2}],
            "direction": 1,
            "sumDrawing": 0,
            "lastPlayerDrew": False,
        }

        provider_results = {}
        available_providers = list(PROVIDERS_CONFIG.keys())

        for provider in available_providers:
            try:
                llm_player = get_llm_player(provider)

                # Get move with timing
                import time

                start_time = time.time()

                move_dict = llm_player.get_intelligent_move(
                    example_game_state, example_game_state["currentPlayer"]["cards"]
                )

                end_time = time.time()

                provider_results[provider] = {
                    "move": move_dict,
                    "response_time": round(end_time - start_time, 2),
                    "model": llm_player.model_name,
                    "provider": provider,
                }

            except Exception as e:
                provider_results[provider] = {"error": str(e), "provider": provider}

        return {
            "comparison": "Multi-Provider LLM Comparison",
            "gameState": example_game_state,
            "results": provider_results,
            "summary": {
                "successful_providers": len(
                    [r for r in provider_results.values() if "error" not in r]
                ),
                "total_tested": len(provider_results),
            },
        }

    except Exception as e:
        logger.error(f"Error in multi-provider example: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/example/bots-server-integration")
async def example_bots_server_integration():
    """Example of how to integrate with BotsServer.ts using LangChain"""
    try:
        # Create integration instance
        integration = BotsServerIntegration("gemini", "gemini-2.5-pro")

        # Example game state (similar to what BotsServer would provide)
        game_state = {
            "currentPlayer": {
                "id": "langchain_bot",
                "name": "LangChain Bot",
                "cards": [
                    {"id": "card_1", "digit": 8, "color": "yellow"},
                    {"id": "card_2", "action": "skip", "color": "red"},
                    {"id": "card_3", "digit": 1, "color": "green"},
                ],
            },
            "tableStack": [{"id": "current_top", "digit": 8, "color": "red"}],
            "otherPlayers": [
                {"name": "Human Player", "cards": 5},
                {"name": "Simple Bot", "cards": 7},
            ],
            "direction": -1,  # Counter-clockwise
            "sumDrawing": 0,
            "lastPlayerDrew": False,
        }

        # Get bot move using structured output
        bot_move = integration.get_bot_move(
            game_state, game_state["currentPlayer"]["cards"]
        )

        # Validate move
        is_valid, validation_msg = integration.validate_bot_move(
            bot_move, game_state, game_state["currentPlayer"]["cards"]
        )

        # Get strategic analysis
        bot_analysis = integration.get_bot_analysis(
            game_state, game_state["currentPlayer"]["cards"]
        )

        return {
            "integration": "BotsServer.ts Integration with LangChain",
            "gameState": game_state,
            "botMove": bot_move,
            "validation": {"isValid": is_valid, "message": validation_msg},
            "strategicAnalysis": bot_analysis.model_dump(),
            "implementation": {
                "description": "Replace simple bot logic in BotsServer.ts with this integration",
                "benefits": [
                    "Structured output ensures consistent response format",
                    "Advanced strategic reasoning",
                    "Multiple LLM provider support",
                    "Automatic validation and retry logic",
                    "Detailed game analysis capabilities",
                ],
            },
        }

    except Exception as e:
        logger.error(f"Error in integration example: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task for cleanup
@app.post("/cleanup")
async def cleanup_old_sessions(background_tasks: BackgroundTasks):
    """Clean up old game sessions and cached LLM players"""
    background_tasks.add_task(cleanup_resources)
    return {"message": "Cleanup task started"}


async def cleanup_resources():
    """Background task to clean up resources"""
    try:
        logger.info("Starting resource cleanup...")

        # Clean up old sessions (implement proper timestamp-based cleanup)
        sessions_before = len(game_sessions)
        # game_sessions.clear()  # Simple cleanup - implement proper logic

        # Optionally clean up LLM player cache if memory usage is high
        # llm_player_cache.clear()

        logger.info(
            f"Resource cleanup completed. Sessions: {sessions_before} -> {len(game_sessions)}"
        )

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


@app.get("/cache/stats")
async def cache_statistics():
    """Get cache statistics"""
    return {
        "llm_player_cache": {
            "size": len(llm_player_cache),
            "keys": list(llm_player_cache.keys()),
        },
        "game_sessions": {
            "active_sessions": len(game_sessions),
            "session_ids": list(game_sessions.keys()),
        },
    }


@app.delete("/cache/clear")
async def clear_cache():
    """Clear all caches"""
    llm_player_cache.clear()
    game_sessions.clear()
    return {"message": "All caches cleared successfully"}


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
