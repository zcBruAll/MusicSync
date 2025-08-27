import librosa
import pretty_midi
import numpy as np
import os

def audio_to_midi():
    """
    Convert an audio file to MIDI format by extracting chromatic notes.
    """
    notes_by_instruments = {}
    
    for file_path in file_paths:
        # Load the audio file 
        # y = audio signal, sr = sample rate in Hz (default 22050Hz)
        y, sr = librosa.load(path=file_path)
        
        # Detect note onset frames using backtracking for better accuracy
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr, backtrack=True)
        
        # Extract chromatic features using Short-Time Fourier Transform
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        
        # Process each detected onset to extract note information
        notes = []
        prev_time = 0
        
        for i, onset in enumerate(onset_frames):
        
            # Get chroma values at this onset
            chroma_at_onset = chroma[:, onset]
            
            # Find the dominant note (strongest chroma value)
            note_pitch = chroma_at_onset.argmax()
            
            # Convert frame to time
            onset_time = librosa.frames_to_time(onset, sr=sr)
            
            # Set normalized MIDI velocity
            velocity = 100
            
            # Calculate note duration (time until next onset or use current time for first note)
            if i == 0:
                duration = onset_time
            else:
                duration = onset_time - prev_time
                
            notes.append((note_pitch, onset_time, duration, velocity))
            prev_time = onset_time
        notes_by_instruments[file_path] = notes
    return notes_by_instruments

def generate_midi(notes_by_instruments):
    midi_file = pretty_midi.PrettyMIDI()
    
    for file_path, notes in notes_by_instruments.items():
        filename = os.path.basename(file_path).lower()
        
        if 'piano' in filename:
            instrument_program = 0  # Acoustic Grand Piano
        elif 'trumpet' in filename:
            instrument_program = 73  # Trumpet
        else:
            instrument_program = 0  # Default to piano
            
        # Create MIDI file
        instrument = pretty_midi.Instrument(program=instrument_program)
        
        # Add notes to instrument
        for pitch, onset, duration, velocity in notes:
            # Add 60 to pitch to get proper MIDI note number (C4 = 60)
            midi_note = pretty_midi.Note(
                velocity=velocity,
                pitch=pitch + 60,
                start=onset,
                end=onset + duration
            )
            instrument.notes.append(midi_note)
        
        # Add instrument to MIDI file
        midi_file.instruments.append(instrument)
        
    # Generate output filename based on input filename
    base_name = "all"
    output_filename = f"./Sounds/{base_name}_converted.mid"
    
    # Write MIDI file
    midi_file.write(output_filename)
    
    print(f"MIDI file created: {output_filename}")
    print(f"Number of notes extracted: {len(notes)}")# Create MIDI file
    
def print_notes(notes):
    for pitch, onset, duration, velocity in notes:
        print(f"{pitch}\t{onset:.2f}\t{duration:.2f}\t\t{velocity}")
# Example usage
if __name__ == "__main__":
    file_paths = ["./Sounds/Ecossaise_Trumpet.mp3","./Sounds/Ecossaise_Piano.mp3"]
    
    notes_by_instruments = audio_to_midi()
    # print_notes(notes)
    generate_midi(notes_by_instruments)