from animation import *
from mp3_to_midi import *
from midi_part.midi_comparator import *
from config import INPUT_FILE, OUTPUT_PIANO_MIDI, OUTPUT_TRUMPET_MIDI, OUTPUT_BOTH_MIDI

start_conversion()

# When both instruments
combine_midis(OUTPUT_PIANO_MIDI, OUTPUT_TRUMPET_MIDI, OUTPUT_BOTH_MIDI)
generate_graph(REF_MIDI, [OUTPUT_BOTH_MIDI])

start_animation(INPUT_FILE, OUTPUT_BOTH_MIDI)