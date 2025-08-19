import logging
from typing import Dict, List, Optional, Tuple, Literal, Union
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_sambanova import ChatSambaNovaCloud
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_cerebras import ChatCerebras
from langchain_core.messages import SystemMessage, HumanMessage
import os
from dotenv import load_dotenv

from config import PROVIDERS_CONFIG

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for structured output
class UNOMove(BaseModel):
    """Structured response for UNO game moves"""

    action: Literal["play", "draw"] = Field(
        description="The action to take: play a card or draw from deck"
    )
    card_id: Optional[Union[str, int]] = Field(
        None, description="ID of the card to play (required if action is 'play')"
    )
    color: Optional[Literal["red", "blue", "green", "yellow"]] = Field(
        None, description="Color to choose when playing wild/draw four cards"
    )
    reasoning: str = Field(description="Brief explanation of the decision strategy")


class GameAnalysis(BaseModel):
    """Optional extended analysis of the game state"""

    best_cards_to_keep: List[str] = Field(
        description="IDs of cards that should be kept for strategic reasons"
    )
    opponent_threat_level: int = Field(
        description="Threat level of opponents (1-10)", ge=1, le=10
    )
    strategic_notes: str = Field(description="Additional strategic considerations")


class LLMPlayer:
    def __init__(
        self,
        provider: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize LLMPlayer with LangChain and structured output

        Args:
            provider: LLM provider ("openai", "groq", "anthropic", etc.)
            base_url: Custom API base URL (optional)
            api_key: API key (will use environment variables if not provided)
            model: Model name to use for predictions
        """
        self.name = "LangChain LLM Player"
        self.provider = provider
        self.model_name = model or PROVIDERS_CONFIG.get(provider, {}).get(
            "default_model"
        )
        if not self.model_name:
            raise ValueError(f"No model specified and no default model for provider {provider}")
        self.max_retries = 3

        # Initialize LangChain model based on provider
        self.llm = self._initialize_llm(provider, api_key, self.model_name)

        # Create structured output model
        self.structured_llm = self.llm.with_structured_output(UNOMove)

    def _initialize_llm(self, provider: str, api_key: Optional[str], model: str):
        """Initialize the appropriate LangChain model based on the centralized config."""
        
        provider_config = PROVIDERS_CONFIG.get(provider)
        if not provider_config:
            raise ValueError(f"Unsupported provider: {provider}")

        llm_class = provider_config.get("class")
        if not llm_class:
            raise ValueError(f"No LangChain class mapped for provider: {provider}")

        # Get API key from argument or environment variable specified in config
        api_key_env_var = provider_config.get("api_key_env")
        final_api_key = api_key or (api_key_env_var and os.getenv(api_key_env_var))

        if not final_api_key:
            raise ValueError(f"{provider_config.get('name', provider)} API key is required")

        # Prepare arguments for the LLM class
        kwargs = {
            "model": model,
            "api_key": final_api_key,
            "temperature": 0.1, # A common default
        }

        # Add provider-specific arguments from config
        if provider_config.get("extra_args"):
            kwargs.update(provider_config["extra_args"])

        try:
            return llm_class(**kwargs)
        except Exception as e:
            logger.error(f"Error initializing LLM for provider {provider}: {e}")
            raise

    def get_game_context(self, game_state: Dict) -> str:
        """
        Convert game state to a context string for the LLM

        Args:
            game_state: Current game state from BotsServer

        Returns:
            Formatted context string for the LLM
        """
        try:
            # Extract relevant game information
            current_player = game_state.get("currentPlayer", {})
            player_cards = current_player.get("cards", [])
            table_stack = game_state.get("tableStack", [])
            top_card = table_stack[0] if table_stack else None
            other_players = game_state.get("otherPlayers", [])
            direction = game_state.get("direction", 1)
            sum_drawing = game_state.get("sumDrawing", 0)
            last_player_drew = game_state.get("lastPlayerDrew", False)

            # Format player cards
            cards_str = self._format_cards(player_cards)

            # Format top card
            top_card_str = (
                self._format_card(top_card) if top_card else "No card played yet"
            )

            # Format other players info
            other_players_str = self._format_other_players(other_players)

            # Add previous validation errors for learning
            validation_context = ""
            if game_state.get("lastValidationError"):
                validation_context = (
                    f"\nPREVIOUS ERROR: {game_state['lastValidationError']}"
                )
                if game_state.get("lastInvalidMove"):
                    validation_context += (
                        f"\nInvalid move was: {game_state['lastInvalidMove']}"
                    )

            context = f"""
CURRENT GAME STATE:
- Your cards: {cards_str}
- Top card on table: {top_card_str}
- Game direction: {"clockwise" if direction == 1 else "counter-clockwise"}
- Cards to draw if you must draw: {sum_drawing}
- Last player drew: {last_player_drew}
- Other players: {other_players_str}

UNO RULES:
- Match color, number, or action with the top card
- Special cards: reverse (changes direction), skip (skips next player), draw two (+2), draw four (+4), wild (change color)
- Black cards (wild, draw four) can be played anytime
- If pending draws exist and you didn't draw, play a matching draw card or draw the pending amount
- Goal: Get rid of all cards first

STRATEGY PRIORITIES:
1. Play high-value cards early (draw four, wild, action cards)
2. Save wild cards for strategic moments
3. Consider opponents' card counts
4. Block opponents when they have few cards
5. Manage your hand size efficiently
{validation_context}
"""
            return context

        except Exception as e:
            logger.error(f"Error formatting game context: {e}")
            return "Error formatting game context"

    def _format_cards(self, cards: List[Dict]) -> str:
        """Format player cards for display"""
        if not cards:
            return "No cards"

        formatted = []
        for i, card in enumerate(cards):
            card_str = self._format_card(card)
            formatted.append(f"{card.get('id', f'card_{i}')}: {card_str}")
        return ", ".join(formatted)

    def _format_card(self, card: Dict) -> str:
        """Format a single card for display"""
        if not card:
            return "Unknown card"

        parts = []
        if card.get("color"):
            parts.append(card["color"])
        if card.get("digit") is not None:
            parts.append(str(card["digit"]))
        if card.get("action"):
            parts.append(card["action"])

        return " ".join(parts) if parts else "Unknown card"

    def _format_other_players(self, players: List[Dict]) -> str:
        """Format other players information"""
        if not players:
            return "No other players"

        formatted = []
        for player in players:
            name = player.get("name", "Unknown")
            cards = player.get("cards", [])

            # Handle both cases: cards as list or cards as integer count
            if isinstance(cards, list):
                card_count = len(cards)
            elif isinstance(cards, int):
                card_count = cards
            else:
                card_count = 0

            formatted.append(f"{name} ({card_count} cards)")

        return "; ".join(formatted)

    def create_system_prompt(self) -> str:
        """Create the system prompt for the LLM"""
        return """You are an expert UNO player with advanced strategic thinking. 

Your goal is to:
1. Make legal moves according to UNO rules
2. Play strategically to win the game
3. Adapt your strategy based on game state
4. Provide clear reasoning for your decisions

You must respond with structured data containing:
- action: "play" or "draw"
- card_id: ID of card to play (if playing)
- color: color choice for wild cards
- reasoning: brief explanation of your strategy

Always ensure your moves are legal according to UNO rules."""

    def create_move_prompt(self, game_context: str) -> str:
        """Create the human prompt for move prediction"""
        return f"""
{game_context}

Analyze the current game state and decide your best move. Consider:

1. LEGAL MOVES: What cards can you legally play?
2. STRATEGY: Which move gives you the best advantage?
3. OPPONENTS: How can you disrupt their strategies?
4. HAND MANAGEMENT: Which cards should you keep/play?

Make your decision and explain your reasoning.
"""

    def predict_move(self, game_state: Dict) -> UNOMove:
        """
        Predict the next move using LangChain structured output

        Args:
            game_state: Current game state from BotsServer

        Returns:
            UNOMove object with the predicted move
        """
        try:
            # Get game context
            game_context = self.get_game_context(game_state)

            # Create messages
            system_message = SystemMessage(content=self.create_system_prompt())
            human_message = HumanMessage(content=self.create_move_prompt(game_context))

            # Get structured response from LLM
            try:
                response = self.structured_llm.invoke([system_message, human_message])
                logger.info(f"LLM predicted move: {response}")

                # Handle structured response
                if hasattr(response, "action"):
                    # Already a UNOMove-like object
                    return UNOMove(
                        action=getattr(response, "action", "draw"),
                        card_id=getattr(response, "card_id", None),
                        color=getattr(response, "color", None),
                        reasoning=getattr(
                            response, "reasoning", "No reasoning provided"
                        ),
                    )
                else:
                    # Try to convert dict response
                    response_dict = response if isinstance(response, dict) else {}
                    return UNOMove(
                        action=response_dict.get("action", "draw"),
                        card_id=response_dict.get("card_id"),
                        color=response_dict.get("color"),
                        reasoning=response_dict.get(
                            "reasoning", "No reasoning provided"
                        ),
                    )

            except Exception as structured_error:
                logger.warning(
                    f"Structured output failed, falling back to raw LLM: {structured_error}"
                )
                # Fallback to raw LLM response for providers that don't support structured output well
                raw_response = self.llm.invoke([system_message, human_message])
                logger.info(f"Raw LLM response: {raw_response}")

                # Parse raw text response manually
                return self._parse_raw_response(raw_response, game_state)

        except Exception as e:
            logger.error(f"Error predicting move: {e}")
            # Return a safe default move
            return UNOMove(
                action="draw",
                card_id=None,
                color=None,
                reasoning=f"Error occurred during prediction: {str(e)}",
            )

    def _parse_raw_response(self, raw_response, game_state: Dict) -> UNOMove:
        """
        Parse raw LLM response text into a UNOMove object

        Args:
            raw_response: Raw response from LLM (could be text or other format)
            game_state: Current game state to help map card descriptions to IDs

        Returns:
            UNOMove object with parsed move
        """
        import re
        import json

        try:
            # Extract text content from response
            if hasattr(raw_response, "content"):
                text = raw_response.content
            elif isinstance(raw_response, str):
                text = raw_response
            else:
                text = str(raw_response)

            logger.info(f"Parsing raw response: {text}")

            # Remove <think> tags if present (common in SambaNova responses)
            text_clean = text.replace("<think>", "").replace("</think>", "").strip()

            # Try to extract a JSON or dict-like structure from the response
            # Look for {...} or ```json ... ```
            json_match = None
            # Try to find a JSON block in triple backticks
            code_block_match = re.search(r"```(?:json)?\s*({.*?})\s*```", text_clean, re.DOTALL)
            if code_block_match:
                json_match = code_block_match.group(1)
            else:
                # Try to find the first {...} block in the text
                brace_match = re.search(r"({.*?})", text_clean, re.DOTALL)
                if brace_match:
                    json_match = brace_match.group(1)

            if json_match:
                try:
                    # Try to parse as JSON
                    response_dict = json.loads(json_match)
                    logger.info(f"Extracted structured dict from raw response: {response_dict}")
                    # Defensive: sometimes keys are not exactly as expected
                    action = response_dict.get("action", "draw")
                    card_id = response_dict.get("card_id")
                    color = response_dict.get("color")
                    reasoning = (
                        response_dict.get("reasoning")
                        or response_dict.get("resoning")
                        or "No reasoning provided"
                    )
                    return UNOMove(
                        action=action,
                        card_id=card_id,
                        color=color,
                        reasoning=reasoning,
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse JSON/dict from raw response: {e}")

            # If no structured block found, return a safe default
            return UNOMove(
                action="draw",
                card_id=None,
                color=None,
                reasoning="Could not extract structured move from LLM response.",
            )

        except Exception as e:
            logger.error(f"Error parsing raw response: {e}")
            return UNOMove(
                action="draw",
                card_id=None,
                color=None,
                reasoning=f"Failed to parse response: {str(e)}",
            )


    def _parse_raw_analysis(self, raw_analysis) -> GameAnalysis:
        """
        Parse raw LLM response text into a GameAnalysis object

        Args:
            raw_analysis: Raw response from LLM (could be text or other format)

        Returns:
            GameAnalysis object with parsed analysis
        """
        try:
            # Extract text content from response
            if hasattr(raw_analysis, "content"):
                text = raw_analysis.content
            elif isinstance(raw_analysis, str):
                text = raw_analysis
            else:
                text = str(raw_analysis)

            logger.info(f"Parsing raw analysis: {text}")

            # Simple parsing logic for analysis
            text_lower = text.lower()

            # Extract cards to keep (look for patterns like "keep card_1", "save card_2", etc.)
            cards_to_keep = []
            import re

            card_patterns = [
                r"keep\s+(card_?\d+)",
                r"save\s+(card_?\d+)",
                r"hold\s+(card_?\d+)",
                r"card_(\d+)",
                r"card(\d+)",
            ]

            for pattern in card_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    card_id = match if match.startswith("card") else f"card_{match}"
                    if card_id not in cards_to_keep:
                        cards_to_keep.append(card_id)

            # Extract threat level (look for numbers 1-10)
            threat_level = 5  # Default
            threat_matches = re.findall(
                r"threat\s*level[:\s]*(\d+)", text, re.IGNORECASE
            )
            if threat_matches:
                try:
                    threat_level = int(threat_matches[0])
                    if threat_level < 1 or threat_level > 10:
                        threat_level = 5
                except ValueError:
                    pass

            # Extract strategic notes
            strategic_notes = text.strip()
            if len(strategic_notes) > 300:  # Truncate if too long
                strategic_notes = strategic_notes[:300] + "..."

            return GameAnalysis(
                best_cards_to_keep=cards_to_keep,
                opponent_threat_level=threat_level,
                strategic_notes=strategic_notes,
            )

        except Exception as e:
            logger.error(f"Error parsing raw analysis: {e}")
            return GameAnalysis(
                best_cards_to_keep=[],
                opponent_threat_level=5,
                strategic_notes=f"Failed to parse analysis: {str(e)}",
            )

    def validate_move(
        self, move: UNOMove, game_state: Dict, player_cards: List[Dict]
    ) -> Tuple[bool, str]:
        """
        Validate if the predicted move is legal

        Args:
            move: The predicted move from the LLM
            game_state: Current game state
            player_cards: Current player's cards

        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            if move.action == "draw":
                return True, "Draw action is always valid"

            # Validate play action
            if not move.card_id:
                return False, "Card ID is required for play action"

            # Find the card in player's hand (coerce to string for comparison)
            move_card_id = str(move.card_id) if move.card_id is not None else None
            card = next((c for c in player_cards if c.get("id") == move_card_id), None)
            if not card:
                return False, f"Card with ID {move_card_id} not found in player's hand"

            # Get top card and game rules
            table_stack = game_state.get("tableStack", [])
            top_card = table_stack[0] if table_stack else None
            sum_drawing = game_state.get("sumDrawing", 0)
            last_player_drew = game_state.get("lastPlayerDrew", False)

            # Check if move is valid according to UNO rules
            is_valid = self._can_play_card(
                top_card, card, last_player_drew, sum_drawing
            )

            if not is_valid:
                reason = self._get_invalid_move_reason(
                    top_card, card, last_player_drew, sum_drawing
                )
                return False, reason

            # Validate color choice for wild cards
            if card.get("action") in ["wild", "draw four"]:
                if not move.color or move.color not in [
                    "red",
                    "blue",
                    "green",
                    "yellow",
                ]:
                    return (
                        False,
                        f"Invalid color '{move.color}' for wild card. Must be red, blue, green, or yellow",
                    )

            return True, "Move is valid"

        except Exception as e:
            logger.error(f"Error validating move: {e}")
            return False, f"Validation error: {str(e)}"

    def _can_play_card(
        self,
        top_card: Optional[Dict],
        new_card: Dict,
        last_player_drew: bool,
        sum_drawing: int,
    ) -> bool:
        """
        Check if a card can be played according to UNO rules

        This mirrors the logic from BotsServer.ts
        """
        # No card played yet
        if not top_card:
            return True

        # Check if there are pending draw cards
        is_old_drawing_card = top_card.get("action") and "draw" in top_card["action"]
        have_to_draw = is_old_drawing_card and not last_player_drew
        is_new_drawing_card = new_card.get("action") and "draw" in new_card["action"]

        # Wild cards can be played anytime if no draw is pending
        if not have_to_draw and new_card.get("action") == "wild":
            return True

        # Draw four can be played anytime
        if new_card.get("action") == "draw four":
            return True

        # Black cards can be played if no draw is pending
        if top_card.get("color") == "black" and not have_to_draw:
            return True

        # If draw is pending, only matching draw cards can be played
        if have_to_draw and is_new_drawing_card:
            return True

        # Regular card matching rules
        if not have_to_draw:
            # Color match
            if top_card.get("color") == new_card.get("color"):
                return True

            # Number match
            if (
                top_card.get("digit") is not None
                and new_card.get("digit") is not None
                and top_card["digit"] == new_card["digit"]
            ):
                return True

        return False

    def _get_invalid_move_reason(
        self,
        top_card: Optional[Dict],
        new_card: Dict,
        last_player_drew: bool,
        sum_drawing: int,
    ) -> str:
        """Get a human-readable reason why a move is invalid"""
        if not top_card:
            return "No top card to match against"

        is_old_drawing_card = top_card.get("action") and "draw" in top_card["action"]
        have_to_draw = is_old_drawing_card and not last_player_drew

        if have_to_draw:
            if not (new_card.get("action") and "draw" in new_card["action"]):
                return f"Must play a draw card or draw {sum_drawing} cards due to pending draw"

        if top_card.get("color") != "black":
            if (
                top_card.get("color") != new_card.get("color")
                and top_card.get("digit") != new_card.get("digit")
                and new_card.get("action") not in ["wild", "draw four"]
            ):
                return f"Card must match color ({top_card.get('color')}) or number ({top_card.get('digit')}) of top card"

        return "Move does not follow UNO rules"

    def get_intelligent_move(self, game_state: Dict, player_cards: List[Dict]) -> Dict:
        """
        Get an intelligent move with validation and retry logic

        Args:
            game_state: Current game state
            player_cards: Current player's cards

        Returns:
            Valid move dictionary (converted from Pydantic model)
        """
        for attempt in range(self.max_retries):
            try:
                # Predict move using structured output
                predicted_move = self.predict_move(game_state)

                # Validate move
                is_valid, reason = self.validate_move(
                    predicted_move, game_state, player_cards
                )

                if is_valid:
                    logger.info(f"LLM predicted valid move: {predicted_move}")
                    # Convert Pydantic model to dict for backward compatibility
                    move_dict = predicted_move.model_dump()
                    # Normalize card_id to string to align with game state card ids
                    if move_dict.get("action") == "play" and move_dict.get("card_id") is not None:
                        move_dict["card_id"] = str(move_dict["card_id"])
                    return move_dict
                else:
                    logger.warning(f"Attempt {attempt + 1}: Invalid move - {reason}")

                    # If this is not the last attempt, add the reason to the context for retry
                    if attempt < self.max_retries - 1:
                        game_state["lastValidationError"] = reason
                        game_state["lastInvalidMove"] = predicted_move.model_dump()

            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    break

        # If all attempts failed, return a safe default move
        logger.warning("All LLM attempts failed, using fallback draw move")
        return {
            "action": "draw",
            "reasoning": "LLM failed to predict valid move, defaulting to draw",
        }

    def get_game_analysis(
        self, game_state: Dict, player_cards: List[Dict]
    ) -> GameAnalysis:
        """
        Get extended game analysis using structured output

        Args:
            game_state: Current game state
            player_cards: Current player's cards

        Returns:
            GameAnalysis object with strategic insights
        """
        try:
            # Create analysis-specific LLM
            try:
                analysis_llm = self.llm.with_structured_output(GameAnalysis)
                game_context = self.get_game_context(game_state)

                analysis_prompt = f"""
{game_context}

Provide a strategic analysis of the current game state:

1. Identify which cards you should keep for strategic advantage
2. Assess the threat level of your opponents (1-10 scale)
3. Provide additional strategic notes and recommendations

Focus on long-term strategy and optimal play.
"""

                system_message = SystemMessage(
                    content="You are a strategic UNO analyst providing detailed game insights."
                )
                human_message = HumanMessage(content=analysis_prompt)

                analysis = analysis_llm.invoke([system_message, human_message])
            except Exception as structured_error:
                logger.warning(
                    f"Structured analysis failed, falling back to raw LLM: {structured_error}"
                )
                # Fallback to raw LLM response
                game_context = self.get_game_context(game_state)

                analysis_prompt = f"""
{game_context}

Provide a strategic analysis of the current game state. Focus on:
1. Which cards to keep for strategic advantage
2. Opponent threat level (1-10)
3. Strategic recommendations

Keep your response concise and actionable.
"""

                system_message = SystemMessage(
                    content="You are a strategic UNO analyst providing detailed game insights."
                )
                human_message = HumanMessage(content=analysis_prompt)

                raw_analysis = self.llm.invoke([system_message, human_message])
                return self._parse_raw_analysis(raw_analysis)

            # Handle different response types from LangChain
            if hasattr(analysis, "best_cards_to_keep"):
                # Already a GameAnalysis-like object
                return GameAnalysis(
                    best_cards_to_keep=getattr(analysis, "best_cards_to_keep", []),
                    opponent_threat_level=getattr(analysis, "opponent_threat_level", 5),
                    strategic_notes=getattr(
                        analysis, "strategic_notes", "No strategic notes provided"
                    ),
                )
            else:
                # Try to convert dict response
                analysis_dict = analysis if isinstance(analysis, dict) else {}
                return GameAnalysis(
                    best_cards_to_keep=analysis_dict.get("best_cards_to_keep", []),
                    opponent_threat_level=analysis_dict.get("opponent_threat_level", 5),
                    strategic_notes=analysis_dict.get(
                        "strategic_notes", "No strategic notes provided"
                    ),
                )

        except Exception as e:
            logger.error(f"Error getting game analysis: {e}")
            # Return default analysis
            return GameAnalysis(
                best_cards_to_keep=[],
                opponent_threat_level=5,
                strategic_notes=f"Analysis error: {str(e)}",
            )

    def update_game_state(self, game_state: Dict, move_result: Dict):
        """
        Update the game state based on the move result

        Args:
            game_state: Current game state to update
            move_result: Result of the executed move
        """
        try:
            # Clear any previous validation errors
            game_state.pop("lastValidationError", None)
            game_state.pop("lastInvalidMove", None)

            # Update game state based on move result
            if move_result.get("action") == "play":
                card_id = move_result.get("card_id")
                # normalize to string
                card_id = str(card_id) if card_id is not None else None
                if card_id:
                    # Remove played card from player's hand
                    player_cards = game_state.get("currentPlayer", {}).get("cards", [])
                    played_card = next(
                        (c for c in player_cards if c.get("id") == card_id), None
                    )

                    if played_card:
                        # Remove from hand
                        game_state["currentPlayer"]["cards"] = [
                            c for c in player_cards if c.get("id") != card_id
                        ]

                        # Add to table stack
                        table_stack = game_state.get("tableStack", [])
                        table_stack.insert(0, played_card)
                        game_state["tableStack"] = table_stack

                        # Update game effects
                        self._apply_card_effects(game_state, played_card, move_result)

                        # Reset draw flag
                        game_state["lastPlayerDrew"] = False

            elif move_result.get("action") == "draw":
                # Handle draw action
                game_state["lastPlayerDrew"] = True
                # Reset draw counter if drawing
                if game_state.get("sumDrawing", 0) > 0:
                    game_state["sumDrawing"] = 0

        except Exception as e:
            logger.error(f"Error updating game state: {e}")

    def _apply_card_effects(self, game_state: Dict, card: Dict, move_result: Dict):
        """Apply the effects of played cards to game state"""
        action = card.get("action")

        if action == "reverse":
            current_direction = game_state.get("direction", 1)
            game_state["direction"] = -current_direction

        elif action == "draw two":
            game_state["sumDrawing"] = game_state.get("sumDrawing", 0) + 2

        elif action == "draw four":
            game_state["sumDrawing"] = game_state.get("sumDrawing", 0) + 4
            # Update color for wild cards
            if move_result.get("color"):
                card["color"] = move_result["color"]

        elif action == "wild":
            # Update color for wild cards
            if move_result.get("color"):
                card["color"] = move_result["color"]
