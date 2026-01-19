# Data Collection Scripts

Scripts for collecting and processing disc golf form videos for model training.

## Scripts

| Script | Purpose |
|--------|---------|
| `download_pro_videos.py` | Download pro player form videos |
| `form_metrics.py` | Extract form metrics from videos |
| `model_generator.py` | Generate training data |
| `pose_extractor.py` | Extract pose data from videos |
| `pro_form_analyzer.py` | Analyze professional player form |
| `speed_analyzer.py` | Analyze disc/arm speed |
| `test_pro_model.py` | Test trained models |

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

These scripts are for development/research purposes. Generated data and models should be placed in the `data/` directory (gitignored).
