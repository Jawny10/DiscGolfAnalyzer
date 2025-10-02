# pro_form_analyzer.py
import os
import argparse
import logging
import cv2
import numpy as np
from pose_extractor import extract_poses
from form_metrics import calculate_metrics
from model_generator import create_pro_model
from speed_analyzer import SpeedAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pro_form_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def analyze_pro_video(video_path, pro_name, throw_type):
    """Analyze a single professional's throw video"""
    logger.info(f"Analyzing {throw_type} form for {pro_name} from {video_path}")
    
    # Extract poses from the video
    poses = extract_poses(video_path)
    if not poses:
        logger.error(f"Failed to extract poses from {video_path}")
        return False
        
    # Calculate form metrics
    metrics = calculate_metrics(poses)
    logger.info(f"Extracted {len(metrics.keys())} form metrics")
    
    # Calculate disc speed
    logger.info("Analyzing disc speed...")
    speed_analyzer = SpeedAnalyzer()
    
    # Get release frame from metrics if available
    release_frame = None
    if 'key_moments' in metrics and 'release' in metrics['key_moments']:
        release_frame = metrics['key_moments']['release'].get('frame')
    
    # Calculate disc speed
    speed_data = speed_analyzer.track_disc(
        video_path, 
        release_frame=release_frame
    )
    
    if speed_data and speed_data['speed']:
        logger.info(f"Disc speed: {speed_data['speed']['miles_per_hour']:.1f} mph")
        
        # Add speed to metrics
        metrics['disc_speed'] = [{
            'frame': speed_data['speed']['release_frame'],
            'value': speed_data['speed']['miles_per_hour']
        }]
    else:
        logger.warning("Could not calculate disc speed")
    
    # Create or update pro model
    output_dir = f"../data/pro_models/{pro_name}"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    model_path = f"{output_dir}/{throw_type}_model.json"
    create_pro_model(metrics, model_path, pro_name, throw_type)
    
    logger.info(f"Created model at {model_path}")
    return True

def process_all_pros(base_dir):
    """Process all videos for all pros in the directory structure"""
    for pro_dir in os.listdir(base_dir):
        pro_path = os.path.join(base_dir, pro_dir)
        if not os.path.isdir(pro_path):
            continue
            
        pro_name = pro_dir
        logger.info(f"Processing videos for {pro_name}")
        
        for throw_type_dir in os.listdir(pro_path):
            throw_type_path = os.path.join(pro_path, throw_type_dir)
            if not os.path.isdir(throw_type_path):
                continue
                
            throw_type = throw_type_dir
            logger.info(f"Processing {throw_type} throws for {pro_name}")
            
            for video_file in os.listdir(throw_type_path):
                if video_file.endswith(('.mp4', '.mov', '.webm')):
                    video_path = os.path.join(throw_type_path, video_file)
                    analyze_pro_video(video_path, pro_name, throw_type)

def analyze_user_video(video_path, output_path=None):
    """Analyze a user's throw video and compare to pro models"""
    logger.info(f"Analyzing user video: {video_path}")
    
    # Extract poses from the video
    poses = extract_poses(video_path)
    if not poses:
        logger.error(f"Failed to extract poses from {video_path}")
        return False
    
    # Calculate form metrics
    metrics = calculate_metrics(poses)
    logger.info(f"Extracted {len(metrics.keys())} form metrics")
    
    # Calculate disc speed
    logger.info("Analyzing disc speed...")
    speed_analyzer = SpeedAnalyzer()
    
    # Get release frame from metrics if available
    release_frame = None
    if 'key_moments' in metrics and 'release' in metrics['key_moments']:
        release_frame = metrics['key_moments']['release'].get('frame')
    
    # Calculate disc speed
    speed_data = speed_analyzer.track_disc(
        video_path, 
        release_frame=release_frame
    )
    
    if speed_data and speed_data['speed']:
        logger.info(f"Disc speed: {speed_data['speed']['miles_per_hour']:.1f} mph")
        
        # Add speed to metrics
        metrics['disc_speed'] = [{
            'frame': speed_data['speed']['release_frame'],
            'value': speed_data['speed']['miles_per_hour']
        }]
    
    # Save user metrics if output path provided
    if output_path:
        user_model = {
            'metrics': metrics,
            'key_moments': metrics.get('key_moments', {}),
            'phases': identify_throw_phases(metrics)
        }
        
        # Remove key_moments from metrics to avoid duplication
        if 'key_moments' in user_model['metrics']:
            del user_model['metrics']['key_moments']
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the model
        with open(output_path, 'w') as f:
            import json
            json.dump(user_model, f, indent=2)
        
        logger.info(f"Saved user metrics to {output_path}")
    
    return metrics

def compare_with_pro(user_metrics, pro_model_path):
    """Compare user metrics with a professional model"""
    logger.info(f"Comparing user throw with pro model: {pro_model_path}")
    
    # Load pro model
    with open(pro_model_path, 'r') as f:
        import json
        pro_model = json.load(f)
    
    # Calculate similarity scores for each metric
    similarity_scores = {}
    overall_similarity = 0
    metric_count = 0
    
    for metric_name in user_metrics:
        if metric_name == 'key_moments' or not user_metrics[metric_name]:
            continue
        
        if metric_name in pro_model['metrics'] and pro_model['metrics'][metric_name]:
            # Extract user values
            user_frames = [m['frame'] for m in user_metrics[metric_name]]
            user_values = [m['value'] for m in user_metrics[metric_name]]
            
            # Extract pro values
            pro_frames = [m['frame'] for m in pro_model['metrics'][metric_name]]
            pro_values = [m['value'] for m in pro_model['metrics'][metric_name]]
            
            # Normalize to percentage of video length
            user_frames_norm = [f / max(user_frames) for f in user_frames]
            pro_frames_norm = [f / max(pro_frames) for f in pro_frames]
            
            # Interpolate pro values to match user frames
            from scipy.interpolate import interp1d
            if len(pro_frames_norm) > 1:  # Need at least 2 points for interpolation
                pro_interp = interp1d(pro_frames_norm, pro_values, 
                                     bounds_error=False, fill_value="extrapolate")
                pro_values_interp = pro_interp(user_frames_norm)
                
                # Calculate similarity (1 - normalized difference)
                # Scale differences based on the metric type
                if metric_name in ['shoulder_rotation', 'hip_rotation', 'elbow_angle', 'wrist_angle']:
                    # Angle metrics - normalize by 180 degrees
                    diffs = np.abs(np.array(user_values) - np.array(pro_values_interp))
                    similarity = 1.0 - np.mean(diffs) / 180.0
                elif metric_name == 'disc_speed':
                    # Speed - normalize by max pro speed
                    max_pro_speed = max(pro_values)
                    diffs = np.abs(np.array(user_values) - np.array(pro_values_interp))
                    similarity = 1.0 - np.mean(diffs) / max_pro_speed
                else:
                    # Other metrics - use min-max normalization
                    max_val = max(max(user_values), max(pro_values))
                    min_val = min(min(user_values), min(pro_values))
                    if max_val > min_val:
                        diffs = np.abs(np.array(user_values) - np.array(pro_values_interp))
                        similarity = 1.0 - np.mean(diffs) / (max_val - min_val)
                    else:
                        similarity = 1.0
                
                similarity_scores[metric_name] = max(0.0, min(1.0, similarity))
                overall_similarity += similarity_scores[metric_name]
                metric_count += 1
    
    # Calculate overall similarity
    if metric_count > 0:
        overall_similarity /= metric_count
    
    return {
        'pro_name': pro_model.get('pro_name', 'Unknown Pro'),
        'throw_type': pro_model.get('throw_type', 'Unknown Throw'),
        'overall_similarity': overall_similarity,
        'metric_similarities': similarity_scores
    }

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

def main():
    parser = argparse.ArgumentParser(description='Analyze professional disc golfers form')
    parser.add_argument('--video', type=str, help='Process a single video')
    parser.add_argument('--pro', type=str, help='Pro name for single video')
    parser.add_argument('--type', type=str, help='Throw type for single video')
    parser.add_argument('--all', action='store_true', help='Process all videos in pro_videos directory')
    parser.add_argument('--user', type=str, help='Analyze a user video and compare to pro models')
    parser.add_argument('--compare', type=str, help='Pro model to compare with (used with --user)')
    args = parser.parse_args()
    
    if args.video and args.pro and args.type:
        analyze_pro_video(args.video, args.pro, args.type)
    elif args.all:
        process_all_pros('pro_videos')
    elif args.user:
        user_metrics = analyze_user_video(
            args.user, 
            output_path="../data/user_models/latest_user_throw.json"
        )
        
        if args.compare and user_metrics:
            # Compare with specified pro model
            comparison = compare_with_pro(
                user_metrics, 
                args.compare
            )
            
            print("\n===== Comparison Results =====")
            print(f"Pro: {comparison['pro_name']}")
            print(f"Throw Type: {comparison['throw_type']}")
            print(f"Overall Similarity: {comparison['overall_similarity']*100:.1f}%")
            print("\nMetric Similarities:")
            for metric, similarity in comparison['metric_similarities'].items():
                print(f"  {metric}: {similarity*100:.1f}%")
        
        elif user_metrics:
            # Compare with all available pro models
            pro_models_dir = "../data/pro_models"
            if os.path.exists(pro_models_dir):
                best_match = None
                best_similarity = -1
                
                for pro_dir in os.listdir(pro_models_dir):
                    pro_path = os.path.join(pro_models_dir, pro_dir)
                    if os.path.isdir(pro_path):
                        for model_file in os.listdir(pro_path):
                            if model_file.endswith('.json'):
                                model_path = os.path.join(pro_path, model_file)
                                comparison = compare_with_pro(user_metrics, model_path)
                                
                                if comparison['overall_similarity'] > best_similarity:
                                    best_similarity = comparison['overall_similarity']
                                    best_match = comparison
                
                if best_match:
                    print("\n===== Best Match =====")
                    print(f"Pro: {best_match['pro_name']}")
                    print(f"Throw Type: {best_match['throw_type']}")
                    print(f"Overall Similarity: {best_match['overall_similarity']*100:.1f}%")
                    print("\nMetric Similarities:")
                    for metric, similarity in best_match['metric_similarities'].items():
                        print(f"  {metric}: {similarity*100:.1f}%")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()