import librosa
import librosa.display as ldisplay
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from matplotlib.animation import PillowWriter
from matplotlib.lines import Line2D
from scipy.signal import find_peaks
from collections import defaultdict
import mido
from mido import MidiFile, MidiTrack, Message

# -------------------- Config --------------------
INPUT_FILE = "Sounds/Ecossaise_Piano.mp3" # File name and path of the input file
OUTPUT_GIF = "Output/analysis.gif"      # File name and path of the outputed gif
OUTPUT_MIDI = "Output/detected_notes.mid"  # File name and path of the output MIDI file

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

# Note timing and smoothing parameters
SMOOTHING_TIME = 0.25                   # seconds - max gap to bridge between same notes
MIN_NOTE_DURATION = 0.1                 # seconds - minimum duration for a note to be considered valid
DETECTION_THRESHOLD = 0.3               # minimum strength for note detection

# MIDI export parameters
MIDI_TEMPO_BPM = 120                    # BPM for MIDI file
MIDI_VELOCITY_MIN = 64                  # minimum MIDI velocity
MIDI_VELOCITY_MAX = 127                 # maximum MIDI velocity
MIDI_PROGRAM = 0                        # MIDI program (0 = Acoustic Grand Piano)

# -------------------- Load & preprocess --------------------
y, sr = librosa.load(INPUT_FILE, mono=True)
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

# -------------------- Note Timing and Smoothing Classes --------------------

class NoteEvent:
    def __init__(self, note_name, frequency, start_time, strength):
        self.note_name = note_name
        self.frequency = frequency
        self.start_time = start_time
        self.end_time = start_time
        self.max_strength = strength
        self.last_seen_time = start_time
        self.is_active = True
    
    def update(self, time, strength):
        """Update note with new detection"""
        self.end_time = time
        self.last_seen_time = time
        self.max_strength = max(self.max_strength, strength)
    
    def get_duration(self):
        """Get note duration in seconds"""
        return self.end_time - self.start_time
    
    def __str__(self):
        return f"{self.note_name}: {self.start_time:.2f}s - {self.end_time:.2f}s ({self.get_duration():.2f}s)"

class NoteTracker:
    def __init__(self, smoothing_time=0.25, min_duration=0.1, detection_threshold=0.3):
        self.smoothing_time = smoothing_time
        self.min_duration = min_duration
        self.detection_threshold = detection_threshold
        self.active_notes = {}  # note_name -> NoteEvent
        self.completed_notes = []  # List of completed NoteEvent objects
        self.note_tolerance_hz = 5  # Hz tolerance for considering notes the same
    
    def _get_note_key(self, note_name, frequency):
        """Create a key for tracking notes, allowing for slight frequency variations"""
        # Round frequency to nearest 5 Hz to group similar frequencies
        rounded_freq = round(frequency / self.note_tolerance_hz) * self.note_tolerance_hz
        return f"{note_name}_{rounded_freq:.0f}"
    
    def update(self, current_time, detected_notes):
        """
        Update tracker with new frame data
        detected_notes: list of (frequency, strength, note_name) tuples
        """
        # Convert to dict for easier lookup
        current_detections = {}
        for freq, strength, note_name in detected_notes:
            if strength >= self.detection_threshold:
                key = self._get_note_key(note_name, freq)
                current_detections[key] = (note_name, freq, strength)
        
        # Update existing notes or mark for potential closure
        notes_to_remove = []
        for key, note_event in self.active_notes.items():
            if key in current_detections:
                # Note is still being detected
                note_name, freq, strength = current_detections[key]
                note_event.update(current_time, strength)
            else:
                # Note not detected this frame
                gap_duration = current_time - note_event.last_seen_time
                if gap_duration > self.smoothing_time:
                    # Gap is too long, close this note
                    note_event.is_active = False
                    if note_event.get_duration() >= self.min_duration:
                        self.completed_notes.append(note_event)
                    notes_to_remove.append(key)
        
        # Remove notes that have ended
        for key in notes_to_remove:
            del self.active_notes[key]
        
        # Add new notes
        for key, (note_name, freq, strength) in current_detections.items():
            if key not in self.active_notes:
                self.active_notes[key] = NoteEvent(note_name, freq, current_time, strength)
    
    def finalize(self, final_time):
        """Finalize all remaining active notes"""
        for note_event in self.active_notes.values():
            note_event.end_time = final_time
            note_event.is_active = False
            if note_event.get_duration() >= self.min_duration:
                self.completed_notes.append(note_event)
        self.active_notes.clear()
    
    def get_active_notes(self):
        """Get currently active notes"""
        return list(self.active_notes.values())
    
    def get_completed_notes(self):
        """Get all completed notes"""
        return self.completed_notes
    
    def export_to_midi(self, output_file, tempo_bpm=120, velocity_min=64, velocity_max=127, program=0):
        """
        Export detected notes to a MIDI file.
        
        Args:
            output_file: Path to output MIDI file
            tempo_bpm: Tempo in beats per minute
            velocity_min: Minimum MIDI velocity (for weakest notes)
            velocity_max: Maximum MIDI velocity (for strongest notes)
            program: MIDI program number (0 = Acoustic Grand Piano)
        """
        # Create MIDI file and track
        mid = MidiFile()
        track = MidiTrack()
        mid.tracks.append(track)
        
        # Set tempo (microseconds per beat)
        tempo = mido.bpm2tempo(tempo_bpm)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
        
        # Set program (instrument)
        track.append(mido.Message('program_change', program=program, time=0))
        
        # Prepare all notes for MIDI export
        all_notes = self.completed_notes.copy()
        
        # Add any remaining active notes (finalized)
        for note_event in self.active_notes.values():
            if not note_event.is_active and note_event.get_duration() >= self.min_duration:
                all_notes.append(note_event)
        
        if not all_notes:
            print("No notes to export to MIDI.")
            return
        
        # Sort notes by start time
        all_notes.sort(key=lambda x: x.start_time)
        
        # Calculate velocity range
        if len(all_notes) > 1:
            strengths = [note.max_strength for note in all_notes]
            min_strength = min(strengths)
            max_strength = max(strengths)
            strength_range = max_strength - min_strength
        else:
            min_strength = max_strength = all_notes[0].max_strength
            strength_range = 1.0
        
        # Convert notes to MIDI events
        midi_events = []  # List of (time, event_type, midi_note, velocity)
        
        for note_event in all_notes:
            try:
                # Convert frequency to MIDI note number
                midi_note = int(round(librosa.hz_to_midi(note_event.frequency)))
                
                # Clamp to valid MIDI range
                midi_note = max(0, min(127, midi_note))
                
                # Calculate velocity based on note strength
                if strength_range > 0:
                    norm_strength = (note_event.max_strength - min_strength) / strength_range
                else:
                    norm_strength = 0.5
                
                velocity = int(velocity_min + norm_strength * (velocity_max - velocity_min))
                velocity = max(1, min(127, velocity))  # Ensure valid MIDI velocity
                
                # Add note on and note off events
                midi_events.append((note_event.start_time, 'note_on', midi_note, velocity))
                midi_events.append((note_event.end_time, 'note_off', midi_note, velocity))
                
            except Exception as e:
                print(f"Warning: Could not convert note {note_event.note_name} at {note_event.frequency:.1f} Hz to MIDI: {e}")
                continue
        
        if not midi_events:
            print("No valid MIDI events to export.")
            return
        
        # Sort events by time
        midi_events.sort(key=lambda x: x[0])
        
        # Convert to MIDI messages with proper timing
        current_time = 0.0
        ticks_per_second = mid.ticks_per_beat * (tempo_bpm / 60.0)
        
        for event_time, event_type, midi_note, velocity in midi_events:
            # Calculate delta time in ticks
            delta_time_sec = event_time - current_time
            delta_ticks = int(round(delta_time_sec * ticks_per_second))
            delta_ticks = max(0, delta_ticks)  # Ensure non-negative
            
            if event_type == 'note_on':
                track.append(mido.Message('note_on', note=midi_note, velocity=velocity, time=delta_ticks))
            elif event_type == 'note_off':
                track.append(mido.Message('note_off', note=midi_note, velocity=velocity, time=delta_ticks))
            
            current_time = event_time
        
        # Save MIDI file
        try:
            mid.save(output_file)
            print(f"\nMIDI file exported successfully: {output_file}")
            print(f"  - {len(all_notes)} notes exported")
            print(f"  - Tempo: {tempo_bpm} BPM")
            print(f"  - Program: {program} (Piano)")
            print(f"  - Velocity range: {velocity_min}-{velocity_max}")
            print(f"  - Duration: {max(note.end_time for note in all_notes):.2f} seconds")
        except Exception as e:
            print(f"Error saving MIDI file: {e}")
    
    def print_note_summary(self):
        """Print summary of all detected notes"""
        print("\n" + "="*60)
        print("NOTE TIMING SUMMARY")
        print("="*60)
        
        all_notes = self.completed_notes + [n for n in self.active_notes.values() if not n.is_active]
        all_notes.sort(key=lambda x: x.start_time)
        
        if not all_notes:
            print("No notes detected with sufficient duration.")
            return
        
        print(f"Total notes detected: {len(all_notes)}")
        print(f"Time range: {all_notes[0].start_time:.2f}s - {all_notes[-1].end_time:.2f}s")
        print("\nDetailed note list:")
        print("-" * 60)
        
        for i, note in enumerate(all_notes, 1):
            print(f"{i:2d}. {note}")
        
        # Statistics by note name
        note_stats = defaultdict(list)
        for note in all_notes:
            note_stats[note.note_name].append(note.get_duration())
        
        print("\nNote statistics:")
        print("-" * 30)
        for note_name, durations in sorted(note_stats.items()):
            avg_duration = np.mean(durations)
            total_duration = sum(durations)
            count = len(durations)
            print(f"{note_name:>6s}: {count:2d} occurrences, avg {avg_duration:.2f}s, total {total_duration:.2f}s")

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

# -------------------- Initialize Note Tracker --------------------
note_tracker = NoteTracker(
    smoothing_time=SMOOTHING_TIME,
    min_duration=MIN_NOTE_DURATION,
    detection_threshold=DETECTION_THRESHOLD
)

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

# Number of animation frames = number of STFT columns
FRAME_COUNT = S_b.shape[1]
total_duration = FRAME_COUNT * HOP / sr

print(f"Animation info: {FRAME_COUNT} frames, FPS={FPS}, HOP={HOP}, N_FFT={N_FFT}")
print(f"Frequency range: {FREQ_MIN}-{FREQ_MAX} Hz")
print(f"Total audio duration: {total_duration:.2f} seconds")
print(f"Smoothing settings: {SMOOTHING_TIME}s gap tolerance, {MIN_NOTE_DURATION}s min duration")

writer = PillowWriter(fps=FPS)
with writer.saving(fig, OUTPUT_GIF, dpi=120):
    for frame_number in range(FRAME_COUNT):
        # Current time and spectrum column
        current_time = frame_number * HOP / sr
        spec_col = S_b[:, frame_number]
        line.set_data(xf_b, spec_col)

        # --- Detect simultaneous notes for tracking ---
        simultaneous_notes = detect_simultaneous_notes(spec_col, xf_b, max_notes=5)
        
        # Update note tracker
        note_tracker.update(current_time, simultaneous_notes)

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
        
        if frame_number % 15 == 0:  # Progress indicator
            print(f"Processed frame {frame_number}/{FRAME_COUNT} | Active notes: {active_count}")

# Finalize note tracking
note_tracker.finalize(total_duration)

print(f"Animation complete! Saved as '{OUTPUT_GIF}'")

# Print note timing summary
note_tracker.print_note_summary()

# Export to MIDI
print(f"\nExporting detected notes to MIDI...")
note_tracker.export_to_midi(
    OUTPUT_MIDI,
    tempo_bpm=MIDI_TEMPO_BPM,
    velocity_min=MIDI_VELOCITY_MIN,
    velocity_max=MIDI_VELOCITY_MAX,
    program=MIDI_PROGRAM
)