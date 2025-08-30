INPUT_FILE = "Sounds/Ecossaise_Piano.mp3" # File name and path of the input file
OUTPUT_GIF = "Output/analysis.gif"      # File name and path of the outputed gif
OUTPUT_MIDI = "Output/detected_notes"  # File name and path of the output MIDI file

ENABLE_ANIMATION = False

FPS = 30
FFT_WINDOWS_SECONDS = 0.046  # ~46ms for better time-frequency resolution (2048 samples at 44.1kHz)
FREQ_MIN = 80  # C2 - lowest note typically in music
FREQ_MAX = 2000  # High enough for harmonics but not noise
TOP_NOTES = 5

# Enhanced polyphonic detection parameters
MIN_PEAK_HEIGHT = 0.015  # Lowered for better sensitivity
MIN_PEAK_DISTANCE = 2  # Increased for better peak separation
MAX_HARMONICS = 12  # More harmonics for better fundamental detection
HARMONIC_TOLERANCE = 0.03  # Tighter tolerance for cleaner detection
HARMONIC_WEIGHT_DECAY = 0.85  # Weight decay for higher harmonics

SMOOTHING_TIME = 0.10  # Reduced for better temporal resolution
MIN_NOTE_DURATION = 0.05
DETECTION_THRESHOLD = 0.15

# MIDI export parameters
MIDI_TEMPO_BPM = 120                    # BPM for MIDI file
MIDI_VELOCITY_MIN = 64                  # minimum MIDI velocity
MIDI_VELOCITY_MAX = 127                 # maximum MIDI velocity
MIDI_PROGRAM = 0                        # MIDI program (0 = Acoustic Grand Piano)

