import pretty_midi

def readMidi(filepath):
    all_notes = []
    
    midi_data = pretty_midi.PrettyMIDI(filepath)
    for instrument in midi_data.instruments:
        all_notes.append(instrument.notes)
    
    return all_notes

def seperateInstrument(all_notes, instru):
    #piano (maybe)
    if instru == 0:
        return all_notes[0]
    #trumpet (mabye)
    if instru == 1:
        return all_notes[1]
    
def calculateLifetime(notes):
    all_lifetime = []
    
    for n in notes:
        #need to change into more readable data
        all_lifetime.append(float(n.end - n.start))

    return all_lifetime

def noteLifetime(note):
    return float(note.end - note.start)

def getStart(notes):
    all_starts = []
    
    for n in notes:
        #need to change into more readable data
        all_starts.append(float(n.start))
    
    return all_starts    
    
def getPitch(notes):
    all_pitch = []
    
    for n in notes:
        all_pitch.append(n.pitch)
    
    return all_pitch

def getVelocity(notes):
    all_velocity = []
    
    for n in notes:
        all_velocity.append(n.velocity)
        
    return all_velocity

def velocityRange(note):
    if note.velocity <= 65:
        return 2
    elif note.velocity <= 70:
        return 3
    elif note.velocity <= 75:
        return 4
    elif note.velocity <= 80:
        return 5

""" fonctions tests
notes = readMidi('Sounds/PinkPanther.midi')
instru = seperateInstrument(notes, 0)
tmp = getVelocity(instru)
print(tmp) """