import librosa
import numpy as np
from scipy.signal import find_peaks
import math

from config import *

# -------------------- Enhanced CQT-Based Polyphonic Note Detection --------------------

def detect_notes_with_cqt_onsets(cqt_spectrum, cqt_frequencies, current_time, onset_times, max_notes=5):
    """
    Enhanced note detection using CQT spectrum and onset information.
    
    CQT advantages:
    - Logarithmic frequency spacing matches musical scales
    - Better frequency resolution for bass notes
    - Harmonic relationships are more regular in CQT space
    
    Args:
        cqt_spectrum: CQT magnitude values for current time frame
        cqt_frequencies: Frequency values corresponding to CQT bins
        current_time: Current time in seconds
        onset_times: Array of detected onset times
        max_notes: Maximum number of simultaneous notes to detect
        
    Returns:
        List of (frequency_hz, strength, note_name, is_piano) tuples
    """
    # Check if we're near an onset (within 100ms) - this helps with timing accuracy
    near_onset = any(abs(current_time - onset_time) < 0.1 for onset_time in onset_times)
    
    # Adapt detection sensitivity based on onset proximity
    # Near onsets, we expect new notes to start, so we lower thresholds
    if near_onset:
        adjusted_min_height = MIN_PEAK_HEIGHT * 0.6  # More sensitive near onsets
        adjusted_threshold = DETECTION_THRESHOLD * 0.7
        onset_boost = 1.3  # Boost confidence scores near onsets
    else:
        adjusted_min_height = MIN_PEAK_HEIGHT
        adjusted_threshold = DETECTION_THRESHOLD
        onset_boost = 1.0
    
    # Find spectral peaks in CQT domain - this is more reliable than STFT for musical content
    peak_freqs, peak_mags, peak_indices = find_cqt_peaks(
        cqt_spectrum, cqt_frequencies, 
        min_height=adjusted_min_height
    )
    
    if len(peak_freqs) == 0:
        return []
    
    # Group peaks into fundamentals using CQT-optimized harmonic detection
    # CQT makes harmonic detection much more reliable because harmonics appear
    # at regular intervals in the logarithmic frequency space
    fundamentals = group_cqt_harmonics(peak_freqs, peak_mags, cqt_frequencies)
    
    # Convert to musical notes with enhanced scoring
    notes = []
    for f0, energy, num_harmonics, harmonic_strength in fundamentals[:max_notes]:
        if FREQ_MIN <= f0 <= FREQ_MAX and energy >= adjusted_threshold:
            try:
                # Convert frequency to musical note
                midi = librosa.hz_to_midi(f0)
                note_name = librosa.midi_to_note(midi, octave=True)
                
                # Enhanced confidence scoring considers:
                # 1. Base energy from peak detection
                # 2. Number of supporting harmonics (more = better)
                # 3. Strength of harmonic pattern
                # 4. Onset proximity boost
                confidence = energy * (1 + 0.15 * (num_harmonics - 1)) * harmonic_strength * onset_boost
                
                # Simple instrument classification placeholder
                # This could be enhanced with spectral characteristics analysis
                # is_piano = classify_instrument_simple(f0, confidence, num_harmonics)
                is_piano = True
                
                notes.append((f0, confidence, note_name, is_piano))
            except Exception as e:
                # Skip notes that can't be converted (e.g., too high/low frequency)
                continue
    
    return notes

def find_cqt_peaks(cqt_spectrum, cqt_frequencies, min_height=MIN_PEAK_HEIGHT):
    """
    Find significant peaks in CQT spectrum with musical-aware parameters.
    
    CQT peak detection is different from STFT because:
    - CQT bins are logarithmically spaced
    - Musical notes have natural relationships in log-frequency space
    - We can use musical knowledge to set better distance parameters
    
    Returns:
        peak_freqs: Frequencies of detected peaks
        peak_mags: Magnitudes of detected peaks  
        peak_indices: Indices in CQT spectrum
    """
    # Calculate minimum distance in bins for peak separation
    # We want to separate peaks by at least 1 semitone to avoid double-detection
    # In CQT with bins_per_octave=36, each semitone = 3 bins
    min_distance_bins = max(2, int(36 / 12))  # About 1 semitone
    
    # Find peaks with adaptive parameters
    peaks, properties = find_peaks(
        cqt_spectrum, 
        height=min_height, 
        distance=min_distance_bins,
        prominence=0.01,  # Relative prominence to distinguish real peaks from noise
        width=1           # Minimum width in bins
    )
    
    if len(peaks) == 0:
        return [], [], []
    
    peak_freqs = cqt_frequencies[peaks]
    peak_mags = cqt_spectrum[peaks]
    
    # Sort by magnitude (strongest first) for better fundamental detection
    sort_idx = np.argsort(peak_mags)[::-1]
    return peak_freqs[sort_idx], peak_mags[sort_idx], peaks[sort_idx]

def group_cqt_harmonics(peak_freqs, peak_mags, cqt_frequencies, max_harmonics=MAX_HARMONICS):
    """
    Group CQT peaks into fundamental frequencies and their harmonics.
    
    This is where CQT really shines! In CQT space:
    - Harmonics of a fundamental appear at regular intervals
    - The logarithmic spacing makes harmonic ratios easier to detect
    - We can use musical theory more directly
    
    Args:
        peak_freqs: Array of peak frequencies
        peak_mags: Array of peak magnitudes
        cqt_frequencies: Full CQT frequency array
        max_harmonics: Maximum harmonics to consider
        
    Returns:
        List of (fundamental_freq, total_energy, num_harmonics, harmonic_strength) tuples
    """
    if len(peak_freqs) == 0:
        return []
    
    fundamentals = []
    used_peaks = set()
    
    # Sort peaks by magnitude (strongest first) - strongest peaks are likely fundamentals
    peak_order = np.argsort(peak_mags)[::-1]
    
    for i in peak_order:
        if i in used_peaks:
            continue
            
        f0_candidate = peak_freqs[i]
        f0_magnitude = peak_mags[i]
        
        # Find harmonics of this candidate using CQT-optimized detection
        harmonics = [(f0_candidate, f0_magnitude, 1)]  # (freq, mag, harmonic_number)
        harmonic_indices = {i}
        
        # Look for harmonics: 2f0, 3f0, 4f0, etc.
        for harmonic_num in range(2, max_harmonics + 1):
            expected_freq = f0_candidate * harmonic_num
            
            # Find the closest peak to expected harmonic frequency
            closest_peak_idx = None
            min_distance = float('inf')
            
            for j in peak_order:
                if j in used_peaks or j == i:
                    continue
                
                # Check if this peak could be the harmonic we're looking for
                freq_ratio = peak_freqs[j] / f0_candidate
                expected_ratio = harmonic_num
                
                # In CQT space, we can be more precise about harmonic relationships
                relative_error = abs(freq_ratio - expected_ratio) / expected_ratio
                
                if relative_error < HARMONIC_TOLERANCE:
                    distance = abs(peak_freqs[j] - expected_freq)
                    if distance < min_distance:
                        min_distance = distance
                        closest_peak_idx = j
            
            # If we found a good harmonic match, add it
            if closest_peak_idx is not None:
                harmonics.append((peak_freqs[closest_peak_idx], peak_mags[closest_peak_idx], harmonic_num))
                harmonic_indices.add(closest_peak_idx)
        
        # Evaluate the quality of this fundamental candidate
        num_harmonics = len(harmonics)
        
        # Calculate harmonic strength - how well do the harmonics follow expected pattern?
        harmonic_strength = calculate_harmonic_strength(harmonics)
        
        # Only consider as fundamental if:
        # 1. It has supporting harmonics OR is very strong
        # 2. The harmonic pattern is reasonably strong
        if (num_harmonics >= 2 or f0_magnitude > 0.4) and harmonic_strength > 0.5:
            # Calculate total energy (sum of harmonic magnitudes with decay)
            total_energy = 0
            for freq, mag, harm_num in harmonics:
                # Higher harmonics contribute less to total energy (natural decay)
                decay_factor = HARMONIC_WEIGHT_DECAY ** (harm_num - 1)
                total_energy += mag * decay_factor
            
            fundamentals.append((f0_candidate, total_energy, num_harmonics, harmonic_strength))
            used_peaks.update(harmonic_indices)
    
    # Sort fundamentals by total energy (strongest first)
    fundamentals.sort(key=lambda x: x[1], reverse=True)
    return fundamentals

def calculate_harmonic_strength(harmonics):
    """
    Calculate how well the harmonics follow the expected amplitude decay pattern.
    
    In natural instruments, harmonics typically decay in amplitude as frequency increases.
    This function measures how well the detected harmonics follow this pattern.
    
    Returns:
        Strength score between 0 and 1 (1 = perfect harmonic decay pattern)
    """
    if len(harmonics) < 2:
        return 0.5  # Neutral score for single peaks
    
    # Sort harmonics by harmonic number
    harmonics.sort(key=lambda x: x[2])  # Sort by harmonic number
    
    # Calculate expected vs actual amplitude ratios
    strength_scores = []
    
    for i in range(1, len(harmonics)):
        prev_freq, prev_mag, prev_num = harmonics[i-1]
        curr_freq, curr_mag, curr_num = harmonics[i]
        
        # Expected decay based on harmonic number
        expected_ratio = (prev_num / curr_num) ** 0.8  # Slightly less than 1/n decay
        actual_ratio = curr_mag / prev_mag if prev_mag > 0 else 0
        
        # Score how close actual ratio is to expected
        if expected_ratio > 0:
            ratio_error = abs(actual_ratio - expected_ratio) / expected_ratio
            strength_score = max(0, 1 - ratio_error)
            strength_scores.append(strength_score)
    
    return np.mean(strength_scores) if strength_scores else 0.5

def classify_instrument_simple(frequency, confidence, num_harmonics):
    """
    Simple instrument classification based on spectral characteristics.
    
    This is a placeholder for more sophisticated instrument recognition.
    In a full system, you would use:
    - Spectral centroid analysis
    - Attack/decay envelope analysis  
    - Formant analysis
    - Machine learning classifiers
    
    Args:
        frequency: Fundamental frequency
        confidence: Detection confidence
        num_harmonics: Number of detected harmonics
        
    Returns:
        Boolean: True if classified as piano, False otherwise
    """
    # Simple heuristic based on harmonic content and frequency range
    # Piano notes typically have:
    # - Rich harmonic content (many harmonics)
    # - Strong fundamental
    # - Characteristic frequency ranges
    
    # Piano is more likely for:
    # 1. Strong fundamentals with many harmonics
    # 2. Frequencies in typical piano range (A0 to C8)
    # 3. High confidence detections
    
    piano_score = 0
    
    # Frequency range scoring
    if 80 <= frequency <= 1000:  # Prime piano range
        piano_score += 0.4
    elif frequency < 80 or frequency > 2000:  # Less common for piano
        piano_score -= 0.2
    
    # Harmonic content scoring
    if num_harmonics >= 4:  # Rich harmonic content
        piano_score += 0.3
    elif num_harmonics <= 2:  # Poor harmonic content
        piano_score -= 0.2
    
    # Confidence scoring
    if confidence > 0.8:
        piano_score += 0.3
    elif confidence < 0.4:
        piano_score -= 0.2
    
    # Return True if piano score is positive
    return piano_score > 0.2

def top_note_labels_from_cqt(cqt_spectrum, cqt_frequencies, top_k=TOP_NOTES):
    """
    Extract top K strongest peaks from CQT spectrum for visualization.
    
    This function is used for the red labels in the animation that show
    the strongest spectral components at each time frame.
    
    Returns:
        List of (frequency, note_name, magnitude) tuples
    """
    peak_freqs, peak_mags, _ = find_cqt_peaks(cqt_spectrum, cqt_frequencies)
    
    if len(peak_freqs) == 0:
        return []
    
    labels = []
    seen_notes = set()
    
    # Process strongest peaks first, avoiding duplicate note names
    for freq, mag in zip(peak_freqs[:top_k*2], peak_mags[:top_k*2]):
        if freq < FREQ_MIN or freq > FREQ_MAX:
            continue
            
        try:
            midi = librosa.hz_to_midi(freq)
            note_name = librosa.midi_to_note(midi, octave=True)
            
            # Avoid showing multiple peaks for the same note name
            # (which can happen with closely spaced harmonics)
            if note_name in seen_notes:
                continue
                
            labels.append((freq, note_name, mag))
            seen_notes.add(note_name)
            
            if len(labels) >= top_k:
                break
                
        except Exception:
            # Skip frequencies that can't be converted to notes
            continue
    
    return labels

# -------------------- Legacy STFT Support Functions (for compatibility) --------------------
# These functions maintain compatibility with any code that might still reference them

def detect_notes_with_onsets(spectrum, frequencies, current_time, onset_times, max_notes=5):
    """
    Legacy function maintained for compatibility.
    Redirects to CQT-based detection with appropriate warnings.
    """
    print("Warning: Using legacy STFT-based detection. Consider updating to CQT-based method.")
    return detect_notes_with_cqt_onsets(spectrum, frequencies, current_time, onset_times, max_notes)

def detect_simultaneous_notes(spectrum, frequencies, max_notes=5):
    """
    Legacy function for backward compatibility.
    """
    print("Warning: Using legacy STFT-based detection without onset information.")
    # Convert to new format by creating dummy onset times
    return detect_notes_with_cqt_onsets(spectrum, frequencies, 0.0, [], max_notes)
