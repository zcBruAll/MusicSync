import librosa
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib.animation import PillowWriter
from matplotlib.lines import Line2D
import time

from config import *
from Note import *
from note_detection import *
from audio_process import *

start_time = time.time()

y_h, sr = preprocess_audio(INPUT_FILE)

# STFT params derived from config
N_FFT = int(sr * FFT_WINDOWS_SECONDS)
HOP = max(1, int(sr / FPS))
# ADD: Reduce hop length for better time resolution
HOP = min(HOP, N_FFT // 4)  # Ensure 75% overlap minimum for better time precision

# Complex STFT with better parameters for onset detection
D = librosa.stft(y_h, n_fft=N_FFT, hop_length=HOP, win_length=N_FFT,
                 window="hann", center=True)  # CHANGED: center=True for better alignment
S = np.abs(D)                              # magnitude
mx = np.max(S) if np.max(S) > 0 else 1.0   # global max for normalization
S_norm = S / mx

# Frequency axis from librosa helper
xf = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)

# Limit to desired frequency band once, and remember slice
band = (xf >= FREQ_MIN) & (xf <= FREQ_MAX)
xf_b = xf[band]
S_b = S_norm[band, :]

onset_frames = librosa.onset.onset_detect(
    y=y_h, sr=sr, hop_length=HOP, 
    pre_max=0.03, post_max=0.03,  # Short pre/post max for faster response
    pre_avg=0.1, post_avg=0.1,
    delta=0.05, wait=0.03, # Shorter wait time
    backtrack=True
)
onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=HOP)

# -------------------- Pitch tracking with librosa --------------------
# Monophonic f0
f0, vflag, vprob = librosa.pyin(
    y=y_h,
    sr=sr,
    fmin=librosa.note_to_hz("C2"),
    fmax=librosa.note_to_hz("C7"),
    frame_length=N_FFT,
    hop_length=HOP,
    center=False
)

print(f"Audio preprocessing completed in {time.time() - start_time:.2f} seconds")

# -------------------- Initialize Note Tracker --------------------
note_tracker = NoteTracker(
    smoothing_time=SMOOTHING_TIME,
    min_duration=MIN_NOTE_DURATION,
    detection_threshold=DETECTION_THRESHOLD
)

# Number of frames = number of STFT columns
FRAME_COUNT = S_b.shape[1]
total_duration = FRAME_COUNT * HOP / sr

print(f"Processing info: {FRAME_COUNT} frames, HOP={HOP}, N_FFT={N_FFT}")
print(f"Frequency range: {FREQ_MIN}-{FREQ_MAX} Hz")
print(f"Total audio duration: {total_duration:.2f} seconds")
print(f"Smoothing settings: {SMOOTHING_TIME}s gap tolerance, {MIN_NOTE_DURATION}s min duration")
print(f"Animation enabled: {ENABLE_ANIMATION}")

# -------------------- Main Processing Loop --------------------
if ENABLE_ANIMATION:
    # -------------------- Matplotlib animation --------------------
    print("Initializing matplotlib animation...")
    fig, ax = plt.subplots(figsize=(12, 6), dpi=120)
    line, = ax.plot([], [], lw=2, alpha=0.7, label="Spectrum")  # FFT spectrum line
    f0_line = ax.axvline(x=0, lw=3, ls="--", color="blue", alpha=0.8, label="Monophonic f0")
    harm_lines = [ax.axvline(x=0, lw=2, ls=":", alpha=0.5, color="blue") for _ in range(5)]

    # Lines for simultaneous notes (violet)
    multi_lines = []
    multi_texts = []

    handles, labels = ax.get_legend_handles_labels()

    harm_proxy = Line2D([0], [0], linestyle=":", color="blue", alpha=0.5, linewidth=2, label="f0 harmonics")
    multi_proxy = Line2D([0], [0], linestyle="-", alpha=0.8, color="purple", linewidth=2, label="Simultaneous notes")

    handles = [line, f0_line, harm_proxy, multi_proxy]
    labels = [line.get_label(), f0_line.get_label(), harm_proxy.get_label(), multi_proxy.get_label()]

    ax.set_xlim(FREQ_MIN, FREQ_MAX)
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("Frequency (Hz)", fontsize=12)
    ax.set_ylabel("Normalized Magnitude", fontsize=12)
    ax.set_title(f"Polyphonic Music Analysis with Note Timing - {INPUT_FILE}", fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(handles=handles, labels=labels, loc='upper right')

    # Text for f0 note name
    text_xform = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
    f0_text = ax.text(
        0, 0.98, "", transform=text_xform,
        ha="left", va="top",
        fontsize=12, color="blue", weight="bold",
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="blue", pad=2),
        clip_on=False, zorder=10
    )
    f0_text.set_visible(False)

    # Text annotations for spectral peaks
    text_annotations = []

    print("Starting animation processing...")
    writer = PillowWriter(fps=FPS)
    with writer.saving(fig, OUTPUT_GIF, dpi=120):
        for frame_number in range(FRAME_COUNT):
            # Current time and spectrum column
            current_time = frame_number * HOP / sr
            spec_col = S_b[:, frame_number]
            line.set_data(xf_b, spec_col)

            # --- Detect simultaneous notes for tracking with onset awareness ---
            simultaneous_notes = detect_notes_with_onsets(spec_col, xf_b, current_time, onset_times, max_notes=5)
            
            # Update note tracker with enhanced method
            note_tracker.update_note_tracker_with_prediction(current_time, simultaneous_notes)

            # --- Monophonic f0 (pyin) overlay & harmonics ---
            f0_val = f0[frame_number] if frame_number < len(f0) else np.nan
            if f0_val is not None and not np.isnan(f0_val) and FREQ_MIN <= f0_val <= FREQ_MAX:
                f0_line.set_xdata([f0_val, f0_val])
                f0_line.set_visible(True)
                
                # Show harmonics
                for i, hline in enumerate(harm_lines):
                    harmonic_freq = (i + 2) * f0_val  # 2nd, 3rd, 4th, etc.
                    hline.set_xdata([harmonic_freq, harmonic_freq])
                    hline.set_visible(FREQ_MIN <= harmonic_freq <= FREQ_MAX)
                
                # f0 note label
                try:
                    midi = librosa.hz_to_midi(f0_val)
                    note_label = librosa.midi_to_note(midi, octave=True)
                    x_pos = float(np.clip(f0_val, *ax.get_xlim()))
                    f0_text.set_position((x_pos, 0.98))
                    f0_text.set_text(f"f0: {note_label}")
                    f0_text.set_visible(True)
                except:
                    f0_text.set_visible(False)
            else:
                f0_line.set_visible(False)
                for hline in harm_lines:
                    hline.set_visible(False)
                f0_text.set_visible(False)

            # --- Red labels: strongest spectral peaks ---
            for txt in text_annotations:
                txt.remove()
            text_annotations = []
            
            top_notes = top_note_labels_from_spectrum(spec_col, xf_b, top_k=TOP_NOTES)
            for freq, name, mag in top_notes:
                text_annotations.append(
                    ax.text(freq, mag + 0.02, name, color="red", fontsize=10, 
                           ha="center", va="bottom", weight="bold",
                           bbox=dict(facecolor="white", alpha=0.7, edgecolor="red", pad=1))
                )

            # --- Violet/Purple lines: tracked simultaneous notes ---
            # Clear previous multi-pitch annotations
            for t in multi_texts:
                t.remove()
            multi_texts = []

            # Get active notes from tracker
            active_notes = note_tracker.get_active_notes()

            # Ensure we have enough lines
            while len(multi_lines) < len(active_notes):
                multi_lines.append(ax.axvline(x=0, lw=2, ls="-", alpha=0.8, color="purple"))

            # Update lines and labels for tracked notes
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

            # Add frame info
            time_sec = frame_number * HOP / sr
            active_count = len(active_notes)
            completed_count = len(note_tracker.get_completed_notes())
            ax.text(0, 0, f"Time: {time_sec:.2f}s | Active: {active_count} | Completed: {completed_count}", 
                    transform=ax.transAxes, fontsize=10,
                    bbox=dict(facecolor="white", alpha=0.8))

            writer.grab_frame()
            
            if frame_number % 30 == 0:  # Progress indicator
                progress = (frame_number + 1) / FRAME_COUNT * 100
                print(f"Animation progress: {progress:.1f}% | Active notes: {active_count}")

    print(f"Animation complete! Saved as '{OUTPUT_GIF}'")

else:
    # -------------------- Fast processing without animation --------------------
    print("Processing audio without animation (fast mode)...")
    processing_start = time.time()
    
    for frame_number in range(FRAME_COUNT):
        # Current time and spectrum column
        current_time = frame_number * HOP / sr
        spec_col = S_b[:, frame_number]

        # Detect simultaneous notes for tracking with onset awareness
        simultaneous_notes = detect_notes_with_onsets(spec_col, xf_b, current_time, onset_times, max_notes=5)
        
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
    print(f"Audio processing completed in {processing_time:.2f} seconds")
    print(f"Processing speed: {FRAME_COUNT / processing_time:.1f} frames/second")

# Finalize note tracking
note_tracker.finalize(total_duration)

# Print note timing summary
note_tracker.print_note_summary()

# Export to MIDI
print(f"\nExporting detected notes to MIDI...")
midi_start = time.time()
note_tracker.export_to_midi(
    OUTPUT_MIDI,
    tempo_bpm=MIDI_TEMPO_BPM,
    velocity_min=MIDI_VELOCITY_MIN,
    velocity_max=MIDI_VELOCITY_MAX,
    program=MIDI_PROGRAM
)
note_tracker.export_to_midi(
    OUTPUT_MIDI,
    tempo_bpm=MIDI_TEMPO_BPM,
    velocity_min=MIDI_VELOCITY_MIN,
    velocity_max=MIDI_VELOCITY_MAX,
    program=73
)
midi_time = time.time() - midi_start
print(f"MIDI export completed in {midi_time:.2f} seconds")

total_time = time.time() - start_time
print(f"\nTotal processing time: {total_time:.2f} seconds")
