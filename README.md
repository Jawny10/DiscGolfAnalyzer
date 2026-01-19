# Disc Golf Analyzer

A full-stack application for analyzing disc golf throws using computer vision and pose estimation.

## Architecture

```
┌─────────────────────────────────────┐     ┌─────────────────────────────────┐
│     Java Spring Boot (8080)         │     │     Python ML Service (5001)    │
│                                     │     │                                 │
│  ┌─────────────────────────────┐    │     │  ┌───────────────────────────┐  │
│  │ ThrowAnalysisController     │    │     │  │ Flask app.py              │  │
│  │   POST /api/throws/analyze  │────┼────►│  │   POST /analyze           │  │
│  │   POST /api/throws/         │    │     │  │   POST /analyze-pose      │  │
│  │        analyze-enhanced     │    │     │  └───────────────────────────┘  │
│  └─────────────────────────────┘    │     │              │                  │
│              │                      │     │              ▼                  │
│              ▼                      │     │  ┌───────────────────────────┐  │
│  ┌─────────────────────────────┐    │     │  │ MediaPipe Pose Extractor  │  │
│  │ VideoProcessingService      │    │     │  │ Biomechanics Analyzer     │  │
│  │ AnthropicVisionService      │    │     │  │ Feedback Generator        │  │
│  │ (optional Claude AI)        │    │     │  └───────────────────────────┘  │
│  └─────────────────────────────┘    │     │                                 │
└─────────────────────────────────────┘     └─────────────────────────────────┘
```

## Features

- **Disc Trajectory Tracking**: Detects and tracks disc flight path
- **Pose Estimation**: Extracts body landmarks using MediaPipe
- **Biomechanics Analysis**: Calculates key disc golf metrics:
  - Reachback depth
  - Hip rotation
  - Shoulder separation (X-factor)
  - Follow-through quality
  - Weight shift
- **Coaching Feedback**: Rule-based tips based on form analysis
- **Optional AI Enhancement**: Claude integration for natural language feedback

## Quick Start

### Prerequisites

- Java 17+
- Python 3.10+
- Maven 3.8+

### 1. Start the ML Service

```bash
cd ml-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### 2. Start the Spring Boot Application

```bash
# From project root
./mvnw spring-boot:run
```

### 3. Analyze a Throw

```bash
# Basic analysis
curl -X POST -F "video=@throw.mp4" http://localhost:8080/api/throws/analyze

# Enhanced analysis with pose detection
curl -X POST \
  -F "video=@throw.mp4" \
  -F "handedness=right" \
  -F "skillLevel=intermediate" \
  http://localhost:8080/api/throws/analyze-enhanced
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/throws/health` | GET | Health check |
| `/api/throws/analyze` | POST | Basic trajectory analysis |
| `/api/throws/analyze-enhanced` | POST | Full pose + trajectory analysis |

## Configuration

Edit `src/main/resources/application.properties`:

```properties
# ML Service
ml.service.url=http://localhost:5001

# Pose Analysis
analysis.pose.enabled=true
analysis.pose.min-confidence=0.5

# Anthropic Claude (optional)
anthropic.enabled=false
anthropic.model=claude-sonnet-4-20250514
# Set ANTHROPIC_API_KEY env var to enable
```

## Project Structure

```
discgolfanalyzer/
├── src/main/java/com/discgolfanalyzer/
│   ├── controller/          # REST controllers
│   ├── service/             # Business logic
│   │   └── video/           # Video processing
│   ├── dto/                 # Data transfer objects
│   ├── model/               # JPA entities
│   ├── repository/          # Data access
│   └── config/              # Spring configuration
├── ml-service/              # Python ML microservice
│   ├── app.py               # Flask application
│   ├── pose/                # Pose analysis module
│   ├── analysis/            # Analysis utilities
│   └── video_processor/     # Video processing
└── data-collection/         # Training data scripts (optional)
```

## Response Format

### Enhanced Analysis Response

```json
{
  "trajectory": {
    "flightPath": "hyzer",
    "distance": 85.5,
    "maxHeight": 12.3,
    "releaseAngle": 15.0,
    "techniqueFeedback": ["Good hyzer angle for controlled fades"]
  },
  "pose": {
    "detected": true,
    "metrics": {
      "reachbackDepthScore": 72,
      "hipRotationDegrees": 38.5,
      "shoulderSeparationDegrees": 32.0,
      "followThroughScore": 68,
      "weightShiftScore": 75
    }
  },
  "feedback": {
    "poseTips": [
      "Rotate your hips more during the throw",
      "Extend reachback further behind shoulder"
    ],
    "priorityFocus": "hip_rotation",
    "strengths": ["Good weight transfer"],
    "overallScore": 65
  },
  "aiEnhancedSummary": "..." // Only if anthropic.enabled=true
}
```

## Development

### Running Tests

```bash
# Java tests
./mvnw test

# Python tests
cd ml-service
pytest
```

### Building for Production

```bash
./mvnw clean package -DskipTests
java -jar target/discgolfanalyzer-0.0.1-SNAPSHOT.jar
```

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full Railway deployment instructions.

### Quick Deploy to Railway

1. Push to GitHub
2. Create new Railway project from repo
3. Add ML service (root: `ml-service`)
4. Add API service (root: `/`)
5. Set `ML_SERVICE_URL=http://ml-service.railway.internal:5001`
6. Generate public domain

### Local Docker Development

```bash
docker-compose up --build
# API: http://localhost:8080
# ML:  http://localhost:5001
```

## Tech Stack

**Backend**
- Java 17, Spring Boot 3.x
- Spring Data JPA, H2 (dev) / PostgreSQL (prod)
- Spring Security

**ML Service**
- Python 3.10+
- Flask
- OpenCV
- MediaPipe
- NumPy

**Optional**
- Anthropic Claude API for AI-enhanced feedback
