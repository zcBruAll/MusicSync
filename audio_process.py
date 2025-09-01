import librosa
import numpy as np
import time
from scipy.signal import find_peaks
from scipy.ndimage import median_filter
from scipy.interpolate import interp1d

# -------------------- Load & preprocess --------------------
def preprocess_audio(file_path):
    """Enhanced audio preprocessing with better separation techniques"""
    print("Loading and preprocessing audio with enhanced techniques...")
    start_time = time.time()
    
    # Load audio
    y, sr = librosa.load(file_path, mono=True, sr=None)
    
    # Apply pre-emphasis to boost higher frequencies
    pre_emphasis = 0.97
    y = np.append(y[0], y[1:] - pre_emphasis * y[:-1])
    
    # Enhanced harmonic-percussive separation with multiple margins
    y_harmonic, y_percussive = librosa.effects.hpss(y, margin=(1.0, 5.0))
    
    # NEW: Apply spectral gating to reduce noise between notes
    y_gated = apply_spectral_gating(y_harmonic, sr)
    
    # Use primarily harmonic component with some original signal
    y_processed = 0.9 * y_gated + 0.1 * y
    
    print(f"Enhanced preprocessing completed in {time.time() - start_time:.2f} seconds")
    return y_processed, sr

def apply_spectral_gating(y, sr, gate_threshold_db=-40, attack_time=0.01, release_time=0.1):
    """
    Apply spectral gating to reduce noise during quiet periods.
    This helps isolate note events more clearly.
    """
    # Compute short-time energy
    hop_length = int(sr * 0.01)  # 10ms hops
    frame_length = int(sr * 0.025)  # 25ms frames
    
    # Calculate RMS energy per frame
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    
    # Convert to dB and create gate mask
    rms_db = librosa.amplitude_to_db(rms, ref=np.max(rms))
    gate_mask = rms_db > gate_threshold_db
    
    # Smooth the gate mask to avoid abrupt changes
    attack_frames = int(attack_time * sr / hop_length)
    release_frames = int(release_time * sr / hop_length)
    
    # Apply attack/release smoothing
    gate_smooth = np.copy(gate_mask).astype(float)
    for i in range(1, len(gate_smooth)):
        if gate_mask[i] and not gate_mask[i-1]:  # Attack
            for j in range(max(0, i-attack_frames), i):
                alpha = (j - (i-attack_frames)) / attack_frames
                gate_smooth[j] = alpha
        elif not gate_mask[i] and gate_mask[i-1]:  # Release
            for j in range(i, min(len(gate_smooth), i+release_frames)):
                alpha = 1.0 - (j - i) / release_frames
                gate_smooth[j] = alpha
    
    # Interpolate gate to match audio length
    time_frames = librosa.frames_to_time(range(len(gate_smooth)), sr=sr, hop_length=hop_length)
    time_audio = np.linspace(0, len(y)/sr, len(y))
    gate_interp = interp1d(time_frames, gate_smooth, kind='linear', 
                          bounds_error=False, fill_value=(gate_smooth[0], gate_smooth[-1]))
    gate_full = gate_interp(time_audio)
    
    # Apply gate with minimum level to avoid complete silence
    min_level = 0.1
    gate_full = np.maximum(gate_full, min_level)
    
    return y * gate_full

def compute_enhanced_spectrogram(y, sr, n_fft, hop_length):
    """Compute enhanced spectrogram with multiple techniques"""
    # Use multiple window types and combine
    windows = ['hann', 'hamming', 'blackman']
    spectrograms = []
    
    for window in windows:
        D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length, 
                        win_length=n_fft, window=window, center=True)
        spectrograms.append(np.abs(D))
    
    # Combine spectrograms (weighted average)
    weights = [0.5, 0.3, 0.2]  # Hann gets most weight
    S = np.zeros_like(spectrograms[0])
    for spec, weight in zip(spectrograms, weights):
        S += spec * weight
    
    # NEW: Apply advanced spectral processing
    S_processed = apply_spectral_masking_removal(S)
    S_whitened = spectral_whitening(S_processed, smoothing_factor=0.15)
    
    # Combine processed versions with different weights
    S_final = 0.6 * S_processed + 0.4 * S_whitened
    
    return S_final

def apply_spectral_masking_removal(S, masking_threshold=0.1):
    """
    Remove spectral masking effects where loud components hide quieter ones.
    This is particularly important for polyphonic music analysis.
    """
    S_unmasked = np.copy(S)
    
    # For each time frame, identify masking relationships
    for t in range(S.shape[1]):
        spectrum = S[:, t]
        
        # Find local maxima (potential maskers)
        peaks, _ = find_peaks(spectrum, height=np.max(spectrum) * 0.1, distance=5)
        
        for peak in peaks:
            peak_mag = spectrum[peak]
            
            # Apply masking in frequency neighborhood
            # Masking is stronger for nearby frequencies
            for f in range(len(spectrum)):
                freq_distance = abs(f - peak)
                if freq_distance > 0:
                    # Calculate masking threshold based on distance and magnitude
                    masking_level = peak_mag * np.exp(-freq_distance * 0.1) * masking_threshold
                    
                    # Reduce masking effect by boosting masked components
                    if spectrum[f] < masking_level and spectrum[f] > 0:
                        boost_factor = 1.0 + (masking_level - spectrum[f]) / masking_level * 0.3
                        S_unmasked[f, t] *= boost_factor
    
    return S_unmasked

def spectral_whitening(S, smoothing_factor=0.1):
    """Apply spectral whitening to reduce masking effects"""
    # Compute smoothed spectrum envelope
    S_smooth = median_filter(S, size=(1, int(S.shape[1] * smoothing_factor)))
    S_smooth[S_smooth == 0] = 1e-10  # Avoid division by zero
    
    # Whiten by dividing by envelope
    S_white = S / S_smooth
    
    return S_white


