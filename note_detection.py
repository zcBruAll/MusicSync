import librosa
import numpy as np
from scipy.signal import find_peaks

from config import *
# -------------------- Polyphonic Note Detection Functions --------------------

def detect_notes_with_onsets(spectrum, frequencies, current_time, onset_times, max_notes=5):
    """
    Enhanced note detection that considers onset information for timing.
    """
    # Check if we're near an onset (within 100ms)
    near_onset = any(abs(current_time - onset_time) < 0.1 for onset_time in onset_times)
    
    # Adjust thresholds based on onset proximity
    if near_onset:
        adjusted_min_height = MIN_PEAK_HEIGHT * 0.7  # Lower threshold near onsets
        adjusted_threshold = DETECTION_THRESHOLD * 0.8
    else:
        adjusted_min_height = MIN_PEAK_HEIGHT
        adjusted_threshold = DETECTION_THRESHOLD
    
    peak_freqs, peak_mags = find_spectral_peaks(spectrum, frequencies, 
                                               min_height=adjusted_min_height)
    
    if len(peak_freqs) == 0:
        return []
    
    # Group peaks into fundamentals
    fundamentals = group_harmonics(peak_freqs, peak_mags)
    
    # Convert to notes and filter by frequency range
    notes = []
    for f0, energy, num_harmonics in fundamentals[:max_notes]:
        if FREQ_MIN <= f0 <= FREQ_MAX and energy >= adjusted_threshold:
            try:
                midi = librosa.hz_to_midi(f0)
                note_name = librosa.midi_to_note(midi, octave=True)
                # Boost score for notes with more harmonics and near onsets
                adjusted_energy = energy * (1 + 0.1 * (num_harmonics - 1))
                if near_onset:
                    adjusted_energy *= 1.2  # Boost confidence near onsets
                notes.append((f0, adjusted_energy, note_name, True))#num_harmonics < 5))
            except:
                continue
    
    return notes

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


