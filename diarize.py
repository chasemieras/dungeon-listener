import re

def extract_name_from_text(text):
    """Extract name from various introduction patterns"""
    text = text.strip()
    
    # Pattern 1: "My name is [Name]"
    match = re.search(r'\bmy name is\s+(\w+)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 2: "I'm [Name]" or "I am [Name]" 
    # But exclude common adjectives/emotions
    excluded_words = {
        'good', 'bad', 'fine', 'okay', 'worried', 'excited', 'happy', 'sad',
        'tired', 'busy', 'ready', 'done', 'sorry', 'here', 'back', 'late',
        'early', 'sick', 'well', 'hungry', 'thirsty', 'cold', 'hot', 'dead',
        'alive', 'free', 'busy', 'lost', 'found', 'sure', 'confused',
        'interested', 'bored', 'angry', 'calm', 'nervous', 'confident'
    }
    
    # Look for "I'm [word]" or "I am [word]" at start of sentence
    match = re.search(r'\b(?:i\'m|i am)\s+(\w+)', text, re.IGNORECASE)
    if match:
        potential_name = match.group(1).lower()
        # Only accept if it's not a common adjective and looks like a name
        if (potential_name not in excluded_words and 
            potential_name[0].isupper() in text):  # Check if originally capitalized
            return match.group(1)
    
    # Pattern 3: "This is [Name]" or "It's [Name]"
    match = re.search(r'\b(?:this is|it\'s)\s+(\w+)', text, re.IGNORECASE)
    if match:
        potential_name = match.group(1).lower()
        if potential_name not in excluded_words:
            return match.group(1)
    
    # Pattern 4: "[Name] speaking" or "[Name] here"
    match = re.search(r'^(\w+)\s+(?:speaking|here)', text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return None

def clean_name(name):
    if not name:
        return name
    
    import string
    name = name.strip(string.punctuation + string.whitespace)
    
    separators = [',', '.', '!', '?', ';', ':']
    for sep in separators:
        if sep in name:
            name = name.split(sep)[0].strip()
            break
    
    return name

def update_speaker_names(result):
    speaker_map = {}
    speaker_lines = {}
    
    for segment in result["segments"]:
        speaker = segment.get("speaker", "Unknown")
        if speaker not in speaker_lines:
            speaker_lines[speaker] = []
        speaker_lines[speaker].append(segment)
    
    for speaker, segments in speaker_lines.items():
        found = False
        for segment in segments[:10]:
            text = segment.get("text", "")
            name = extract_name_advanced(text)
            if name:
                cleaned_name = clean_name(name)
                if cleaned_name: 
                    speaker_map[speaker] = cleaned_name
                    found = True
                    break
        
        if not found:
            speaker_map[speaker] = speaker
    
    for segment in result["segments"]:
        speaker = segment.get("speaker", "Unknown")
        segment["speaker"] = speaker_map.get(speaker, speaker)

def extract_name_advanced(text):
    text = text.strip()
    
    patterns = [
        # "My name is [Name]" - most reliable
        (r'\bmy name is\s+(\w+(?:\s+\w+)?)', 0.9),
        
        # "I'm [Name]" but only if Name is capitalized and not common word
        (r'\bi\'m\s+([A-Z]\w+)', 0.7),
        
        # "I am [Name]" with same conditions
        (r'\bi am\s+([A-Z]\w+)', 0.7),
        
        # "This is [Name]" 
        (r'\bthis is\s+([A-Z]\w+)', 0.8),
        
        # "[Name] speaking/here"
        (r'^([A-Z]\w+)\s+(?:speaking|here)', 0.8),
        
        # "Call me [Name]"
        (r'\bcall me\s+(\w+)', 0.8),
    ]
    
    excluded_words = {
        'good', 'bad', 'fine', 'okay', 'worried', 'excited', 'happy', 'sad',
        'tired', 'busy', 'ready', 'done', 'sorry', 'here', 'back', 'late',
        'early', 'sick', 'well', 'hungry', 'thirsty', 'cold', 'hot', 'dead',
        'alive', 'free', 'lost', 'found', 'sure', 'confused', 'interested', 
        'bored', 'angry', 'calm', 'nervous', 'confident', 'available',
        'working', 'thinking', 'looking', 'trying', 'going', 'coming'
    }
    
    best_match = None
    best_confidence = 0
    
    for pattern, confidence in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            potential_name = match.group(1).strip()
            
            if potential_name.lower() in excluded_words:
                continue
                
            if confidence > best_confidence:
                best_match = potential_name
                best_confidence = confidence
    
    return best_match if best_confidence > 0.6 else None