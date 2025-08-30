import librosa
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib.animation import PillowWriter
from matplotlib.lines import Line2D
import time

from config import *
from Note import *
from midi_part import midi_combinator
from midi_part import midi_comparator
from note_detection import *
from audio_process import *
from midi_part.midi_combinator import combine_midis
from midi_part.midi_comparator import generate_graph

start_time = time.time()

y_h, sr = preprocess_audio(INPUT_FILE)

# CQT parameters derived from config - much better for musical analysis
# CQT uses logarithmic frequency spacing that matches musical scales
HOP = max(1, int(sr / FPS))
# Reduce hop length for better time resolution while maintaining reasonable processing speed
HOP = min(HOP, int(sr * 0.01))  # Maximum 10ms hop for good temporal resolution

print("Computing Constant-Q Transform for enhanced musical analysis...")
cqt_start = time.time()

# CQT parameters optimized for musical note detection
# Each octave will have the same number of bins, making harmonic relationships easier to detect
bins_per_octave = 36  # 3 bins per semitone for high resolution
n_bins = 7 * bins_per_octave  # Cover 7 octaves (C1 to C8)
fmin = librosa.note_to_hz('C2')  # Start from C2 for musical range

# Compute CQT with parameters optimized for polyphonic music
CQT = librosa.cqt(
    y=y_h,
    sr=sr,
    fmin=fmin,
    n_bins=n_bins,
    bins_per_octave=bins_per_octave,
    hop_length=HOP,
    filter_scale=0.8,  # Tighter filters for better frequency separation
    sparsity=0.01      # Remove very small values to reduce noise
)

# Get magnitude and normalize
S = np.abs(CQT)
mx = np.max(S) if np.max(S) > 0 else 1.0
S_norm = S / mx

# Create frequency axis for CQT bins
# CQT frequencies are logarithmically spaced
cqt_freqs = librosa.cqt_frequencies(
    n_bins=n_bins, 
    fmin=fmin, 
    bins_per_octave=bins_per_octave
)

# Filter to desired frequency range
band = (cqt_freqs >= FREQ_MIN) & (cqt_freqs <= FREQ_MAX)
cqt_freqs_filtered = cqt_freqs[band]
S_filtered = S_norm[band, :]

print(f"CQT computation completed in {time.time() - cqt_start:.2f} seconds")

# Enhanced onset detection using multiple features for better accuracy
print("Detecting note onsets with enhanced algorithm...")
onset_start = time.time()

# Combine multiple onset detection methods for robustness
onset_frames_spectral = librosa.onset.onset_detect(
    y=y_h, sr=sr, hop_length=HOP,
    pre_max=0.03, post_max=0.03,
    pre_avg=0.1, post_avg=0.1,
    delta=0.05, wait=0.03,
    backtrack=True,
    units='frames'
)

# Use CQT-based onset detection for complementary information
onset_envelope = np.sum(np.diff(S_filtered, axis=1, prepend=0), axis=0)
onset_frames_cqt = librosa.util.peak_pick(
    onset_envelope,
    pre_max=3, post_max=3,
    pre_avg=10, post_avg=10,
    delta=0.1, wait=3
)

# Combine and deduplicate onsets
all_onset_frames = np.unique(np.concatenate([onset_frames_spectral, onset_frames_cqt]))
onset_times = librosa.frames_to_time(all_onset_frames, sr=sr, hop_length=HOP)

print(f"Onset detection completed in {time.time() - onset_start:.2f} seconds")
print(f"Detected {len(onset_times)} note onsets")

print(f"Audio preprocessing completed in {time.time() - start_time:.2f} seconds")

# -------------------- Initialize Note Tracker --------------------
note_tracker = NoteTracker(
    smoothing_time=SMOOTHING_TIME,
    min_duration=MIN_NOTE_DURATION,
    detection_threshold=DETECTION_THRESHOLD
)

# Number of frames = number of CQT columns
FRAME_COUNT = S_filtered.shape[1]
total_duration = FRAME_COUNT * HOP / sr

print(f"Processing info: {FRAME_COUNT} frames, HOP={HOP}")
print(f"CQT frequency range: {cqt_freqs_filtered[0]:.1f}-{cqt_freqs_filtered[-1]:.1f} Hz")
print(f"CQT bins: {len(cqt_freqs_filtered)}, bins per octave: {bins_per_octave}")
print(f"Total audio duration: {total_duration:.2f} seconds")
print(f"Smoothing settings: {SMOOTHING_TIME}s gap tolerance, {MIN_NOTE_DURATION}s min duration")
print(f"Animation enabled: {ENABLE_ANIMATION}")

# -------------------- Main Processing Loop --------------------
if ENABLE_ANIMATION:
    # -------------------- Enhanced Matplotlib animation for CQT --------------------
    print("Initializing matplotlib animation with CQT visualization...")
    fig, ax = plt.subplots(figsize=(12, 6), dpi=120)
    
    # Main CQT spectrum line
    line, = ax.plot([], [], lw=2, alpha=0.7, label="CQT Spectrum")
    
    # Lines for simultaneous notes (violet/purple)
    multi_lines = []
    multi_texts = []

    # Legend setup for CQT visualization
    multi_proxy = Line2D([0], [0], linestyle="-", alpha=0.8, color="purple", linewidth=2, label="Detected notes")
    onset_proxy = Line2D([0], [0], linestyle="|", alpha=0.8, color="orange", linewidth=3, label="Note onsets")

    handles = [line, multi_proxy, onset_proxy]
    labels = [line.get_label(), multi_proxy.get_label(), onset_proxy.get_label()]

    ax.set_xlim(FREQ_MIN, FREQ_MAX)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("Frequency (Hz)", fontsize=12)
    ax.set_ylabel("Normalized CQT Magnitude", fontsize=12)
    ax.set_title(f"Polyphonic Music Analysis with CQT - {INPUT_FILE}", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(handles=handles, labels=labels, loc='upper right')

    # Text annotations for spectral peaks and other info
    text_annotations = []
    
    # Onset indicator line
    onset_line = ax.axvline(x=0, lw=3, ls="|", color="orange", alpha=0.0)

    print("Starting CQT animation processing...")
    writer = PillowWriter(fps=FPS)
    with writer.saving(fig, OUTPUT_GIF, dpi=120):
        for frame_number in range(FRAME_COUNT):
            # Current time and CQT spectrum column
            current_time = frame_number * HOP / sr
            cqt_col = S_filtered[:, frame_number]
            
            # Update main spectrum plot
            line.set_data(cqt_freqs_filtered, cqt_col)

            # --- Detect simultaneous notes using enhanced CQT-based detection ---
            simultaneous_notes = detect_notes_with_cqt_onsets(
                cqt_col, cqt_freqs_filtered, current_time, onset_times, max_notes=5
            )
            
            # Update note tracker
            note_tracker.update_note_tracker_with_prediction(current_time, simultaneous_notes)

            # --- Show onset indicators ---
            near_onset = any(abs(current_time - onset_time) < 0.1 for onset_time in onset_times)
            if near_onset:
                onset_line.set_alpha(0.8)
                closest_onset_time = min(onset_times, key=lambda t: abs(t - current_time))
                onset_freq = FREQ_MIN + (FREQ_MAX - FREQ_MIN) * 0.1
                onset_line.set_xdata([onset_freq, onset_freq])
            else:
                onset_line.set_alpha(0.0)

            # --- Red labels: strongest CQT peaks ---
            for txt in text_annotations:
                txt.remove()
            text_annotations = []
            
            top_notes = top_note_labels_from_cqt(cqt_col, cqt_freqs_filtered, top_k=TOP_NOTES)
            for freq, name, mag in top_notes:
                text_annotations.append(
                    ax.text(freq, mag + 0.02, name, color="red", fontsize=10, 
                           ha="center", va="bottom", weight="bold",
                           bbox=dict(facecolor="white", alpha=0.7, edgecolor="red", pad=1))
                )

            # --- Purple lines: tracked simultaneous notes ---
            # Clear previous annotations
            for t in multi_texts:
                t.remove()
            multi_texts = []

            # Get active notes from tracker
            active_notes = note_tracker.get_active_notes()

            # Ensure we have enough lines
            while len(multi_lines) < len(active_notes):
                multi_lines.append(ax.axvline(x=0, lw=2, ls="-", alpha=0.8, color="purple"))

            # Update lines and labels for tracked notes
            text_xform = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
            for i, note_event in enumerate(active_notes):
                multi_lines[i].set_xdata([note_event.frequency, note_event.frequency])
                multi_lines[i].set_visible(True)
                
                # Add note label with duration info
                duration = current_time - note_event.start_time
                multi_texts.append(ax.text(
                    note_event.frequency, 0.92 - i * 0.04, 
                    f"{note_event.note_name} ({duration:.1f}s)", 
                    transform=text_xform,
                    ha="center", va="top", fontsize=11, 
                    color="purple", weight="bold",
                    bbox=dict(facecolor="white", alpha=0.8, edgecolor="purple", pad=1)
                ))

            # Hide unused lines
            for j in range(len(active_notes), len(multi_lines)):
                multi_lines[j].set_visible(False)

            # Add comprehensive frame info
            active_count = len(active_notes)
            completed_count = len(note_tracker.get_completed_notes())
            ax.text(0, 0, f"Time: {current_time:.2f}s | Active: {active_count} | Completed: {completed_count} | CQT Analysis", 
                    transform=ax.transAxes, fontsize=10,
                    bbox=dict(facecolor="white", alpha=0.8))

            writer.grab_frame()
            
            if frame_number % 30 == 0:  # Progress indicator
                progress = (frame_number + 1) / FRAME_COUNT * 100
                print(f"Animation progress: {progress:.1f}% | Active notes: {active_count}")

    print(f"CQT animation complete! Saved as '{OUTPUT_GIF}'")

else:
    # -------------------- Fast processing without animation (CQT-based) --------------------
    print("Processing audio with CQT analysis (fast mode)...")
    processing_start = time.time()
    
    for frame_number in range(FRAME_COUNT):
        # Current time and CQT spectrum column
        current_time = frame_number * HOP / sr
        cqt_col = S_filtered[:, frame_number]

        # Detect simultaneous notes using CQT-based onset-aware detection
        simultaneous_notes = detect_notes_with_cqt_onsets(
            cqt_col, cqt_freqs_filtered, current_time, onset_times, max_notes=5
        )
        
        # Update note tracker
        note_tracker.update_note_tracker_with_prediction(current_time, simultaneous_notes)
        
        # Progress indicator (less frequent than animation mode)
        if frame_number % 100 == 0:
            progress = (frame_number + 1) / FRAME_COUNT * 100
            active_count = len(note_tracker.get_active_notes())
            completed_count = len(note_tracker.get_completed_notes())
            elapsed = time.time() - processing_start
            est_total = elapsed / (frame_number + 1) * FRAME_COUNT
            est_remaining = est_total - elapsed
            print(f"Progress: {progress:.1f}% | Active: {active_count} | Completed: {completed_count} | ETA: {est_remaining:.1f}s")
    
    processing_time = time.time() - processing_start
    print(f"CQT audio processing completed in {processing_time:.2f} seconds")
    print(f"Processing speed: {FRAME_COUNT / processing_time:.1f} frames/second")

# Finalize note tracking
note_tracker.finalize(total_duration)

# Print comprehensive note timing summary
note_tracker.print_note_summary()

# Export to MIDI with enhanced metadata
print(f"\nExporting detected notes to MIDI...")
midi_start = time.time()

# Export piano notes (assuming most detected notes are piano in your current setup)
note_tracker.export_to_midi(
    OUTPUT_MIDI,
    tempo_bpm=MIDI_TEMPO_BPM,
    velocity_min=MIDI_VELOCITY_MIN,
    velocity_max=MIDI_VELOCITY_MAX,
    program=MIDI_PROGRAM  # Piano
)

# Export non-piano notes (for future instrument separation enhancement)
note_tracker.export_to_midi(
    OUTPUT_MIDI,
    tempo_bpm=MIDI_TEMPO_BPM,
    velocity_min=MIDI_VELOCITY_MIN,
    velocity_max=MIDI_VELOCITY_MAX,
    program=73  # Flute (placeholder for other instruments)
)

midi_time = time.time() - midi_start
print(f"MIDI export completed in {midi_time:.2f} seconds")

total_time = time.time() - start_time
print(f"\nTotal processing time with CQT: {total_time:.2f} seconds")
print("Enhanced polyphonic analysis complete!")

# When both instruments
# combine_midis(OUTPUT_MIDI + "0.mid", OUTPUT_MIDI + "73.mid", OUTPUT_MIDI + "both.mid")
# generate_graph("Sounds/Ecossaise_Beethoven.mid", [OUTPUT_MIDI + "both.mid"])

generate_graph("Output/Ecossaise_Beethoven.mid", ["Output/saved_data.mid", OUTPUT_MIDI + "73.mid"])
