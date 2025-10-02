# model_generator.py
import json
import numpy as np
import logging
import os
from datetime import datetime


logger = logging.getLogger(__name__)

def convert_numpy_types(obj):
    """Convert NumPy types to standard Python types for JSON serialization"""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

def create_pro_model(metrics, output_path, pro_name, throw_type):
    """Create a model of a pro's form from metrics data"""
    logger.info(f"Creating model for {pro_name}'s {throw_type} throw")
    
    # Extract key phases of the throw based on key moments
    phases = identify_throw_phases(metrics)
    
    # Create the model
    model = {
        'pro_name': pro_name,
        'throw_type': throw_type,
        'date_created': datetime.now().isoformat(),
        'phases': phases,
        'metrics': metrics,
        'key_moments': metrics.get('key_moments', {})
    }
    
    # Remove the key_moments from metrics to avoid duplication
    if 'key_moments' in model['metrics']:
        del model['metrics']['key_moments']
    
    # Convert NumPy types to standard Python types
    model = convert_numpy_types(model)
    
    # Save the model
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    logger.info(f"Saved model to {output_path}")
    return model

def identify_throw_phases(metrics):
    """Identify key phases of the throw from metrics data"""
    phases = {
        'reach_back': {
            'frame_range': [0, 0],
            'key_metrics': {}
        },
        'pull_through': {
            'frame_range': [0, 0],
            'key_metrics': {}
        },
        'release': {
            'frame_range': [0, 0],
            'key_metrics': {}
        },
        'follow_through': {
            'frame_range': [0, 0],
            'key_metrics': {}
        }
    }
    
    key_moments = metrics.get('key_moments', {})
    
    # Get frame boundaries from the data
    all_frames = []
    for metric_name, values in metrics.items():
        if metric_name != 'key_moments' and values:
            all_frames.extend([v['frame'] for v in values])
    
    if not all_frames:
        logger.warning("No frame data found in metrics")
        return phases
        
    min_frame = min(all_frames)
    max_frame = max(all_frames)
    
    # Get reach back frame
    reach_back_frame = key_moments.get('reach_back', {}).get('frame')
    if reach_back_frame:
        # Define reach back phase: start 15 frames before detected point to the point itself
        reach_back_start = max(min_frame, reach_back_frame - 15)
        phases['reach_back']['frame_range'] = [reach_back_start, reach_back_frame]
        
        # Extract key metrics at reach back
        for metric_name, values in metrics.items():
            if metric_name != 'key_moments':
                # Find value closest to reach_back_frame
                values_at_frame = [v for v in values if v['frame'] == reach_back_frame]
                if values_at_frame:
                    phases['reach_back']['key_metrics'][metric_name] = values_at_frame[0]['value']
    
    # Get release frame
    release_frame = key_moments.get('release', {}).get('frame')
    if release_frame:
        # Define release phase: 5 frames before to 5 frames after
        phases['release']['frame_range'] = [release_frame - 5, release_frame + 5]
        
        # Define pull through phase: from reach back to just before release
        if reach_back_frame:
            phases['pull_through']['frame_range'] = [reach_back_frame, release_frame - 5]
        
        # Define follow through phase: from after release to end
        phases['follow_through']['frame_range'] = [release_frame + 5, max_frame]
        
        # Extract key metrics at release
        for metric_name, values in metrics.items():
            if metric_name != 'key_moments':
                # Find value closest to release_frame
                values_at_frame = [v for v in values if v['frame'] == release_frame]
                if values_at_frame:
                    phases['release']['key_metrics'][metric_name] = values_at_frame[0]['value']
    
    # If key moments weren't detected, make a best guess based on frame divisions
    if not reach_back_frame and not release_frame:
        total_frames = max_frame - min_frame
        quarter = total_frames // 4
        
        phases['reach_back']['frame_range'] = [min_frame, min_frame + quarter]
        phases['pull_through']['frame_range'] = [min_frame + quarter, min_frame + 2*quarter]
        phases['release']['frame_range'] = [min_frame + 2*quarter, min_frame + 3*quarter]
        phases['follow_through']['frame_range'] = [min_frame + 3*quarter, max_frame]
    
    return phases