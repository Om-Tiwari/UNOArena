# UNO LLM Backend with LangChain Integration

A sophisticated UNO game backend that uses LangChain to provide intelligent, LLM-powered bot players with structured output and advanced game analysis.

## 🚀 Features

### **Core Capabilities**
- **LangChain Integration**: Modern LLM orchestration with structured output
- **Multiple Provider Support**: OpenAI, Groq, Anthropic, HuggingFace, Cerebras, SambaNova
- **Structured Responses**: Pydantic models ensure consistent, validated output
- **Advanced Game Logic**: Intelligent UNO strategy with move validation
- **Real-time Analysis**: Strategic insights and opponent threat assessment

### **Technical Features**
- **FastAPI Backend**: High-performance async API server
- **Type Safety**: Full TypeScript and Python type coverage
- **Error Handling**: Robust fallback mechanisms and retry logic
- **Performance Monitoring**: Response time tracking and provider comparison
- **Caching**: Intelligent LLM player caching for optimal performance

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   TypeScript    │    │   FastAPI        │    │   LangChain     │
│   BotsServer    │◄──►│   Backend        │◄──►│   LLM Players   │
│                 │    │                  │    │                 │
│ • Game Logic    │    │ • REST API       │    │ • OpenAI        │
│ • LLM Client    │    │ • Validation     │    │ • Groq          │
│ • Fallback      │    │ • Caching        │    │ • Anthropic     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📦 Installation

### **Prerequisites**
- Python 3.8+
- Node.js 16+ (for TypeScript integration)
- API keys for desired LLM providers

### **Backend Setup**
```bash
cd uno_backend

# Install dependencies
pip install -e .

# Set environment variables
cp .env.example .env
# Edit .env with your API keys
```

### **Environment Variables**
```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# Groq
GROQ_API_KEY=your_groq_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key

# HuggingFace
HUGGINGFACEHUB_API_TOKEN=your_huggingface_key

# Cerebras
CEREBRAS_API_KEY=your_cerebras_key

# SambaNova
SAMBANOVA_API_KEY=your_sambanova_key
```

## 🚀 Quick Start

### **1. Start the Backend**
```bash
cd uno_backend
python main.py
```

### **2. Test the Integration**
```bash
# Test basic functionality
python test_langchain_integration.py

# Test with specific providers
python test_llm_player.py
```

### **3. Use in TypeScript**
```typescript
import { LLMEnhancedBotsServer } from './bots_server_integration_example';

const enhancedServer = new LLMEnhancedBotsServer();
enhancedServer.setLLMUsage(true);
enhancedServer.setLLMProvider("openai", "gpt-4");

// Get intelligent move
const move = await enhancedServer.getLLMMove(gameState, playerCards);
```

## 🔧 API Endpoints

### **Core Endpoints**
- `GET /` - API information and features
- `GET /health` - Health check and status
- `GET /providers` - Available LLM providers

### **Game Endpoints**
- `POST /move` - Get LLM move prediction
- `POST /analysis` - Get strategic game analysis
- `POST /session` - Create game session
- `GET /session/{id}` - Get session details

### **Example Usage**
```python
import requests

# Get LLM move
response = requests.post("http://localhost:8000/move", json={
    "gameState": {
        "currentPlayer": {"id": "bot", "name": "LLM Bot", "cards": [...]},
        "tableStack": [{"digit": 5, "color": "green"}],
        "otherPlayers": [...],
        "direction": 1,
        "sumDrawing": 0,
        "lastPlayerDrew": False,
        "gamePhase": "playing"
    },
    "playerCards": [...],
    "provider": "openai",
    "model": "gpt-4"
})

move = response.json()
print(f"Action: {move['action']}")
print(f"Reasoning: {move['reasoning']}")
```

## 🧠 LLM Integration

### **Structured Output**
The system uses Pydantic models to ensure consistent, validated responses:

```python
class UNOMove(BaseModel):
    action: Literal["play", "draw"]
    card_id: Optional[str]
    color: Optional[Literal["red", "blue", "green", "yellow"]]
    reasoning: str

class GameAnalysis(BaseModel):
    best_cards_to_keep: List[str]
    opponent_threat_level: int
    strategic_notes: str
```

### **Provider Support**
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Groq**: Llama models, Mixtral
- **Anthropic**: Claude 3 models
- **HuggingFace**: Various open models
- **Cerebras**: Qwen models
- **SambaNova**: DeepSeek models

### **Prompt Engineering**
The system uses sophisticated prompts that:
- Provide clear game context and rules
- Request structured JSON responses
- Include strategic guidance
- Handle edge cases and special rules

## 🎮 Game Logic

### **Move Validation**
- **Color Matching**: Red, blue, green, yellow
- **Number Matching**: 0-9 digits
- **Action Cards**: Skip, reverse, draw two, draw four, wild
- **Special Rules**: Draw stacking, wild color selection

### **Strategic Features**
- **Card Priority**: Action cards > low numbers > high numbers
- **Opponent Analysis**: Threat level assessment
- **Hand Management**: Optimal card retention strategy
- **Timing**: Strategic use of special cards

## 🧪 Testing

### **Test Suite**
```bash
# Basic integration tests
python test_langchain_integration.py

# Comprehensive LLM tests
python test_llm_player.py

# Provider comparison
python test_llm_player.py --compare-providers
```

### **Test Coverage**
- ✅ Module imports and initialization
- ✅ Pydantic model validation
- ✅ Game context formatting
- ✅ Move validation logic
- ✅ LLM provider integration
- ✅ Error handling and fallbacks

## 🔄 Integration with BotsServer

### **TypeScript Integration**
```typescript
// Replace simple bot logic with LLM intelligence
class LLMEnhancedBotsServer extends EventsObject {
    async getLLMMove(gameState: any, playerCards: any[]): Promise<LLMMoveResponse> {
        // Call LangChain backend
        const response = await fetch(`${this.llmBackendUrl}/move`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                gameState: this.getGameStateForLLM(gameState),
                playerCards: playerCards,
                provider: this.apiProvider,
                model: this.model
            })
        });
        
        return response.json();
    }
}
```

### **Fallback Mechanisms**
- **LLM Unavailable**: Falls back to simple bot logic
- **Invalid Moves**: Automatic retry with feedback
- **Timeout Handling**: Graceful degradation
- **Error Recovery**: Robust error handling

## 📊 Performance & Monitoring

### **Metrics Tracked**
- Response times per provider
- Success rates per scenario
- Error types and frequencies
- Provider availability and reliability

### **Optimization Features**
- **Caching**: LLM player instances cached
- **Connection Pooling**: Efficient HTTP client usage
- **Timeout Management**: Configurable timeouts per provider
- **Load Balancing**: Provider selection based on performance

## 🚀 Advanced Features

### **Game Analysis**
```python
# Get strategic insights
analysis = await enhancedServer.getGameAnalysis(gameState, playerCards)
print(f"Threat Level: {analysis.opponent_threat_level}/10")
print(f"Keep Cards: {analysis.best_cards_to_keep}")
print(f"Strategy: {analysis.strategic_notes}")
```

### **Multi-Provider Testing**
```python
# Compare providers
providers = ["openai", "groq", "anthropic"]
results = {}

for provider in providers:
    enhancedServer.setLLMProvider(provider)
    start_time = time.time()
    move = await enhancedServer.getLLMMove(gameState, playerCards)
    response_time = time.time() - start_time
    
    results[provider] = {
        "move": move,
        "response_time": response_time
    }
```

## 🔧 Configuration

### **LLM Settings**
```typescript
enhancedServer.setLLMUsage(true);
enhancedServer.setLLMBackendUrl("http://localhost:8000");
enhancedServer.setLLMTimeout(15000);
enhancedServer.setLLMProvider("openai", "gpt-4");
```

### **Backend Configuration**
```python
# main.py
app = FastAPI(
    title="UNO LLM Backend with LangChain",
    description="Backend service for UNO game with LangChain-powered LLM bot players",
    version="2.0.0"
)

# CORS and middleware configuration
app.add_middleware(CORSMiddleware, allow_origins=["*"])
```

## 🐛 Troubleshooting

### **Common Issues**

#### **1. Import Errors**
```bash
# Install LangChain dependencies
pip install -e .

# Check Python version (3.8+ required)
python --version
```

#### **2. API Key Issues**
```bash
# Verify environment variables
echo $OPENAI_API_KEY
echo $GROQ_API_KEY

# Check .env file
cat .env
```

#### **3. Connection Issues**
```bash
# Test backend health
curl http://localhost:8000/health

# Check CORS settings
# Ensure frontend URL is allowed
```

#### **4. LLM Response Issues**
```bash
# Test with simple prompt
python test_langchain_integration.py

# Check provider status
curl http://localhost:8000/providers
```

### **Debug Mode**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test specific provider
python test_llm_player.py --provider openai
```

## 🔮 Future Enhancements

### **Planned Features**
- **Multi-Game Support**: Extend to other card games
- **Advanced Analytics**: Game performance metrics
- **A/B Testing**: Compare different LLM strategies
- **Real-time Learning**: Adapt strategies based on outcomes
- **Federated Learning**: Collaborative model improvement

### **Performance Improvements**
- **Async Processing**: Parallel LLM calls
- **Streaming Responses**: Real-time move generation
- **Model Fine-tuning**: Custom UNO-specific models
- **Edge Computing**: Local model deployment

## 📚 API Documentation

### **Interactive Docs**
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### **Code Examples**
See `examples/` directory for:
- Basic integration examples
- Advanced usage patterns
- Performance testing scripts
- Custom provider implementations

## 🤝 Contributing

### **Development Setup**
```bash
# Clone repository
git clone <repo-url>
cd uno_arena

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
flake8 .
mypy .
```

### **Code Standards**
- **Python**: Black formatting, flake8 linting, mypy type checking
- **TypeScript**: ESLint, Prettier, strict type checking
- **Testing**: pytest with 90%+ coverage target
- **Documentation**: Comprehensive docstrings and README updates

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain Team**: For the excellent LLM orchestration framework
- **FastAPI**: For the high-performance async web framework
- **UNO Community**: For game rules and strategy insights
- **Open Source Contributors**: For various LLM provider integrations

---

**Ready to play UNO with AI-powered intelligence?** 🎯

Start with the quick setup guide above, and you'll have intelligent UNO bots running in minutes!
