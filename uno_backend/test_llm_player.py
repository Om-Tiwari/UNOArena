#!/usr/bin/env python3
"""
Comprehensive Test Suite for LLMPlayer class with LangChain Integration
This script tests all LLM providers with various game scenarios and provides analysis
"""

import os
import json
import time
from typing import Dict, List, Tuple
from LLMPlayer import LLMPlayer, UNOMove
from dotenv import load_dotenv
from config import PROVIDERS_CONFIG

load_dotenv()

class LLMTestResult:
    """Class to track test results for each provider"""
    
    def __init__(self, provider_name: str, model_name: str):
        self.provider_name = provider_name
        self.model_name = model_name
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.errors = []
        self.response_times = []
        self.validation_results = []
        
    def add_test_result(self, test_name: str, success: bool, error: str | None = None, response_time: float | None = None):
        self.total_tests += 1
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
            if error:
                self.errors.append(f"{test_name}: {error}")
        
        if response_time:
            self.response_times.append(response_time)
    
    def add_validation_result(self, test_name: str, is_valid: bool, reason: str):
        self.validation_results.append({
            "test": test_name,
            "valid": is_valid,
            "reason": reason
        })
    
    def get_success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100
    
    def get_avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

def get_available_providers() -> List[Tuple[str, str]]:
    """Get list of available LLM providers and models from the centralized config."""
    providers = []
    for provider_name, config in PROVIDERS_CONFIG.items():
        api_key_env = config.get("api_key_env")
        if api_key_env and os.getenv(api_key_env):
            models_to_test = config.get("supported_models", [config.get("default_model")])
            for model in models_to_test:
                if model:
                    providers.append((provider_name, model))
    return providers

def create_test_scenarios() -> List[Tuple[str, Dict, str]]:
    """Create comprehensive test scenarios for UNO game"""
    scenarios = []
    
    # Test Case 1: Simple number match (should play red 5)
    scenarios.append((
        "Number Match - Should Play Red 5",
        {
            "currentPlayer": {
                "id": "1", "name": "LLM Bot",
                "cards": [
                    {"id": "card_1", "digit": 5, "color": "red"},
                    {"id": "card_2", "digit": 7, "color": "blue"},
                    {"id": "card_3", "action": "skip", "color": "green"}
                ]
            },
            "tableStack": [{"id": "top_card", "digit": 5, "color": "green"}],
            "otherPlayers": [{"name": "Player 2", "cards": 6}, {"name": "Player 3", "cards": 4}],
            "direction": 1, "sumDrawing": 0, "lastPlayerDrew": False, "gamePhase": "playing"
        },
        "Should play red 5 to match the green 5 on table"
    ))
    
    # Test Case 2: Color match (should play blue 7)
    scenarios.append((
        "Color Match - Should Play Blue 7",
        {
            "currentPlayer": {
                "id": "1", "name": "LLM Bot",
                "cards": [
                    {"id": "card_1", "digit": 3, "color": "red"},
                    {"id": "card_2", "digit": 7, "color": "blue"},
                    {"id": "card_3", "action": "wild", "color": "black"}
                ]
            },
            "tableStack": [{"id": "top_card", "digit": 8, "color": "blue"}],
            "otherPlayers": [{"name": "Player 2", "cards": 3}, {"name": "Player 3", "cards": 5}],
            "direction": 1, "sumDrawing": 0, "lastPlayerDrew": False, "gamePhase": "playing"
        },
        "Should play blue 7 to match the blue color on table"
    ))
    
    # Test Case 3: Wild card with color choice
    scenarios.append((
        "Wild Card - Should Play Wild and Choose Color",
        {
            "currentPlayer": {
                "id": "1", "name": "LLM Bot",
                "cards": [
                    {"id": "card_1", "digit": 3, "color": "red"},
                    {"id": "card_2", "action": "wild", "color": "black"},
                    {"id": "card_3", "action": "draw four", "color": "black"}
                ]
            },
            "tableStack": [{"id": "top_card", "digit": 8, "color": "blue"}],
            "otherPlayers": [{"name": "Player 2", "cards": 3}, {"name": "Player 3", "cards": 5}],
            "direction": 1, "sumDrawing": 0, "lastPlayerDrew": False, "gamePhase": "playing"
        },
        "Should play wild card and specify a color (any color is valid)"
    ))
    
    # Test Case 4: Must draw scenario (pending draw cards)
    scenarios.append((
        "Must Draw - Pending Draw Cards",
        {
            "currentPlayer": {
                "id": "1", "name": "LLM Bot",
                "cards": [
                    {"id": "card_1", "digit": 4, "color": "red"},
                    {"id": "card_2", "action": "reverse", "color": "yellow"}
                ]
            },
            "tableStack": [{"id": "top_card", "action": "draw two", "color": "blue"}],
            "otherPlayers": [{"name": "Player 2", "cards": 5}, {"name": "Player 3", "cards": 3}],
            "direction": 1, "sumDrawing": 2, "lastPlayerDrew": False, "gamePhase": "playing"
        },
        "Must draw 2 cards due to pending draw two, no matching cards in hand"
    ))
    
    # Test Case 5: Can play draw card to match pending draw
    scenarios.append((
        "Draw Card Match - Should Play Draw Two",
        {
            "currentPlayer": {
                "id": "1", "name": "LLM Bot",
                "cards": [
                    {"id": "card_1", "digit": 4, "color": "red"},
                    {"id": "card_2", "action": "draw two", "color": "yellow"}
                ]
            },
            "tableStack": [{"id": "top_card", "action": "draw two", "color": "blue"}],
            "otherPlayers": [{"name": "Player 2", "cards": 5}, {"name": "Player 3", "cards": 3}],
            "direction": 1, "sumDrawing": 2, "lastPlayerDrew": False, "gamePhase": "playing"
        },
        "Should play yellow draw two to match the pending draw requirement"
    ))
    
    # Test Case 6: No playable cards - must draw
    scenarios.append((
        "No Playable Cards - Must Draw",
        {
            "currentPlayer": {
                "id": "1", "name": "LLM Bot",
                "cards": [
                    {"id": "card_1", "digit": 2, "color": "red"},
                    {"id": "card_2", "digit": 9, "color": "blue"}
                ]
            },
            "tableStack": [{"id": "top_card", "digit": 7, "color": "green"}],
            "otherPlayers": [{"name": "Player 2", "cards": 4}, {"name": "Player 3", "cards": 6}],
            "direction": 1, "sumDrawing": 0, "lastPlayerDrew": False, "gamePhase": "playing"
        },
        "No cards match green 7, must draw a card"
    ))
    
    # Test Case 7: Strategic play - multiple options
    scenarios.append((
        "Strategic Play - Multiple Valid Options",
        {
            "currentPlayer": {
                "id": "1", "name": "LLM Bot",
                "cards": [
                    {"id": "card_1", "digit": 5, "color": "red"},
                    {"id": "card_2", "digit": 5, "color": "blue"},
                    {"id": "card_3", "action": "skip", "color": "red"},
                    {"id": "card_4", "action": "wild", "color": "black"}
                ]
            },
            "tableStack": [{"id": "top_card", "digit": 5, "color": "green"}],
            "otherPlayers": [{"name": "Player 2", "cards": 2}, {"name": "Player 3", "cards": 8}],
            "direction": 1, "sumDrawing": 0, "lastPlayerDrew": False, "gamePhase": "playing"
        },
        "Multiple valid plays: red 5, blue 5, red skip, or wild. Should choose strategically"
    ))
    
    # Test Case 8: Game ending scenario
    scenarios.append((
        "Game Ending - Last Card",
        {
            "currentPlayer": {
                "id": "1", "name": "LLM Bot",
                "cards": [
                    {"id": "card_1", "digit": 5, "color": "red"}
                ]
            },
            "tableStack": [{"id": "top_card", "digit": 5, "color": "green"}],
            "otherPlayers": [{"name": "Player 2", "cards": 3}, {"name": "Player 3", "cards": 4}],
            "direction": 1, "sumDrawing": 0, "lastPlayerDrew": False, "gamePhase": "playing"
        },
        "Last card - should play red 5 to win the game"
    ))
    
    return scenarios

def test_provider_with_scenarios(provider_name: str, model_name: str) -> LLMTestResult:
    """Test a specific provider with all scenarios using LangChain"""
    print(f"\n🧪 Testing {provider_name.upper()} provider ({model_name})")
    print("=" * 60)
    
    result = LLMTestResult(provider_name, model_name)
    
    try:
        # Initialize LLM player with LangChain
        llm_player = LLMPlayer(provider=provider_name, model=model_name)
        print("✅ LLM Player initialized successfully")
        
        # Get test scenarios
        scenarios = create_test_scenarios()
        
        for i, (test_name, game_state, expected_behavior) in enumerate(scenarios, 1):
            print(f"\n📋 Test {i}: {test_name}")
            print(f"Expected: {expected_behavior}")
            
            try:
                # Time the LLM response
                start_time = time.time()
                
                # Use the new LangChain structured output method
                move = llm_player.get_intelligent_move(game_state, game_state["currentPlayer"]["cards"])
                response_time = time.time() - start_time
                
                print(f"LLM Response: {json.dumps(move, indent=2)}")
                print(f"Response Time: {response_time:.2f}s")
                
                # Convert dict to UNOMove for validation
                try:
                    uno_move = UNOMove(**move)
                    # Validate the move using the structured output
                    is_valid, reason = llm_player.validate_move(uno_move, game_state, game_state["currentPlayer"]["cards"])
                    result.add_validation_result(test_name, is_valid, reason)
                except Exception as validation_error:
                    print(f"⚠️  Validation error: {validation_error}")
                    is_valid = False
                    reason = f"Validation failed: {str(validation_error)}"
                    result.add_validation_result(test_name, is_valid, reason)
                
                # Determine if test passed based on move validity and logic
                test_passed = is_valid
                
                # Additional logic checks for specific scenarios
                if test_name == "Number Match - Should Play Red 5":
                    if move.get("action") == "play" and move.get("card_id") == "card_1":
                        test_passed = True
                    else:
                        test_passed = False
                        reason += f" - Expected to play red 5, got {move.get('action')}"
                
                elif test_name == "Color Match - Should Play Blue 7":
                    if move.get("action") == "play" and move.get("card_id") == "card_2":
                        test_passed = True
                    else:
                        test_passed = False
                        reason += f" - Expected to play blue 7, got {move.get('action')}"
                
                elif test_name == "Wild Card - Should Play Wild and Choose Color":
                    if move.get("action") == "play" and move.get("card_id") == "card_2" and move.get("color"):
                        test_passed = True
                    else:
                        test_passed = False
                        reason += f" - Expected to play wild with color, got {move.get('action')}"
                
                elif test_name == "Must Draw - Pending Draw Cards":
                    if move.get("action") == "draw":
                        test_passed = True
                    else:
                        test_passed = False
                        reason += " - Expected to draw due to pending draw cards"
                
                elif test_name == "Draw Card Match - Should Play Draw Two":
                    if move.get("action") == "play" and move.get("card_id") == "card_2":
                        test_passed = True
                    else:
                        test_passed = False
                        reason += " - Expected to play draw two to match pending draw"
                
                elif test_name == "No Playable Cards - Must Draw":
                    if move.get("action") == "draw":
                        test_passed = True
                    else:
                        test_passed = False
                        reason += " - Expected to draw when no cards match"
                
                elif test_name == "Strategic Play - Multiple Valid Options":
                    if move.get("action") == "play" and move.get("card_id"):
                        test_passed = True
                    else:
                        test_passed = False
                        reason += " - Expected to play one of multiple valid cards"
                
                elif test_name == "Game Ending - Last Card":
                    if move.get("action") == "play" and move.get("card_id") == "card_1":
                        test_passed = True
                    else:
                        test_passed = False
                        reason += " - Expected to play last card to win"
                
                # Record test result
                result.add_test_result(test_name, test_passed, reason, response_time)
                
                if test_passed:
                    print("✅ PASSED")
                else:
                    print(f"❌ FAILED: {reason}")
                
            except Exception as e:
                error_msg = f"Exception during test: {str(e)}"
                print(f"❌ ERROR: {error_msg}")
                result.add_test_result(test_name, False, error_msg)
        
    except Exception as e:
        print(f"❌ Failed to initialize {provider_name} provider: {str(e)}")
        result.add_test_result("Initialization", False, str(e))
    
    return result

def analyze_results(results: List[LLMTestResult]) -> None:
    """Analyze and display comprehensive test results"""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE TEST ANALYSIS - LangChain Integration")
    print("="*80)
    
    # Overall statistics
    total_providers = len(results)
    total_tests = sum(r.total_tests for r in results)
    total_passed = sum(r.passed_tests for r in results)
    total_failed = sum(r.failed_tests for r in results)
    
    print("\n🎯 OVERALL STATISTICS:")
    print(f"   Providers Tested: {total_providers}")
    print(f"   Total Tests: {total_tests}")
    print(f"   Total Passed: {total_passed}")
    print(f"   Total Failed: {total_failed}")
    print(f"   Overall Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "   Overall Success Rate: N/A")
    
    # Provider-by-provider analysis
    print("\n🔍 PROVIDER ANALYSIS:")
    print("-" * 80)
    
    # Sort providers by success rate
    sorted_results = sorted(results, key=lambda x: x.get_success_rate(), reverse=True)
    
    for i, result in enumerate(sorted_results):
        print(f"\n{i+1}. {result.provider_name.upper()} ({result.model_name})")
        print(f"   Success Rate: {result.get_success_rate():.1f}%")
        print(f"   Tests: {result.passed_tests}/{result.total_tests}")
        print(f"   Avg Response Time: {result.get_avg_response_time():.2f}s")
        
        if result.errors:
            print(f"   Errors: {len(result.errors)}")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"     - {error}")
            if len(result.errors) > 3:
                print(f"     ... and {len(result.errors) - 3} more errors")
    
    # Identify failing providers
    failing_providers = [r for r in results if r.get_success_rate() < 50]
    if failing_providers:
        print("\n⚠️  FAILING PROVIDERS (Success Rate < 50%):")
        print("-" * 50)
        for result in failing_providers:
            print(f"   {result.provider_name.upper()}: {result.get_success_rate():.1f}%")
            print("     Common Issues:")
            for error in result.errors[:2]:
                print(f"       - {error}")
    
    # Best performing provider
    if sorted_results:
        best = sorted_results[0]
        print("\n🏆 BEST PERFORMING PROVIDER:")
        print(f"   {best.provider_name.upper()}: {best.get_success_rate():.1f}% success rate")
        print(f"   Average response time: {best.get_avg_response_time():.2f}s")
    
    # LangChain specific recommendations
    print("\n💡 LANGCHAIN INTEGRATION RECOMMENDATIONS:")
    print("-" * 50)
    
    if total_passed / total_tests < 0.7:
        print("   ⚠️  Overall performance needs improvement. Consider:")
        print("      - Checking LangChain provider configurations")
        print("      - Verifying API keys and model availability")
        print("      - Reviewing structured output prompts")
        print("      - Testing with different temperature settings")
    
    working_providers = [r for r in results if r.get_success_rate() > 70]
    if working_providers:
        print(f"   ✅ Production-ready providers: {', '.join([r.provider_name.upper() for r in working_providers])}")
    
    if failing_providers:
        print(f"   ❌ Providers needing attention: {', '.join([r.provider_name.upper() for r in failing_providers])}")
    
    print("\n🚀 LANGCHAIN BENEFITS:")
    print("   - Structured output ensures consistent response format")
    print("   - Automatic validation and retry logic")
    print("   - Multiple provider support with unified interface")
    print("   - Advanced prompt engineering capabilities")

def main():
    """Main test execution"""
    print("🧪 COMPREHENSIVE LLMPlayer Test Suite - LangChain Integration")
    print("=" * 80)
    
    # Check available providers
    providers = get_available_providers()
    
    if not providers:
        print("❌ No LLM provider configuration found")
        print("Please set environment variables for at least one provider based on config.py:")
        for provider, config in PROVIDERS_CONFIG.items():
            if config.get("api_key_env"):
                print(f"export {config['api_key_env']}='your_key'")
        return
    
    print(f"🚀 Found {len(providers)} available provider/model combinations:")
    for name, model in providers:
        print(f"   - {name.upper()}: {model}")
    
    # Test all providers
    results = []
    for provider_name, model_name in providers:
        try:
            result = test_provider_with_scenarios(provider_name, model_name)
            results.append(result)
        except Exception as e:
            print(f"❌ Failed to test {provider_name}: {str(e)}")
    
    # Analyze results
    if results:
        analyze_results(results)
    else:
        print("\n❌ No providers were successfully tested")

if __name__ == "__main__":
    main()
