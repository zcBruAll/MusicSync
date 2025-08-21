import librosa
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib.animation import PillowWriter
import numpy as np

# Config
FPS = 30                       # Frames per second of the output animation
FFT_WINDOWS_SECONDS = 0.25     # Size of FFT window in seconds
FREQ_MIN = 10                  # Minimum frequency to display (Hz)
FREQ_MAX = 2000                # Maximum frequency to display (Hz)
TOP_NOTES = 5                  # Number of strongest notes to annotate

# Note names used to convert frequencies into musical notes
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", 
              "G", "G#", "A", "A#", "B"]

# Load audio (mono). Duration limited to 20 seconds for faster analysis.
y, sr = librosa.load("Sounds/Ecossaise_Piano.mp3", mono=True, duration=10)

# Frame step in samples - each frame is spaced this many samples apart.
FRAME_STEP = (sr / FPS)

# FFT window length in samples
FFT_WINDOW_SIZE = int(sr * FFT_WINDOWS_SECONDS)
# Total length of the audio in seconds
AUDIO_LENGTH = len(y) / sr

# Conversions between frequency <-> MIDI note number <-> note name
def freq_to_number(f): return 69 + 12*np.log2(f/440.0)          # 440Hz = A4
def number_to_freq(n): return 440 * 2.0**((n-69)/12.0)
def note_name(n): return NOTE_NAMES[n % 12] + str(int(n/12 - 1))

# Hanning window to reduce spectral leakage
window = 0.5 * (1 - np.cos(np.linspace(0, 2*np.pi, FFT_WINDOW_SIZE, False)))

# Frequencies corresponding to FFT bins (real FFT, only positive side kept)
xf = np.fft.rfftfreq(FFT_WINDOW_SIZE, 1/sr)

# Number of frames in the whole animation
FRAME_COUNT = int(AUDIO_LENGTH*FPS)
# Number of samples to move for each frame
FRAME_OFFSET = int(len(y)/FRAME_COUNT)

def extract_sample(audio, frame_number):
    """
    Get the slice of audio for a given frame number, applying zero-padding
    if necessary (at the end of the audio).
    """
    begin = frame_number * FRAME_OFFSET
    end = begin + FFT_WINDOW_SIZE

    if begin >= len(audio):
        return np.zeros(FFT_WINDOW_SIZE, dtype=float)   # beyond end of audio

    if end <= len(audio):
        return audio[begin:end]
    else:
        pad = end - len(audio)                          # pad with zeros
        return np.concatenate([audio[begin:], np.zeros(pad, dtype=float)])

def find_top_notes(fft, num, min_sep_hz=None, prominence=0.05):
    """
    Identify the most prominent spectral peaks (musical notes) in an FFT frame.
    - Selects up to `num` peaks that are strong, separated, and not duplicated.
    - min_sep_hz: minimum frequency separation between labeled peaks (Hz).
                  If None, defaults to ~3 FFT bins.
    - prominence: min (0..1) prominence relative to frame-local max.
    Returns: list of [frequency (Hz), note name, magnitude]
    """
    mag = np.asarray(fft)                 # already on your global scale (fft/mx)
    if mag.size < 3 or np.max(mag) < 1e-12:
        return []

    # Use a local-normalized copy for thresholding so 'prominence' is frame-robust
    mag_norm = mag / (mag.max() + 1e-12)

    # Frequency resolution and min separation in bins
    df = sr / FFT_WINDOW_SIZE
    if min_sep_hz is None:
        min_sep_bins = 3  # ~Hann mainlobe neighborhood
    else:
        min_sep_bins = max(1, int(round(min_sep_hz / df)))

    # 1) Find local maxima (strictly greater than left, >= right)
    peaks = np.where((mag_norm[1:-1] > mag_norm[:-2]) & (mag_norm[1:-1] >= mag_norm[2:]))[0] + 1
    if peaks.size == 0:
        return []

    # 2) Simple prominence: peak minus max of neighbors within a small window
    w = max(1, min_sep_bins // 2)
    neigh = []
    for k in range(1, w + 1):
        left  = mag_norm[np.clip(peaks - k, 0, mag_norm.size - 1)]
        right = mag_norm[np.clip(peaks + k, 0, mag_norm.size - 1)]
        neigh.append(left)
        neigh.append(right)
    neighbor_max = np.maximum.reduce(neigh) if neigh else np.zeros_like(peaks, dtype=float)
    prom = mag_norm[peaks] - neighbor_max

    # Keep only sufficiently prominent peaks
    good = peaks[prom >= prominence]
    if good.size == 0:
        return []

    # 3) Sort by strength (use normalized mag for ranking)
    order = np.argsort(mag_norm[good])[::-1]
    good = good[order]

    # 4) Non-maximum suppression by frequency separation + unique note names
    kept_bins = []
    kept = []
    kept_names = set()

    for b in good:
        # enforce min bin separation from already kept peaks
        if any(abs(b - kb) < min_sep_bins for kb in kept_bins):
            continue

        f = xf[b]
        if not (FREQ_MIN <= f <= FREQ_MAX):
            continue

        n = int(round(freq_to_number(f)))
        name = note_name(n)

        # optional: avoid duplicate note labels
        if name in kept_names:
            continue

        kept.append([f, name, mag[b]])  # mag on your plot's scale
        kept_bins.append(b)
        kept_names.add(name)
        if len(kept) == num:
            break

    return kept


# --- PASS 1: find global max amplitude for normalization ---
mx = 0
for frame_number in range(FRAME_COUNT):
    sample = extract_sample(y, frame_number)
    fft = np.fft.rfft(sample * window)        # FFT on windowed sample
    fft = np.abs(fft).real                    # Magnitude spectrum
    mx = max(np.max(fft), mx)                 # Keep global max

print(f"Max amplitude: {mx}")

# --- Fundamental frequency detection using librosa’s pYIN algorithm ---
# Estimates the pitch contour (f0) across frames.
f0, vflag, vprob = librosa.pyin(
    y=y,
    sr=sr,
    fmin=librosa.note_to_hz("C2"),   # min pitch to consider
    fmax=librosa.note_to_hz("C7"),   # max pitch to consider
    frame_length=FFT_WINDOW_SIZE,
    hop_length=FRAME_OFFSET,
    center=False
)

# --- SETUP MATPLOTLIB ANIMATION ---
fig, ax = plt.subplots(figsize=(12,6), dpi=120)
line, = ax.plot([], [], lw=2)                           # FFT spectrum line
f0_line = ax.axvline(x=0, lw=2, ls="--", label="f0")    # vertical line at f0
harm_lines = [ax.axvline(x=0, lw=1, ls=":", alpha=0.6) for _ in range(5)]
                                                        # harmonic lines

# Prepare floating text annotation for detected f0 note
y_top = ax.get_ylim()[1]
text_xform = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
f0_text = ax.text(
    0, 0.98, "", transform=text_xform,
    ha="left", va="top",
    fontsize=12, color="tab:blue",
    bbox=dict(facecolor="white", alpha=0.6, edgecolor="none"),
    clip_on=False, zorder=10
)
f0_text.set_visible(False)

# Configure plot axes
ax.set_xlim(FREQ_MIN, FREQ_MAX)
ax.set_ylim(0, 1)
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Magnitude")
ax.set_title("Real-time Frequency Spectrum")
ax.legend()

text_annotations = []  # for red note labels on peaks

# --- RENDER TO GIF WITH PILLOWWRITER ---
writer = PillowWriter(fps=FPS)
with writer.saving(fig, "Output/spectrum.gif", dpi=120):
    for frame_number in range(FRAME_COUNT):
        # Extract sample and compute FFT (normalized by mx)
        sample = extract_sample(y, frame_number)
        fft = np.fft.rfft(sample * window)
        fft = np.abs(fft) / mx 
        
        # Update FFT curve on the plot
        line.set_data(xf, fft)
        
        # Show f0 (fundamental frequency) line and harmonics
        f0_val = f0[frame_number] if frame_number < len(f0) else np.nan
        if f0_val is not None and not np.isnan(f0_val):
            f0_line.set_xdata([f0_val, f0_val])
            f0_line.set_visible(True)
            # Update harmonic lines (2nd, 3rd, ...)
            h = 2
            for hline in harm_lines:
                x = h * f0_val
                hline.set_xdata([x, x])
                hline.set_visible(FREQ_MIN <= x <= FREQ_MAX)
                h += 1
                
            # Update floating text with note name of f0
            note_name_str = note_name(int(round(freq_to_number(f0_val))))
            if note_name_str:
                label = f"{note_name_str}"
                x_min, x_max = ax.get_xlim()
                x_pos = float(np.clip(f0_val, x_min, x_max))
                f0_text.set_ha("right" if x_pos > (x_min + x_max) / 2 else "left")
                f0_text.set_position((x_pos, 0.98))
                f0_text.set_text(label)
                f0_text.set_visible(True)
            else:
                f0_text.set_visible(False)
        else:
            # Hide f0 visuals if none detected
            f0_line.set_visible(False)
            for hline in harm_lines:
                hline.set_visible(False)
            f0_text.set_visible(False)
        
        # Remove previous red labels
        for txt in text_annotations: 
            txt.remove()
        text_annotations = []
        
        # Mark strongest spectral peaks (red labels)
        s = find_top_notes(fft, TOP_NOTES, min_sep_hz=3*(sr/FFT_WINDOW_SIZE), prominence=0.05)
        for note in s:
            txt = ax.text(note[0], note[2], note[1], color="red", fontsize=12)
            text_annotations.append(txt)
        
        # Grab frame for the GIF
        writer.grab_frame()