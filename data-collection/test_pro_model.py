# test_pro_model.py
import json
import matplotlib.pyplot as plt
import numpy as np
import cv2
import os
import argparse
import mediapipe as mp

def load_model(model_path):
    """Load a pro model from a JSON file"""
    with open(model_path, 'r') as f:
        return json.load(f)

# Update the visualize_metrics function in test_pro_model.py

def visualize_metrics(model):
    """Create visualizations of the key metrics in the model"""
    metrics = model['metrics']
    
    # Filter out non-metric entries
    metric_names = [name for name in metrics.keys() if name != 'key_moments']
    
    # Create a figure with subplots for each metric
    fig, axs = plt.subplots(len(metric_names), 1, figsize=(12, 4*len(metric_names)))
    
    for i, metric_name in enumerate(metric_names):
        values = metrics[metric_name]
        if not values:
            continue
            
        # Extract frame numbers and values
        frames = [v['frame'] for v in values]
        metric_values = [v['value'] for v in values]
        
        # Plot the metric
        ax = axs[i] if len(metric_names) > 1 else axs
        ax.plot(frames, metric_values, linewidth=2)
        ax.set_title(f"{metric_name.replace('_', ' ').title()}")
        ax.set_xlabel("Frame")
        ax.set_ylabel("Value")
        ax.grid(True, alpha=0.3)
        
        # Highlight key phases if available
        if 'phases' in model:
            colors = {
                'reach_back': 'lightblue',
                'pull_through': 'lightgreen',
                'release': 'salmon',
                'follow_through': 'lightyellow'
            }
            
            for phase_name, phase_data in model['phases'].items():
                if 'frame_range' in phase_data and len(phase_data['frame_range']) == 2:
                    start, end = phase_data['frame_range']
                    color = colors.get(phase_name, 'lightgray')
                    ax.axvspan(start, end, alpha=0.3, color=color, label=phase_name)
        
        # Mark key moments
        if 'key_moments' in model:
            for moment_name, moment_data in model['key_moments'].items():
                if 'frame' in moment_data:
                    frame = moment_data['frame']
                    ax.axvline(x=frame, color='red', linestyle='--', alpha=0.7)
                    ax.text(frame, ax.get_ylim()[1]*0.9, moment_name, 
                           rotation=90, verticalalignment='top')
    
    # Add a single legend for the phases
    if 'phases' in model:
        handles = [plt.Rectangle((0,0),1,1, color=colors[phase], alpha=0.3) 
                  for phase in colors if phase in model['phases']]
        labels = [phase.replace('_', ' ').title() 
                 for phase in colors if phase in model['phases']]
        axs[0].legend(handles, labels, loc='upper right')
    
    plt.tight_layout()
    plt.savefig("model_metrics.png", dpi=300)
    print(f"Metrics visualization saved to model_metrics.png")
    plt.close()

def render_model_over_video(model, video_path):
    """Render the model's key points over the original video"""
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return
        
    # Initialize MediaPipe pose for visualization
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    
    # Open the video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Create output video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('model_visualization.mp4', fourcc, fps, (width, height))
    
    # Process the video
    frame_idx = 0
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
            
        # Get model data for this frame if available
        frame_annotations = []
        for metric_name, values in model['metrics'].items():
            for value in values:
                if value['frame'] == frame_idx:
                    # Add annotation text
                    text = f"{metric_name}: {value['value']:.1f}"
                    frame_annotations.append(text)
        
        # Add annotations to frame
        y_offset = 30
        for text in frame_annotations:
            cv2.putText(frame, text, (20, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y_offset += 30
        
        # Add phase information if available
        if 'phases' in model:
            for phase_name, phase_data in model['phases'].items():
                if 'frame_range' in phase_data and len(phase_data['frame_range']) == 2:
                    start, end = phase_data['frame_range']
                    if start <= frame_idx <= end:
                        cv2.putText(frame, f"Phase: {phase_name}", (width - 250, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        
        # Write frame to output
        out.write(frame)
        frame_idx += 1
        
        # Progress
        if frame_idx % 30 == 0:
            print(f"Processed {frame_idx} frames")
    
    cap.release()
    out.release()
    print(f"Visualization video saved to model_visualization.mp4")

# Add to print_model_summary function
def print_model_summary(model):
    """Print a summary of the model's key information"""
    print("\n===== Pro Form Model Summary =====")
    print(f"Pro: {model.get('pro_name', 'Unknown')}")
    print(f"Throw Type: {model.get('throw_type', 'Unknown')}")
    
    # Print disc speed if available
    if 'disc_speed' in model['metrics'] and model['metrics']['disc_speed']:
        speed = model['metrics']['disc_speed'][0]['value']
        print(f"\nDisc Speed: {speed:.1f} mph")
    
    # Print metrics summary
    print("\nMetrics Summary:")
    for metric_name, values in model['metrics'].items():
        if values and metric_name != 'key_moments':
            metric_values = [v['value'] for v in values]
            print(f"  {metric_name}:")
            print(f"    Min: {min(metric_values):.2f}")
            print(f"    Max: {max(metric_values):.2f}")
            print(f"    Avg: {sum(metric_values)/len(metric_values):.2f}")
    
    # Print phases if available
    if 'phases' in model:
        print("\nThrow Phases:")
        for phase_name, phase_data in model['phases'].items():
            if 'frame_range' in phase_data:
                print(f"  {phase_name}: frames {phase_data['frame_range']}")

def main():
    parser = argparse.ArgumentParser(description='Test a pro form model')
    parser.add_argument('--model', type=str, required=True, help='Path to the pro model JSON file')
    parser.add_argument('--video', type=str, help='Path to the original video for visualization')
    args = parser.parse_args()
    
    # Load the model
    model = load_model(args.model)
    
    # Print summary
    print_model_summary(model)
    
    # Visualize metrics
    visualize_metrics(model)
    
    # Render visualization video if video path provided
    if args.video:
        render_model_over_video(model, args.video)

if __name__ == "__main__":
    main()