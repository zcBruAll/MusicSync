# -------------------- Input/Output Configuration --------------------
INPUT_FILE = "Sounds/Ecossaise_Piano.mp3"  # File name and path of the input file
OUTPUT_GIF = "Output/cqt_analysis.gif"     # File name and path of the output gif  
OUTPUT_MIDI = "Output/detected_notes"      # File name and path of the output MIDI file

# -------------------- Processing Mode Configuration --------------------
ENABLE_ANIMATION = False  # Set to True for visual analysis, False for faster processing

# -------------------- Animation Parameters --------------------
FPS = 30  # Frames per second for animation (if enabled)

# -------------------- CQT-Specific Parameters (Replaces FFT_WINDOWS_SECONDS) --------------------
# CQT provides better frequency resolution for musical analysis
# Each octave gets the same number of frequency bins, matching musical scales naturally
BINS_PER_OCTAVE = 36      # 3 bins per semitone (36 bins per octave) for high resolution
N_OCTAVES = 7             # Cover range from C1 to C8 (covers full musical range)
CQT_FILTER_SCALE = 0.8    # Tighter filters for better frequency separation (0.5-1.0)
CQT_SPARSITY = 0.01       # Remove very small values to reduce noise (0.01-0.1)

# -------------------- Frequency Range Configuration --------------------
# Musical frequency range - optimized for typical musical content
FREQ_MIN = 80    # Just below C2 (80 Hz ≈ low piano range)
FREQ_MAX = 2000  # High enough for harmonics and overtones, low enough to avoid noise

# -------------------- Visualization Parameters --------------------
TOP_NOTES = 5  # Number of strongest peaks to show as red labels in animation

# -------------------- Enhanced Polyphonic Detection Parameters --------------------
# These parameters are tuned for CQT analysis and provide better note separation

# Peak Detection Settings
MIN_PEAK_HEIGHT = 0.05      # Lower threshold for better sensitivity with CQT
MIN_PEAK_DISTANCE = 2        # Bins between peaks (in CQT space, ~1 semitone)
PEAK_PROMINENCE = 0.05       # Minimum prominence to distinguish real peaks from noise

# Harmonic Analysis Settings  
MAX_HARMONICS = 10           # Maximum harmonics to analyze per fundamental
HARMONIC_TOLERANCE = 0.05    # Tighter tolerance for cleaner harmonic detection (5%)
HARMONIC_WEIGHT_DECAY = 0.85 # Weight decay for higher harmonics (85% retention per octave)

# Note Tracking Settings
SMOOTHING_TIME = 0.08        # Reduced gap tolerance for better temporal resolution (80ms)
MIN_NOTE_DURATION = 0.05     # Minimum note duration to avoid micro-notes (50ms)
DETECTION_THRESHOLD = 0.12   # Lower threshold for more sensitive detection

# Onset Detection Enhancement
ONSET_WINDOW_MS = 100        # Window around onsets for enhanced detection (100ms)
ONSET_BOOST_FACTOR = 1.3     # Confidence boost factor near onsets

# -------------------- MIDI Export Parameters --------------------
MIDI_TEMPO_BPM = 120         # BPM for MIDI file export
MIDI_VELOCITY_MIN = 64       # Minimum MIDI velocity (for weakest detected notes)
MIDI_VELOCITY_MAX = 127      # Maximum MIDI velocity (for strongest detected notes)
MIDI_PROGRAM = 0             # MIDI program number (0 = Acoustic Grand Piano)

# -------------------- Advanced Processing Options --------------------
# These settings affect the quality vs speed trade-off

# Audio Preprocessing
ENABLE_SPECTRAL_GATING = True    # Apply noise gating between notes
GATE_THRESHOLD_DB = -40          # Noise gate threshold in dB
HARMONIC_PERCUSSIVE_SEPARATION = True  # Separate harmonic and percussive components

# CQT Computation
CQT_HOP_RATIO = 0.25            # Hop length as fraction of frame size (affects time resolution)
CQT_WINDOW_BETA = 8.0           # Window beta parameter (affects frequency resolution)

# Multi-threading (for future optimization)
ENABLE_PARALLEL_PROCESSING = False  # Enable parallel processing of audio chunks
NUM_THREADS = 4                     # Number of threads for parallel processing

# -------------------- Debug and Analysis Options --------------------
VERBOSE_LOGGING = True              # Print detailed processing information
SAVE_INTERMEDIATE_RESULTS = False   # Save CQT matrices and peak data for analysis
PLOT_FREQUENCY_RESPONSE = False     # Generate frequency response plots

# -------------------- Instrument Classification Parameters --------------------
# Simple instrument classification settings (can be expanded for better accuracy)
PIANO_HARMONIC_THRESHOLD = 4        # Minimum harmonics for piano classification
PIANO_FREQUENCY_WEIGHT = 0.4        # Weight for frequency-based piano scoring
PIANO_CONFIDENCE_THRESHOLD = 0.2    # Threshold for piano vs other classification

# -------------------- Performance Monitoring --------------------
ENABLE_TIMING_ANALYSIS = True       # Track processing times for optimization
MEMORY_USAGE_MONITORING = False     # Monitor memory usage during processing

# -------------------- Validation and Quality Control --------------------
MAX_SIMULTANEOUS_NOTES = 8          # Maximum notes that can be active simultaneously
MIN_FREQUENCY_SEPARATION = 1.05     # Minimum frequency ratio between simultaneous notes
NOTE_STABILITY_THRESHOLD = 0.8      # Confidence threshold for note stability over time
