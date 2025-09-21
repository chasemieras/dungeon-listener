import whisperx
import gc
import torch
import numpy as np
import datetime
import time
import pathlib

device = "cpu"
batch_size = 16
compute_type = "float32"
modal = "large-v2"

def chunk_audio(audio_path, chunk_length_s=300):
    print(f"[chunk_audio] Loading audio from: {audio_path}")
    start_time = time.time()
    audio = whisperx.load_audio(audio_path)
    sr = 16000
    total_len = len(audio) / sr
    print(f"[chunk_audio] Audio length: {total_len:.2f} seconds. Chunking into {chunk_length_s}s segments.")
    chunks = []
    for start in np.arange(0, total_len, chunk_length_s):
        end = min(start + chunk_length_s, total_len)
        s = int(start * sr)
        e = int(end * sr)
        print(f"[chunk_audio] Creating chunk: start={start:.2f}s, end={end:.2f}s")
        chunks.append((start, audio[s:e]))
    print(f"[chunk_audio] Total chunks created: {len(chunks)}")
    print(f"[chunk_audio] Done in {time.time() - start_time:.2f} seconds.")
    return chunks

def format_time(seconds):
    """Convert seconds to human-readable format"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{int(minutes)}m {remaining_seconds:.0f}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"

def process_audio(audio_path):
    print(f"[process_audio] Loading model: {modal} on {device}")
    total_start = time.time()
    model = whisperx.load_model(modal, device, compute_type=compute_type)
    
    print(f"[process_audio] Chunking audio...")
    chunks = chunk_audio(audio_path)
    total_chunks = len(chunks)
    
    all_segments = []
    language = "en"
    
    for idx, (start_time_chunk, chunk_audio_data) in enumerate(chunks):
        chunk_start = time.time()
        print(f"[process_audio] Transcribing chunk {idx+1}/{total_chunks} (start={start_time_chunk:.2f}s)")
        
        result = model.transcribe(chunk_audio_data, batch_size=batch_size, language=language)
        print(f"[process_audio] Loading alignment model for language: {language}")
        model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
        print(f"[process_audio] Aligning segments for chunk {idx+1}")
        aligned = whisperx.align(result["segments"], model_a, metadata, chunk_audio_data, device, return_char_alignments=False)
        
        for segment in aligned["segments"]:
            segment["start"] += start_time_chunk
            segment["end"] += start_time_chunk
        all_segments.extend(aligned["segments"])
        
        chunk_time = time.time() - chunk_start
        print(f"[process_audio] Finished chunk {idx+1}, segments so far: {len(all_segments)} (chunk time: {format_time(chunk_time)})")
        
        if idx == 0:
            remaining_chunks = total_chunks - 1
            estimated_remaining_time = chunk_time * remaining_chunks
            estimated_total_time = chunk_time * total_chunks
            
            print(f"[time_estimate] Based on first chunk ({format_time(chunk_time)}):")
            print(f"[time_estimate] - Remaining chunks: {remaining_chunks}")
            print(f"[time_estimate] - Estimated remaining time: {format_time(estimated_remaining_time)}")
            print(f"[time_estimate] - Estimated total processing time: {format_time(estimated_total_time)}")
        
        elif idx > 0 and (idx + 1) % 3 == 0:
            elapsed_processing = time.time() - total_start
            avg_chunk_time = elapsed_processing / (idx + 1)
            remaining_chunks = total_chunks - (idx + 1)
            updated_estimate = elapsed_processing + (avg_chunk_time * remaining_chunks)
            
            print(f"[time_estimate] Average chunk time so far: {format_time(avg_chunk_time)}")
            print(f"[time_estimate] Updated estimated total time: {format_time(updated_estimate)}")
        
        gc.collect()
        torch.cuda.empty_cache()
        del model_a
    
    print(f"[process_audio] Combining all segments. Total segments: {len(all_segments)}")
    combined_result = {"segments": all_segments, "language": language}
    
    print(f"[process_audio] Reloading full audio for output.")
    audio = whisperx.load_audio(audio_path)
    
    total_time = time.time() - total_start
    print(f"[process_audio] Done. Total processing time: {format_time(total_time)}")
    
    return audio, combined_result

def diarize_results(token, audio, result_from_whisper):
    print(f"[diarize_results] Loading diarization pipeline.")
    start_time = time.time()
    diarize_model = whisperx.diarize.DiarizationPipeline(use_auth_token=token, device=device)
    print(f"[diarize_results] Running diarization on audio.")
    diarize_segments = diarize_model(audio)
    print(f"[diarize_results] Assigning speakers to words.")
    result = whisperx.assign_word_speakers(diarize_segments, result_from_whisper)
    print(f"[diarize_results] Done in {time.time() - start_time:.2f} seconds.")
    return result
    
def display_results(result):
    print(f"[display_results] Displaying transcription results:")
    start_time = time.time()
    for segment in result["segments"]:
        speaker = segment.get("speaker", "Unknown")
        start = segment["start"]
        end = segment["end"]
        text = segment["text"]
        print(f"{speaker} [{start:.2f}-{end:.2f}]: {text}")
    print(f"[display_results] Done displaying in {time.time() - start_time:.2f} seconds.")

def output_results_to_file(result, file_name, file_type):
    import diarize;
    diarize.update_speaker_names(result)
    documents_folder = pathlib.Path.home() / "Documents"
    transcriptions_folder = documents_folder / "transcriptions"
    transcriptions_folder.mkdir(parents=True, exist_ok=True)
    
    output_path = None
    if file_type == 1:
        output_path = markdown(transcriptions_folder, result, file_name)
    if file_type == 2:
        output_path = html(transcriptions_folder, result, file_name)
    if file_type == 3:
        output_path = txt(transcriptions_folder, result, file_name)

    try:
        import subprocess
        subprocess.Popen(['xdg-open', str(output_path)])
        print(f"[output_results_to_file] Opened {output_path} in the default viewer.")
    except Exception as e:
        print(f"[output_results_to_file] Could not open file: {e}")
        
        
def markdown(transcriptions_folder, result, file_name):
    dt = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = transcriptions_folder / f"{file_name}_{dt}.md"
    print(f"[output_results_to_file] Writing results to {output_path} (Markdown format)")
    start_time = time.time()
    with open(output_path, "w") as f:
        for segment in result["segments"]:
            speaker = segment.get("speaker", "Unknown")
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]
            f.write(f"**{speaker}** [{start:.2f}-{end:.2f}]: {text}\n")
    print(f"[output_results_to_file] Done writing in {time.time() - start_time:.2f} seconds.")
    return output_path

def html(transcriptions_folder, result, file_name):
    dt = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = transcriptions_folder / f"{file_name}_{dt}.html"
    print(f"[output_results_to_file] Writing results to {output_path} (HTML format)")
    start_time = time.time()
    with open(output_path, "w") as f:
        for segment in result["segments"]:
            speaker = segment.get("speaker", "Unknown")
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]
            f.write(f"<b>{speaker}</b> [{start:.2f}-{end:.2f}]: {text}\n")
    print(f"[output_results_to_file] Done writing in {time.time() - start_time:.2f} seconds.")
    return output_path


def txt(transcriptions_folder, result, file_name):
    dt = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = transcriptions_folder / f"{file_name}_{dt}.txt"
    print(f"[output_results_to_file] Writing results to {output_path} (Text format)")
    start_time = time.time()
    with open(output_path, "w") as f:
        for segment in result["segments"]:
            speaker = segment.get("speaker", "Unknown")
            start = segment["start"]
            end = segment["end"]
            text = segment["text"]
            f.write(f"{speaker} [{start:.2f}-{end:.2f}]: {text}\n")
    print(f"[output_results_to_file] Done writing in {time.time() - start_time:.2f} seconds.")
    return output_path
