import librosa
import numpy as np
from scipy.signal import find_peaks
import math

from config import *

# -------------------- Conservative CQT-Based Note Detection with Trumpet Support --------------------

def detect_notes_with_cqt_onsets(cqt_spectrum, cqt_frequencies, current_time, onset_times, max_notes=5):
    """
    Balanced note detection that maintains conservative quality standards
    while adding targeted trumpet detection capabilities.
    
    Key principle: Only be more permissive when we have strong evidence
    that we're dealing with legitimate trumpet notes, not noise.
    """
    
    # Check if we're near an onset - but be more selective about what constitutes "near"
    near_onset = any(abs(current_time - onset_time) < 0.05 for onset_time in onset_times)
    very_near_onset = any(abs(current_time - onset_time) < 0.02 for onset_time in onset_times)
    
    # Use the original conservative parameters as baseline
    base_min_height = MIN_PEAK_HEIGHT
    base_threshold = DETECTION_THRESHOLD
    
    # Only lower thresholds significantly if we're very close to an onset
    if very_near_onset:
        adjusted_min_height = base_min_height * 0.8  # Only 20% reduction, not 40%
        adjusted_threshold = base_threshold * 0.85    # Only 15% reduction, not 30%
        onset_boost = 1.2  # Reduced from 1.4
    elif near_onset:
        adjusted_min_height = base_min_height * 0.9
        adjusted_threshold = base_threshold * 0.95
        onset_boost = 1.1
    else:
        adjusted_min_height = base_min_height
        adjusted_threshold = base_threshold
        onset_boost = 1.0
    
    # Find peaks with conservative parameters
    peak_freqs, peak_mags, peak_indices = find_cqt_peaks_conservative(
        cqt_spectrum, cqt_frequencies, min_height=adjusted_min_height
    )
    
    if len(peak_freqs) == 0:
        return []
    
    # Group harmonics with stricter quality requirements
    fundamentals = group_cqt_harmonics_conservative(peak_freqs, peak_mags, cqt_frequencies)
    
    # Only proceed with high-quality fundamental candidates
    high_quality_fundamentals = []
    for fundamental_data in fundamentals:
        f0, energy, num_harmonics, harmonic_strength, matched_instrument, pattern_score = fundamental_data
        
        # Strict quality gate - must meet multiple criteria
        passes_quality_check = evaluate_detection_quality(
            f0, energy, num_harmonics, harmonic_strength, pattern_score, adjusted_threshold
        )
        
        if passes_quality_check:
            high_quality_fundamentals.append(fundamental_data)
    
    # Convert only high-quality detections to notes
    detected_notes = []
    centroid, rolloff, flatness = compute_timbre_features_conservative(cqt_spectrum, cqt_frequencies)
    
    for f0, energy, num_harmonics, harmonic_strength, matched_instrument, pattern_score in high_quality_fundamentals:
        try:
            # Conservative confidence calculation - no excessive bonuses
            confidence = calculate_conservative_confidence(
                energy, num_harmonics, harmonic_strength, pattern_score, onset_boost
            )
            
            # Conservative instrument classification
            is_piano = classify_instrument_conservative(
                f0, confidence, num_harmonics, pattern_score,
                centroid, rolloff, flatness, matched_instrument
            )
            
            # Convert to musical note
            midi = librosa.hz_to_midi(f0)
            note_name = librosa.midi_to_note(midi, octave=True)
            
            detected_notes.append((f0, confidence, note_name, is_piano))
            
        except Exception as e:
            continue
    
    # Aggressive duplicate removal - be very strict about what constitutes different notes
    detected_notes = remove_duplicate_notes_strict(detected_notes)
    
    # Sort by confidence and limit to reasonable number
    detected_notes.sort(key=lambda x: x[1], reverse=True)
    return detected_notes[:min(max_notes, 4)]  # Cap at 4 simultaneous notes max

def evaluate_detection_quality(f0, energy, num_harmonics, harmonic_strength, pattern_score, threshold):
    """
    Strict quality evaluation - multiple criteria must be met for a detection to be accepted.
    
    This is the key function that prevents false positives while allowing trumpet notes.
    """
    
    # Rule 1: Must meet energy threshold
    if energy < threshold:
        return False
    
    # Rule 2: Must have either strong harmonics OR very high energy
    if num_harmonics < 2 and energy < threshold * 2.0:
        return False
    
    # Rule 3: Harmonic strength must be reasonable
    if harmonic_strength < 0.4:
        return False
    
    # Rule 4: Must be in reasonable musical frequency range
    if f0 < 70 or f0 > 2000:  # Slightly extended for trumpet but not too much
        return False
    
    # Rule 5: Pattern score should indicate some instrument-like behavior
    if pattern_score < 0.3:
        return False
    
    # Rule 6: Very high frequency detections need extra evidence
    if f0 > 1500 and (num_harmonics < 3 or energy < threshold * 1.5):
        return False
    
    # Rule 7: Very low frequency detections need strong harmonic support  
    if f0 < 100 and (num_harmonics < 3 or harmonic_strength < 0.6):
        return False
    
    return True

def find_cqt_peaks_conservative(cqt_spectrum, cqt_frequencies, min_height=MIN_PEAK_HEIGHT):
    """
    Conservative peak finding that maintains original quality standards
    while being slightly more aware of trumpet characteristics.
    """
    if len(cqt_spectrum) == 0:
        return [], [], []
    
    # Use original conservative distance parameters mostly
    min_distance_bins = max(2, int(36 / 12))  # 1 semitone minimum
    
    # Conservative prominence - higher than my previous version
    prominence_threshold = max(PEAK_PROMINENCE, min_height * 1.5)
    
    # Find peaks with strict parameters
    peaks, properties = find_peaks(
        cqt_spectrum, 
        height=min_height, 
        distance=min_distance_bins,
        prominence=prominence_threshold,
        width=1.0,           # Require minimum width
        rel_height=0.8       # Require good peak shape
    )
    
    if len(peaks) == 0:
        return [], [], []
    
    peak_freqs = cqt_frequencies[peaks]
    peak_mags = cqt_spectrum[peaks]
    
    # Strict filtering - remove peaks that are too weak relative to strongest
    if len(peak_mags) > 0:
        max_mag = np.max(peak_mags)
        # Increased threshold from 0.1 to 0.15 - be more selective
        strong_enough = peak_mags >= max_mag * 0.15
        
        peak_freqs = peak_freqs[strong_enough]
        peak_mags = peak_mags[strong_enough]
        peaks = peaks[strong_enough]
    
    # Additional filtering: remove isolated weak peaks
    filtered_peaks = []
    filtered_mags = []
    filtered_indices = []
    
    for i, (freq, mag, idx) in enumerate(zip(peak_freqs, peak_mags, peaks)):
        # Check if this peak has nearby support (other peaks within reasonable distance)
        has_support = False
        for j, other_freq in enumerate(peak_freqs):
            if i != j:
                freq_ratio = max(freq, other_freq) / min(freq, other_freq)
                # Support from harmonically related frequencies or nearby peaks
                if (freq_ratio <= 4.0 and freq_ratio >= 1.8) or abs(freq - other_freq) < freq * 0.1:
                    has_support = True
                    break
        
        # Accept peak if it has support OR is very strong
        if has_support or mag >= max_mag * 0.4:
            filtered_peaks.append(freq)
            filtered_mags.append(mag)
            filtered_indices.append(idx)
    
    if len(filtered_peaks) > 0:
        # Sort by magnitude (strongest first)
        sort_idx = np.argsort(filtered_mags)[::-1]
        return (np.array(filtered_peaks)[sort_idx], 
                np.array(filtered_mags)[sort_idx], 
                np.array(filtered_indices)[sort_idx])
    else:
        return [], [], []

def group_cqt_harmonics_conservative(peak_freqs, peak_mags, cqt_frequencies):
    """
    Conservative harmonic grouping that maintains quality while adding trumpet support.
    
    Key changes from original:
    1. Keep strict quality requirements
    2. Add limited missing fundamental detection only for strong evidence
    3. Better duplicate prevention
    """
    if len(peak_freqs) == 0:
        return []
    
    fundamentals = []
    used_peaks = set()
    
    # Sort peaks by magnitude (strongest first)
    peak_order = np.argsort(peak_mags)[::-1]
    
    # First pass: standard fundamental detection with original quality standards
    for i in peak_order:
        if i in used_peaks:
            continue
            
        f0_candidate = peak_freqs[i]
        f0_magnitude = peak_mags[i]
        
        # Find harmonics using conservative approach
        harmonics = [(f0_candidate, f0_magnitude, 1)]  # Start with fundamental
        harmonic_indices = {i}
        
        # Look for harmonics with strict matching
        for harmonic_num in range(2, MAX_HARMONICS + 1):
            expected_freq = f0_candidate * harmonic_num
            
            if expected_freq > FREQ_MAX:
                break
                
            # Find closest peak with strict tolerance
            best_match_idx = None
            best_match_error = float('inf')
            
            for j in peak_order:
                if j in used_peaks or j == i:
                    continue
                    
                freq_error = abs(peak_freqs[j] - expected_freq) / expected_freq
                
                # Use original strict tolerance
                if freq_error < HARMONIC_TOLERANCE and freq_error < best_match_error:
                    best_match_error = freq_error
                    best_match_idx = j
            
            if best_match_idx is not None:
                harmonics.append((peak_freqs[best_match_idx], peak_mags[best_match_idx], harmonic_num))
                harmonic_indices.add(best_match_idx)
        
        # Conservative evaluation - require good evidence
        num_harmonics = len(harmonics)
        harmonic_strength = calculate_harmonic_strength_conservative(harmonics)
        matched_instrument, pattern_score = match_harmonic_pattern_conservative(harmonics)
        
        # Strict acceptance criteria - must have multiple supporting factors
        accept_fundamental = False
        
        if num_harmonics >= 3 and harmonic_strength >= 0.6:
            accept_fundamental = True
        elif num_harmonics >= 2 and harmonic_strength >= 0.7 and f0_magnitude > 0.2:
            accept_fundamental = True  
        elif num_harmonics == 1 and f0_magnitude > 0.4 and pattern_score > 0.6:
            accept_fundamental = True  # Very strong single peak with good pattern
        
        if accept_fundamental:
            total_energy = sum(mag * (HARMONIC_WEIGHT_DECAY ** (harm_num - 1)) 
                             for freq, mag, harm_num in harmonics)
            
            fundamentals.append((f0_candidate, total_energy, num_harmonics,
                               harmonic_strength, matched_instrument, pattern_score))
            used_peaks.update(harmonic_indices)
    
    # Second pass: VERY LIMITED missing fundamental detection
    # Only for cases with very strong evidence
    remaining_peaks = [i for i in peak_order if i not in used_peaks]
    
    if len(remaining_peaks) >= 2:  # Need at least 2 unused peaks for missing fundamental
        for i in remaining_peaks[:3]:  # Only check strongest 3 unused peaks
            if i in used_peaks:
                continue
                
            candidate_freq = peak_freqs[i]
            candidate_mag = peak_mags[i]
            
            # Only consider missing fundamental if this peak is quite strong
            if candidate_mag < np.max(peak_mags) * 0.3:
                continue
            
            # Only check if could be 2nd or 3rd harmonic (not higher)
            for harmonic_num in [2, 3]:
                f0_est = candidate_freq / harmonic_num
                
                if not (80 <= f0_est <= 1000):  # Conservative frequency range
                    continue
                
                # Look for supporting evidence with strict requirements
                supporting_harmonics = [(candidate_freq, candidate_mag, harmonic_num)]
                
                for other_harm_num in [2, 3, 4]:
                    if other_harm_num == harmonic_num:
                        continue
                        
                    expected_other_freq = f0_est * other_harm_num
                    
                    for j in remaining_peaks:
                        if j == i or j in used_peaks:
                            continue
                            
                        if abs(peak_freqs[j] - expected_other_freq) < expected_other_freq * 0.04:  # Strict tolerance
                            supporting_harmonics.append((peak_freqs[j], peak_mags[j], other_harm_num))
                            break
                
                # Need at least 2 supporting harmonics for missing fundamental
                if len(supporting_harmonics) >= 2:
                    harmonic_strength = calculate_harmonic_strength_conservative(supporting_harmonics)
                    matched_instrument, pattern_score = match_harmonic_pattern_conservative(supporting_harmonics)
                    
                    # Very strict criteria for missing fundamental
                    if (harmonic_strength >= 0.7 and pattern_score >= 0.6 and 
                        sum(mag for freq, mag, harm_num in supporting_harmonics) > 0.3):
                        
                        total_energy = sum(mag * (HARMONIC_WEIGHT_DECAY ** (harm_num - 1)) 
                                         for freq, mag, harm_num in supporting_harmonics)
                        
                        fundamentals.append((f0_est, total_energy, len(supporting_harmonics),
                                           harmonic_strength, matched_instrument, pattern_score))
                        
                        # Mark supporting peaks as used
                        for freq, mag, harm_num in supporting_harmonics:
                            for k, pf in enumerate(peak_freqs):
                                if abs(pf - freq) < 0.1:
                                    used_peaks.add(k)
                                    break
                        break
    
    # Sort by total energy and return
    fundamentals.sort(key=lambda x: x[1], reverse=True)
    return fundamentals[:6]  # Limit to max 6 fundamental candidates

def calculate_conservative_confidence(energy, num_harmonics, harmonic_strength, pattern_score, onset_boost):
    """
    Conservative confidence calculation that doesn't over-boost weak detections.
    """
    # Base confidence from energy (primary factor)
    base_confidence = energy
    
    # Conservative harmonic bonus - not too generous
    harmonic_bonus = 1 + 0.08 * max(0, num_harmonics - 1)  # Reduced from 0.12
    
    # Pattern quality bonus - only reward good patterns significantly  
    if pattern_score > 0.7:
        pattern_bonus = 1.15
    elif pattern_score > 0.5:
        pattern_bonus = 1.05
    else:
        pattern_bonus = 1.0
    
    # Harmonic strength bonus - conservative
    if harmonic_strength > 0.7:
        strength_bonus = 1.1
    else:
        strength_bonus = 1.0
    
    # Combine factors conservatively
    confidence = base_confidence * harmonic_bonus * pattern_bonus * strength_bonus * onset_boost
    
    return confidence

def classify_instrument_conservative(frequency, confidence, num_harmonics, pattern_score, 
                                   centroid, rolloff, flatness, matched_instrument):
    """
    Conservative instrument classification that maintains original decision boundaries
    while incorporating trumpet pattern recognition.
    """
    
    # Start with pattern matching results - but don't over-weight them
    if matched_instrument == "piano":
        piano_score = 0.2  # Reduced from 0.4
    elif matched_instrument == "trumpet" or matched_instrument == "brass":
        piano_score = -0.1  # Less negative than before
    else:
        piano_score = 0.0
    
    # Frequency range analysis - keep original logic mostly intact
    if 80 <= frequency <= 300:
        piano_score += 0.3  # Piano bass range
    elif 300 <= frequency <= 600:
        piano_score += 0.1  # Mixed range, slight piano preference  
    elif 600 <= frequency <= 1200:
        piano_score -= 0.1  # Trumpet range
    elif frequency > 1200:
        piano_score -= 0.2  # High frequency
    
    # Harmonic structure - keep original conservative logic
    if num_harmonics <= 3:
        piano_score += 0.15  # Piano harmonics decay quickly
    elif num_harmonics >= 5:
        piano_score -= 0.15  # Trumpet has richer harmonics
    
    # Pattern score - only give bonus for very good matches
    if pattern_score > 0.8:
        if matched_instrument == "piano":
            piano_score += 0.2
        elif matched_instrument in ["trumpet", "brass"]:
            piano_score -= 0.2
    
    # Spectral features - keep conservative thresholds
    if centroid < 600:  # Conservative piano centroid threshold
        piano_score += 0.1
    elif centroid > 1000:  # Clear trumpet indication
        piano_score -= 0.15
    
    if rolloff < 2000:
        piano_score += 0.1
    elif rolloff > 3000:
        piano_score -= 0.1
    
    # Conservative decision threshold - slightly favor piano as before
    return piano_score > 0.2  # Increased from 0.15 to be more conservative

def remove_duplicate_notes_strict(detected_notes):
    """
    Very strict duplicate removal - err on the side of removing too many rather than too few.
    """
    if not detected_notes:
        return []
    
    # Group by note name (including octave)
    note_groups = {}
    for freq, conf, name, is_piano in detected_notes:
        if name not in note_groups:
            note_groups[name] = []
        note_groups[name].append((freq, conf, name, is_piano))
    
    unique_notes = []
    for name, detections in note_groups.items():
        # If multiple detections of same note, only keep the strongest
        best_detection = max(detections, key=lambda x: x[1])
        unique_notes.append(best_detection)
    
    # Additional step: remove notes that are very close in frequency
    final_notes = []
    unique_notes.sort(key=lambda x: x[0])  # Sort by frequency
    
    for i, (freq, conf, name, is_piano) in enumerate(unique_notes):
        # Check if this frequency is too close to any already accepted frequency
        too_close = False
        for prev_freq, prev_conf, prev_name, prev_is_piano in final_notes:
            freq_ratio = max(freq, prev_freq) / min(freq, prev_freq)
            if freq_ratio < 1.03:  # Less than 3% frequency difference
                too_close = True
                break
        
        if not too_close:
            final_notes.append((freq, conf, name, is_piano))
    
    return final_notes

def calculate_harmonic_strength_conservative(harmonics):
    """
    Conservative harmonic strength calculation - maintain original standards.
    """
    if len(harmonics) < 2:
        return 0.5
    
    # Sort by harmonic number
    harmonics = sorted(harmonics, key=lambda x: x[2])
    
    strength_scores = []
    
    for i in range(len(harmonics) - 1):
        curr_freq, curr_amp, curr_num = harmonics[i]
        next_freq, next_amp, next_num = harmonics[i + 1]
        
        # Expected frequency ratio
        expected_freq_ratio = next_num / curr_num
        actual_freq_ratio = next_freq / curr_freq
        
        # Strict frequency accuracy requirement
        freq_accuracy = max(0, 1 - abs(actual_freq_ratio - expected_freq_ratio) / expected_freq_ratio)
        strength_scores.append(freq_accuracy)
        
        # Conservative amplitude progression - expect some decay
        if curr_amp > 0:
            amp_ratio = next_amp / curr_amp
            
            # Allow some flexibility for trumpet, but not too much
            if 0.4 <= amp_ratio <= 1.2:  # Reasonable range
                amp_score = 1.0
            else:
                amp_score = max(0, 1 - abs(amp_ratio - 0.7) / 0.7)
            
            strength_scores.append(amp_score)
    
    return np.mean(strength_scores) if strength_scores else 0.5

def match_harmonic_pattern_conservative(harmonics):
    """
    Conservative pattern matching that maintains quality standards.
    """
    if not harmonics or len(harmonics) == 0:
        return "generic", 0.0

    # Sort and normalize
    harmonics = sorted(harmonics, key=lambda x: x[2])
    max_amplitude = max(h[1] for h in harmonics)
    if max_amplitude <= 0:
        return "generic", 0.0
    
    detected_ratios = [h[1] / max_amplitude for h in harmonics]
    harmonic_numbers = [h[2] for h in harmonics]
    
    best_instrument = "generic"
    best_score = 0.0
    
    # Compare against templates
    for instrument_name, template_ratios in HARMONIC_TEMPLATES.items():
        if len(template_ratios) == 0:
            continue
        
        # Calculate match score with conservative standards
        score = calculate_pattern_match_score_conservative(detected_ratios, harmonic_numbers, template_ratios)
        
        if score > best_score:
            best_score = score
            best_instrument = instrument_name
    
    return best_instrument, best_score

def calculate_pattern_match_score_conservative(detected_ratios, harmonic_numbers, template_ratios):
    """
    Conservative pattern matching that requires good correspondence.
    """
    if len(detected_ratios) == 0 or len(template_ratios) == 0:
        return 0.0
    
    total_error = 0.0
    comparisons = 0
    
    # Compare each detected harmonic against template
    for i, (ratio, harm_num) in enumerate(zip(detected_ratios, harmonic_numbers)):
        template_idx = harm_num - 1
        
        if template_idx < len(template_ratios):
            expected_ratio = template_ratios[template_idx]
            error = abs(ratio - expected_ratio)
            total_error += error
            comparisons += 1
    
    if comparisons == 0:
        return 0.0
    
    # Convert to match score - be more demanding
    avg_error = total_error / comparisons
    match_score = max(0.0, 1.0 - avg_error * 1.2)  # Penalty factor increased
    
    # Smaller completeness bonus
    completeness_bonus = min(comparisons / len(template_ratios), 1.0) * 0.05  # Reduced from 0.1
    
    return min(1.0, match_score + completeness_bonus)

def compute_timbre_features_conservative(cqt_spectrum, cqt_frequencies):
    """
    Conservative timbre feature computation - maintain original approach.
    """
    magnitude = np.asarray(cqt_spectrum).astype(float)
    if magnitude.size == 0 or np.sum(magnitude) == 0:
        return 0.0, 0.0, 0.0
    
    total_energy = np.sum(magnitude)
    centroid = np.sum(cqt_frequencies * magnitude) / total_energy
    
    cumulative_energy = np.cumsum(magnitude)
    rolloff_idx = np.searchsorted(cumulative_energy, 0.85 * cumulative_energy[-1])
    rolloff = cqt_frequencies[min(rolloff_idx, len(cqt_frequencies) - 1)]
    
    flatness = np.exp(np.mean(np.log(magnitude + 1e-10))) / (np.mean(magnitude) + 1e-10)
    
    return centroid, rolloff, flatness

def top_note_labels_from_cqt(cqt_spectrum, cqt_frequencies, top_k=TOP_NOTES):
    """
    Conservative top note labeling for visualization.
    """
    peak_freqs, peak_mags, _ = find_cqt_peaks_conservative(cqt_spectrum, cqt_frequencies)
    
    if len(peak_freqs) == 0:
        return []
    
    labels = []
    seen_notes = set()
    used_freqs = set()
    
    # Process only strongest peaks
    for freq, mag in zip(peak_freqs[:8], peak_mags[:8]):  # Limit to top 8
        if freq < FREQ_MIN or freq > FREQ_MAX:
            continue
        
        # Skip if too close to used frequency
        if any(abs(freq - used_freq) < used_freq * 0.08 for used_freq in used_freqs):
            continue
            
        try:
            midi = librosa.hz_to_midi(freq)
            note_name = librosa.midi_to_note(midi, octave=True)
            
            # Conservative duplicate avoidance
            if note_name in seen_notes:
                continue
                
            labels.append((freq, note_name, mag))
            seen_notes.add(note_name)
            used_freqs.add(freq)
            
            if len(labels) >= top_k:
                break
                
        except Exception:
            continue
    
    return labels