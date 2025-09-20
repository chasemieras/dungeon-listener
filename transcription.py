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

def process_audio(audio_path):
    print(f"[process_audio] Loading model: {modal} on {device}")
    total_start = time.time()
    model = whisperx.load_model(modal, device, compute_type=compute_type)
    print(f"[process_audio] Chunking audio...")
    chunks = chunk_audio(audio_path)
    all_segments = []
    language = "en"

    for idx, (start_time_chunk, chunk_audio_data) in enumerate(chunks):
        chunk_start = time.time()
        print(f"[process_audio] Transcribing chunk {idx+1}/{len(chunks)} (start={start_time_chunk:.2f}s)")
        result = model.transcribe(chunk_audio_data, batch_size=batch_size, language=language)
        print(f"[process_audio] Loading alignment model for language: {language}")
        model_a, metadata = whisperx.load_align_model(language_code=language, device=device)
        print(f"[process_audio] Aligning segments for chunk {idx+1}")
        aligned = whisperx.align(result["segments"], model_a, metadata, chunk_audio_data, device, return_char_alignments=False)
        for segment in aligned["segments"]:
            segment["start"] += start_time_chunk
            segment["end"] += start_time_chunk
        all_segments.extend(aligned["segments"])
        print(f"[process_audio] Finished chunk {idx+1}, segments so far: {len(all_segments)} (chunk time: {time.time() - chunk_start:.2f}s)")
        gc.collect(); torch.cuda.empty_cache(); del model_a

    print(f"[process_audio] Combining all segments. Total segments: {len(all_segments)}")
    combined_result = {"segments": all_segments, "language": language}
    print(f"[process_audio] Reloading full audio for output.")
    audio = whisperx.load_audio(audio_path)
    print(f"[process_audio] Done. Total processing time: {time.time() - total_start:.2f} seconds.")
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
        for segment in segments[:20]:
            text = segment.get("text", "")
            lowered = text.lower()
            if "my name is" in lowered:
                idx = lowered.find("my name is")
                after = text[idx + len("my name is"):].strip()
                name = after.split()[0] if after else speaker
                # name = after.split(".")[0].split(",")[0].strip()
                speaker_map[speaker] = name
                found = True
                break
        if not found:
            speaker_map[speaker] = speaker 

    for segment in result["segments"]:
        speaker = segment.get("speaker", "Unknown")
        segment["speaker"] = speaker_map.get(speaker, speaker)

def output_results_to_file(result):
    update_speaker_names(result)

    documents_folder = pathlib.Path.home() / "Documents"
    transcriptions_folder = documents_folder / "transcriptions"
    transcriptions_folder.mkdir(parents=True, exist_ok=True)

    dt = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = transcriptions_folder / f"transcription_{dt}.md"
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

    # Open the file in the default file viewer
    try:
        import subprocess
        subprocess.Popen(['xdg-open', str(output_path)])
        print(f"[output_results_to_file] Opened {output_path} in the default viewer.")
    except Exception as e:
        print(f"[output_results_to_file] Could not open file: {e}")