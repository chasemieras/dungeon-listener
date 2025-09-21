def handle_unknown_speakers(result, max_gap_seconds=5.0, look_ahead=2):
    if not result.get("segments"):
        return result
    
    segments = result["segments"]
    
    for i, segment in enumerate(segments):
        if segment.get("speaker", "Unknown") == "Unknown":
            prev_speaker = get_previous_known_speaker(segments, i)
            next_speaker = get_next_known_speaker(segments, i, look_ahead)
            
            if (prev_speaker and next_speaker and 
                prev_speaker == next_speaker and
                is_within_time_gap(segments, i, max_gap_seconds)):
                segment["speaker"] = prev_speaker
            
            elif (prev_speaker and 
                  is_within_time_gap(segments, i, max_gap_seconds) and
                  should_assign_to_previous(segments, i, max_gap_seconds)):
                segment["speaker"] = prev_speaker
    
    return result

def should_assign_to_previous(segments, current_index, max_gap_seconds):
    if current_index == 0:
        return False
    
    current_segment = segments[current_index]
    prev_segment = segments[current_index - 1]
    
    current_start = current_segment.get("start", 0)
    prev_end = prev_segment.get("end", current_start)
    time_gap = current_start - prev_end
    
    if time_gap > max_gap_seconds:
        return False
    
    current_text = current_segment.get("text", "").strip().lower()
    
    if len(current_text) <= 10:
        return True
    
    filler_words = {"um", "uh", "ah", "hmm", "yeah", "yes", "no", "okay", "ok", "right", "sure"}
    if current_text in filler_words:
        return True
    
    continuation_words = {"and", "but", "so", "because", "however", "also", "then", "now"}
    first_word = current_text.split()[0] if current_text.split() else ""
    if first_word in continuation_words:
        return True
    
    return True

def get_previous_known_speaker(segments, current_index):
    for i in range(current_index - 1, -1, -1):
        speaker = segments[i].get("speaker", "Unknown")
        if speaker != "Unknown":
            return speaker
    return None

def get_next_known_speaker(segments, current_index, look_ahead):
    end_index = min(current_index + look_ahead + 1, len(segments))
    for i in range(current_index + 1, end_index):
        speaker = segments[i].get("speaker", "Unknown")
        if speaker != "Unknown":
            return speaker
    return None

def is_within_time_gap(segments, current_index, max_gap_seconds):
    if current_index == 0:
        return False
    
    current_start = segments[current_index].get("start", 0)
    prev_end = segments[current_index - 1].get("end", current_start)
    
    return (current_start - prev_end) <= max_gap_seconds