import logging
from typing import Dict, List, Optional, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from LLMPlayer import LLMPlayer, UNOMove
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
    allow_origins=["*"],
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

# Removed analysis request/response models as /analysis API is not used by frontend

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
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for frontend connection testing"""
    return {"status": "healthy", "message": "LLM Backend is running"}


@app.get("/providers")
async def list_providers():
    """List supported LLM providers and their default models"""
    # Sanitize config to ensure JSON-serializable response (exclude non-serializable class objects)
    safe_providers = {}
    for key, cfg in PROVIDERS_CONFIG.items():
        safe_cfg = {
            k: v
            for k, v in cfg.items()
            if k != "class"  # exclude class references (not JSON serializable)
        }
        # Optionally include class name as string for UI display/debugging
        if "class" in cfg:
            try:
                safe_cfg["class_name"] = getattr(cfg["class"], "__name__", str(cfg["class"]))
            except Exception:
                safe_cfg["class_name"] = "unknown"
        safe_providers[key] = safe_cfg

    return {
        "providers": safe_providers,
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


if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
