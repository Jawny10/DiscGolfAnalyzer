# ml-service/analysis/feedback.py

def generate_feedback(technique_analysis):
    """
    Generate actionable feedback based on technique analysis.
    
    Args:
        technique_analysis (dict): Dictionary containing technique analysis
        
    Returns:
        list: List of feedback strings
    """
    feedback = []
    
    # Check for release angle issues
    release_angle = technique_analysis.get("release_angle", 0)
    if release_angle < 0:
        feedback.append(f"Your release angle is too low ({release_angle:.1f} degrees). Try raising your arm slightly at release.")
    elif release_angle > 30:
        feedback.append(f"Your release angle is too high ({release_angle:.1f} degrees). Try lowering your arm slightly at release.")
    else:
        feedback.append(f"Your release angle of {release_angle:.1f} degrees is good!")
    
    # Check for consistency
    consistency = technique_analysis.get("consistency", 0)
    if consistency < 0.7:
        feedback.append("Your throw consistency needs improvement. Focus on a smoother release motion.")
    else:
        feedback.append("Your throw has good consistency in velocity!")
    
    # Check for wobble
    wobble = technique_analysis.get("wobble", 0)
    if wobble > 10:
        feedback.append(f"Your disc has significant wobble. Focus on a cleaner release with your wrist aligned to the flight plate.")
    elif wobble > 5:
        feedback.append(f"Your disc has some wobble. Try to keep your wrist firmer during release.")
    else:
        feedback.append("Your disc stability looks good with minimal wobble!")
    
    # Flight path feedback
    flight_path = technique_analysis.get("flight_path", "undetermined")
    if flight_path == "hyzer":
        feedback.append("Your throw has a hyzer flight path (curves right for right-handed backhand). This is good for controlled placement.")
    elif flight_path == "anhyzer":
        feedback.append("Your throw has an anhyzer flight path (curves left for right-handed backhand). This can help with distance but may sacrifice accuracy.")
    elif flight_path == "straight":
        feedback.append("Your throw has a very straight flight path. Great for hitting narrow fairways!")
    
    return feedback