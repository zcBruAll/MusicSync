import librosa
import librosa.display as ldisplay
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib.animation import PillowWriter
from matplotlib.lines import Line2D
from scipy.signal import find_peaks
from collections import defaultdict

# -------------------- Config --------------------
INPUT_FILE = "Sounds/Ecossaise_Piano.mp3" # File name and path of the input file
OUTPUT_GIF = "Output/analysis.gif"      # File name and path of the outputed gif

FPS = 30                                # frames per second of the animation
FFT_WINDOWS_SECONDS = 0.25              # STFT window size in seconds
FREQ_MIN = 10                           # Hz
FREQ_MAX = 2000                         # Hz
TOP_NOTES = 5                           # number of strongest notes to annotate

# Polyphonic detection parameters
MIN_PEAK_HEIGHT = 0.025                 # minimum peak height for consideration
MIN_PEAK_DISTANCE = 1                   # minimum distance between peaks (in bins)
MAX_HARMONICS = 8                       # maximum number of harmonics to consider
HARMONIC_TOLERANCE = 0.05               # tolerance for harmonic matching (as fraction)

# -------------------- Load & preprocess --------------------
y, sr = librosa.load(INPUT_FILE, mono=True, duration=10)
# harmonic component only (librosa HPSS)
y_h = librosa.effects.harmonic(y)

# STFT params derived from config
N_FFT = int(sr * FFT_WINDOWS_SECONDS)
HOP = max(1, int(sr / FPS))

# Complex STFT (librosa uses a Hann window by default)
D = librosa.stft(y_h, n_fft=N_FFT, hop_length=HOP, win_length=N_FFT,
                 window="hann", center=False)
S = np.abs(D)                              # magnitude
mx = np.max(S) if np.max(S) > 0 else 1.0   # global max for normalization
S_norm = S / mx

# Frequency axis from librosa helper
xf = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)

# Limit to desired frequency band once, and remember slice
band = (xf >= FREQ_MIN) & (xf <= FREQ_MAX)
xf_b = xf[band]
S_b = S_norm[band, :]

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

# -------------------- Polyphonic Note Detection Functions --------------------

def find_spectral_peaks(spectrum, frequencies, min_height=MIN_PEAK_HEIGHT, min_distance=MIN_PEAK_DISTANCE):
    """Find significant peaks in the spectrum."""
    peaks, properties = find_peaks(spectrum, 
                                 height=min_height, 
                                 distance=min_distance,
                                 prominence=0.02)
    
    if len(peaks) == 0:
        return [], []
    
    peak_freqs = frequencies[peaks]
    peak_mags = spectrum[peaks]
    
    # Sort by magnitude (descending)
    sort_idx = np.argsort(peak_mags)[::-1]
    return peak_freqs[sort_idx], peak_mags[sort_idx]

def is_harmonic(f1, f2, tolerance=HARMONIC_TOLERANCE):
    """Check if f2 is a harmonic of f1 within tolerance."""
    if f1 <= 0 or f2 <= 0:
        return False
    
    ratio = f2 / f1
    # Check if ratio is close to an integer (harmonic relationship)
    closest_int = round(ratio)
    if closest_int < 2:  # We only consider harmonics >= 2nd
        return False
    
    return abs(ratio - closest_int) / closest_int < tolerance

def group_harmonics(peak_freqs, peak_mags, max_harmonics=MAX_HARMONICS):
    """Group peaks into fundamental frequencies and their harmonics."""
    if len(peak_freqs) == 0:
        return []
    
    fundamentals = []
    used_peaks = set()
    
    # Sort peaks by magnitude (strongest first)
    peak_order = np.argsort(peak_mags)[::-1]
    
    for i in peak_order:
        if i in used_peaks:
            continue
            
        f0_candidate = peak_freqs[i]
        f0_magnitude = peak_mags[i]
        
        # Find all harmonics of this candidate
        harmonics = [(f0_candidate, f0_magnitude)]
        harmonic_indices = {i}
        
        # Look for harmonics
        for j in peak_order:
            if j in used_peaks or j == i:
                continue
                
            if is_harmonic(f0_candidate, peak_freqs[j]):
                harmonics.append((peak_freqs[j], peak_mags[j]))
                harmonic_indices.add(j)
                
                if len(harmonics) >= max_harmonics:
                    break
        
        # Only consider as fundamental if it has at least one harmonic or is strong enough
        if len(harmonics) > 2 or f0_magnitude > 0.3:
            # Calculate total energy for this fundamental (sum of harmonic magnitudes)
            total_energy = sum(mag for freq, mag in harmonics)
            fundamentals.append((f0_candidate, total_energy, len(harmonics)))
            used_peaks.update(harmonic_indices)
    
    # Sort by total energy (strongest first)
    fundamentals.sort(key=lambda x: x[1], reverse=True)
    return fundamentals

def detect_simultaneous_notes(spectrum, frequencies, max_notes=5):
    """
    Detect simultaneous notes using spectral peak analysis and harmonic grouping.
    Returns list of (frequency_hz, strength, note_name).
    """
    peak_freqs, peak_mags = find_spectral_peaks(spectrum, frequencies)
    
    if len(peak_freqs) == 0:
        return []
    
    # Group peaks into fundamentals
    fundamentals = group_harmonics(peak_freqs, peak_mags)
    
    # Convert to notes and filter by frequency range
    notes = []
    for f0, energy, num_harmonics in fundamentals[:max_notes]:
        if FREQ_MIN <= f0 <= FREQ_MAX:
            try:
                midi = librosa.hz_to_midi(f0)
                note_name = librosa.midi_to_note(midi, octave=True)
                # Boost score for notes with more harmonics
                adjusted_energy = energy * (1 + 0.1 * (num_harmonics - 1))
                notes.append((f0, adjusted_energy, note_name))
            except:
                continue
    
    return notes

def top_note_labels_from_spectrum(spectrum, frequencies, top_k=TOP_NOTES):
    """
    Return up to top_k strongest spectral peaks as note labels.
    """
    peak_freqs, peak_mags = find_spectral_peaks(spectrum, frequencies)
    
    if len(peak_freqs) == 0:
        return []
    
    labels = []
    seen_notes = set()
    
    for freq, mag in zip(peak_freqs[:top_k*2], peak_mags[:top_k*2]):
        if freq < FREQ_MIN or freq > FREQ_MAX:
            continue
            
        try:
            midi = librosa.hz_to_midi(freq)
            note_name = librosa.midi_to_note(midi, octave=True)
            
            # Avoid duplicate note names
            if note_name in seen_notes:
                continue
                
            labels.append((freq, note_name, mag))
            seen_notes.add(note_name)
            
            if len(labels) >= top_k:
                break
        except:
            continue
    
    return labels

# -------------------- Matplotlib animation --------------------
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
ax.set_title(f"Polyphonic Music Analysis - {INPUT_FILE}", fontsize=14)
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

# Number of animation frames = number of STFT columns
FRAME_COUNT = S_b.shape[1]
print(f"Animation info: {FRAME_COUNT} frames, FPS={FPS}, HOP={HOP}, N_FFT={N_FFT}")
print(f"Frequency range: {FREQ_MIN}-{FREQ_MAX} Hz")

writer = PillowWriter(fps=FPS)
with writer.saving(fig, OUTPUT_GIF, dpi=120):
    for frame_number in range(FRAME_COUNT):
        # Current spectrum column
        spec_col = S_b[:, frame_number]
        line.set_data(xf_b, spec_col)

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

        # --- Violet/Purple lines: simultaneous fundamental frequencies ---
        # Clear previous multi-pitch annotations
        for t in multi_texts:
            t.remove()
        multi_texts = []

        # Detect simultaneous notes
        simultaneous_notes = detect_simultaneous_notes(spec_col, xf_b, max_notes=5)

        # Ensure we have enough lines
        while len(multi_lines) < len(simultaneous_notes):
            multi_lines.append(ax.axvline(x=0, lw=2, ls="-", alpha=0.8, color="purple"))

        # Update lines and labels for detected notes
        for i, (freq, strength, note_name) in enumerate(simultaneous_notes):
            multi_lines[i].set_xdata([freq, freq])
            multi_lines[i].set_visible(True)
            
            # Add note label
            multi_texts.append(ax.text(
                freq, 0.92 - i * 0.04, f"{note_name}", 
                transform=text_xform,
                ha="center", va="top", fontsize=11, 
                color="purple", weight="bold",
                bbox=dict(facecolor="white", alpha=0.8, edgecolor="purple", pad=1)
            ))

        # Hide unused lines
        for j in range(len(simultaneous_notes), len(multi_lines)):
            multi_lines[j].set_visible(False)

        # Add frame info
        time_sec = frame_number * HOP / sr
        ax.text(0, 0, f"Time: {time_sec:.2f}s", 
                transform=ax.transAxes, fontsize=10,
                bbox=dict(facecolor="white", alpha=0.8))

        writer.grab_frame()
        
        if frame_number % 15 == 0:  # Progress indicator
            print(f"Processed frame {frame_number}/{FRAME_COUNT}")

print(f"Animation complete! Saved as '{OUTPUT_GIF}'")