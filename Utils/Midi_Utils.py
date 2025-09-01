import pretty_midi
import scipy.stats
import numpy as np

def readMidi(filepath):
    all_notes = []
    
    midi_data = pretty_midi.PrettyMIDI(filepath)
    for instrument in midi_data.instruments:
        all_notes.append(instrument.notes)
    
    return all_notes

def seperateInstrument(all_notes, instru):
    #trumpet
    if instru == 0:
        return all_notes[0]
    #piano
    if instru == 1:
        return all_notes[1]
    
def noteLifetime(note):
    return float(note.end - note.start)  

def getVelocity(notes):
    all_velocity = []
    
    for n in notes:
        all_velocity.append(n.velocity)
        
    return all_velocity

def velocityRange(notes, note):
    med = np.median(getVelocity(notes))
    iqr = scipy.stats.iqr(getVelocity(notes))
    
    if note.velocity <= med - iqr/2:
        return 2
    elif note.velocity <= med:
        return 3
    elif note.velocity <= med + iqr/2:
        return 4
    elif note.velocity <= 127:
        return 5
    
def get_min_max_pitch(noteList):
    # Calculating the max pitch and min pitch (used later to determine the Y position of the notes)
    maxPitch = 0
    minPitch = noteList[0][0].pitch
    for k in noteList:
        for i in k:
            if (i.pitch > maxPitch):
                maxPitch = i.pitch
            elif (i.pitch < minPitch):
                minPitch = i.pitch

    return minPitch, maxPitch