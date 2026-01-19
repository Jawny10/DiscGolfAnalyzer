# ML Service - Disc Golf Video Analysis

Flask-based microservice for analyzing disc golf throw videos using computer vision and pose estimation.

## Features

- **Disc Trajectory Detection**: Track disc flight path using OpenCV background subtraction
- **Pose Estimation**: Extract body landmarks using MediaPipe
- **Biomechanics Analysis**: Calculate key disc golf metrics (reachback, hip rotation, X-factor)
- **Coaching Feedback**: Generate actionable tips based on form analysis

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/analyze` | POST | Basic trajectory analysis |
| `/analyze-pose` | POST | Full pose + trajectory analysis |

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the service
python app.py
```

The service runs on port 5001 by default.

## API Usage

### Basic Analysis
```bash
curl -X POST -F "video=@throw.mp4" http://localhost:5001/analyze
```

### Enhanced Pose Analysis
```bash
curl -X POST \
  -F "video=@throw.mp4" \
  -F "handedness=right" \
  -F "skill_level=intermediate" \
  http://localhost:5001/analyze-pose
```

## Project Structure

```
ml-service/
├── app.py                 # Flask application & endpoints
├── requirements.txt       # Python dependencies
├── pose/                  # Pose analysis module
│   ├── mediapipe_extractor.py  # MediaPipe pose extraction
│   ├── biomechanics.py         # Disc golf metrics calculation
│   └── feedback_rules.py       # Rule-based feedback generation
├── analysis/              # Legacy analysis utilities
│   ├── feedback.py
│   └── technique.py
└── video_processor/       # Video processing utilities
    ├── disc_detection.py
    └── trajectory.py
```

## Pose Analysis Response

```json
{
  "trajectory": {
    "flightPath": "hyzer",
    "distance": 85.5,
    "maxHeight": 12.3,
    "releaseAngle": 15.0
  },
  "pose": {
    "detected": true,
    "metrics": {
      "reachback_depth_score": 72,
      "hip_rotation_degrees": 38.5,
      "shoulder_separation_degrees": 32.0,
      "follow_through_score": 68,
      "weight_shift_score": 75
    }
  },
  "feedback": {
    "pose_tips": ["Rotate hips more", "Extend reachback"],
    "priority_focus": "hip_rotation",
    "overall_score": 65
  }
}
```

## Dependencies

- Flask - Web framework
- OpenCV - Video processing & disc detection
- MediaPipe - Pose estimation
- NumPy - Numerical computations
