# -------------------- Input/Output Configuration --------------------
INPUT_FILE = "Sounds/PinkPanther_Both.mp3"  # File name and path of the input file
OUTPUT_GIF = "Output/cqt_analysis.gif"     # File name and path of the output gif  
OUTPUT_PIANO_MIDI = "Output/detected_notes0.mid"      # File name and path of the output MIDI file
OUTPUT_TRUMPET_MIDI = "Output/detected_notes73.mid"
OUTPUT_BOTH_MIDI = "Output/detected_notesboth.mid"
REF_MIDI = "Sounds/PinkPanther.midi"

# -------------------- Processing Mode Configuration --------------------
ENABLE_GRAPH_ANIMATION = False  # Set to True for visual analysis, False for faster processing

# -------------------- Animation Parameters --------------------
FPS = 30  # Frames per second for animation (if enabled)

# -------------------- Enhanced Harmonic Templates --------------------
# Key insight: Piano harmonics decay rapidly, trumpet has formant-boosted mid harmonics
HARMONIC_TEMPLATES = {
    "piano":   [1.0, 0.8, 0.5, 0.3, 0.2, 0.12, 0.08, 0.05],  # Classic rapid decay
    "trumpet": [0.7, 0.9, 1.0, 0.85, 0.7, 0.5, 0.3, 0.2],    # Formant-boosted 2nd-3rd harmonics
    "brass":   [0.6, 0.8, 0.9, 0.75, 0.6, 0.4, 0.25, 0.15],  # General brass family
    "generic": [1.0, 0.7, 0.5, 0.35, 0.25, 0.18, 0.12, 0.08] # Fallback template
}

# -------------------- CQT-Specific Parameters --------------------
BINS_PER_OCTAVE = 36      # 3 bins per semitone for high resolution
N_OCTAVES = 7             # Extended range but not excessive (C1 to C8)
CQT_FILTER_SCALE = 0.8    # Tighter filters for better frequency separation
CQT_SPARSITY = 0.01       # Remove very small values to reduce noise

# -------------------- Balanced Frequency Range Configuration --------------------
# Extended for trumpet but not so wide as to invite noise
FREQ_MIN = 70     # Slightly lower for bass instruments
FREQ_MAX = 2500   # Higher than piano-only (2000) but not excessive (was 4000)

# -------------------- Visualization Parameters --------------------
TOP_NOTES = 5  # Back to reasonable number for clarity

# -------------------- Conservative Core Detection Parameters --------------------
# These are the main knobs that control sensitivity vs specificity

# Peak Detection Settings - Keep original conservative values mostly
MIN_PEAK_HEIGHT = 0.06      # Original value - proven to work well
MIN_PEAK_DISTANCE = 2        # Original value - prevents over-detection
PEAK_PROMINENCE = 0.07       # Original value - distinguishes real peaks from noise

# Harmonic Analysis Settings  
MAX_HARMONICS = 10           # Reasonable limit - not too many
HARMONIC_TOLERANCE = 0.05    # Original strict tolerance - prevents false matches
HARMONIC_WEIGHT_DECAY = 0.85 # Moderate decay - works for both instruments

# Note Tracking Settings - Keep proven values
SMOOTHING_TIME = 0.12        # Original value worked well
MIN_NOTE_DURATION = 0.08     # Slightly increased to filter out artifacts
DETECTION_THRESHOLD = 0.12   # Original threshold - proven effective

# Onset Detection Enhancement - Moderate improvements only
ONSET_WINDOW_MS = 50        # Reasonable window size
ONSET_BOOST_FACTOR = 1.2     # Moderate boost - not excessive

# -------------------- Advanced Processing Options --------------------
# Keep conservative settings that were working

# Audio Preprocessing
ENABLE_SPECTRAL_GATING = True    # This helps with noise reduction
GATE_THRESHOLD_DB = -40          # Original threshold
HARMONIC_PERCUSSIVE_SEPARATION = True  # Helps separate instruments

# CQT Computation - Balanced parameters
CQT_HOP_RATIO = 0.25            # Good time resolution without oversampling  
CQT_WINDOW_BETA = 8.0           # Standard value

# -------------------- Instrument Classification Parameters --------------------
# Conservative thresholds that don't over-classify

PIANO_CLASSIFICATION = {
    'typical_centroid_range': (200, 800),   # Conservative range
    'typical_rolloff_range': (800, 2500),   # Conservative range  
    'typical_flatness_range': (0.05, 0.25), # Conservative range
    'typical_freq_range': (80, 1800),       # Main piano range
}

TRUMPET_CLASSIFICATION = {
    'typical_centroid_range': (400, 1200),  # Conservative trumpet range
    'typical_rolloff_range': (1000, 2500),  # Conservative rolloff range
    'typical_flatness_range': (0.15, 0.35), # Conservative flatness range  
    'typical_freq_range': (150, 1000),      # Main trumpet fundamental range
}

# -------------------- MIDI Export Parameters --------------------
MIDI_TEMPO_BPM = 120         # Standard tempo
MIDI_VELOCITY_MIN = 64       # Conservative velocity range
MIDI_VELOCITY_MAX = 127      # Full velocity range
MIDI_PROGRAM = 0             # Acoustic Grand Piano

# -------------------- Debug and Analysis Options --------------------
VERBOSE_LOGGING = True              # Keep logging for debugging
SAVE_INTERMEDIATE_RESULTS = False   # Don't save unless debugging
PLOT_FREQUENCY_RESPONSE = False     # Don't plot unless debugging

# -------------------- Performance Monitoring --------------------
ENABLE_TIMING_ANALYSIS = True       # Track performance
MEMORY_USAGE_MONITORING = False     # Only if needed

# -------------------- Quality Control Parameters --------------------
# These are crucial for preventing false positives

MAX_SIMULTANEOUS_NOTES = 6          # Reasonable limit - most music has ≤6 simultaneous notes
MIN_FREQUENCY_SEPARATION = 1.03     # Prevent duplicate detections (3% minimum separation)
NOTE_STABILITY_THRESHOLD = 0.75     # Require reasonable stability over time

# Minimum evidence thresholds - these prevent weak detections from being accepted
MIN_HARMONIC_EVIDENCE = 2           # Need at least 2 harmonics OR very strong single peak
MIN_PATTERN_SCORE = 0.3             # Minimum pattern matching score to accept detection  
MIN_ENERGY_RATIO = 0.15             # Minimum energy relative to strongest peak in frame

# Quality gates - multiple criteria that must be met
QUALITY_GATES = {
    'min_detection_confidence': 0.1,    # Minimum overall confidence
    'max_spurious_rate': 0.2,           # Maximum allowed spurious detection rate
    'min_instrument_confidence': 0.2,   # Minimum confidence for instrument classification
}

# -------------------- Frequency-Specific Tuning --------------------
# Different frequency ranges have different characteristics and need different handling

# Low frequency range (70-250 Hz) - Piano bass, some trumpet fundamentals
LOW_FREQ_PARAMS = {
    'range': (70, 250),
    'min_harmonics_required': 2,        # Require harmonic support in bass
    'energy_threshold_multiplier': 1.2,  # Slightly higher threshold
    'instrument_bias': 'piano'          # Slight piano bias in this range
}

# Mid frequency range (250-800 Hz) - Mixed piano/trumpet fundamentals  
MID_FREQ_PARAMS = {
    'range': (250, 800),
    'min_harmonics_required': 1,        # Can accept single strong peaks
    'energy_threshold_multiplier': 1.0,  # Standard threshold
    'instrument_bias': None             # No bias - let pattern matching decide
}

# High frequency range (800+ Hz) - Trumpet fundamentals and harmonics
HIGH_FREQ_PARAMS = {
    'range': (800, 2500),  
    'min_harmonics_required': 1,        # Accept single peaks (could be trumpet)
    'energy_threshold_multiplier': 0.9,  # Slightly more sensitive
    'instrument_bias': 'trumpet'        # Slight trumpet bias in this range
}

# -------------------- Harmonic Analysis Tuning --------------------
# Controls how strictly we enforce harmonic relationships

HARMONIC_ANALYSIS = {
    'strict_fundamental_matching': True,     # Require good fundamental frequency match
    'allow_missing_fundamental': True,       # But allow missing fundamental in limited cases
    'max_missing_fundamental_harmonics': 3,  # Only check up to 3rd harmonic for missing fundamental
    'harmonic_strength_threshold': 0.4,      # Minimum harmonic pattern strength
    'pattern_match_weight': 0.3,             # Weight of pattern matching in final decision
}

# -------------------- Temporal Analysis Parameters --------------------
# Controls how notes are tracked over time

TEMPORAL_ANALYSIS = {
    'onset_sensitivity_window': 0.05,       # 50ms window for onset-enhanced detection
    'note_continuation_gap': 0.12,          # 120ms max gap before ending note  
    'minimum_note_duration': 0.08,          # 80ms minimum duration
    'stability_requirement': 0.75,          # Require 75% consistency over note duration
}

# -------------------- Error Prevention Parameters --------------------
# These help catch and filter out common types of false positives

ERROR_PREVENTION = {
    'max_frequency_deviation': 0.05,        # Maximum frequency drift within a note (5%)
    'min_peak_isolation': 0.15,             # Minimum relative isolation for accepting weak peaks
    'duplicate_frequency_threshold': 0.03,   # Consider frequencies within 3% as duplicates
    'noise_floor_multiple': 2.0,            # Peaks must be at least 2x noise floor
    'consistency_requirement': 0.6,         # Require 60% consistency in detection across frames
}