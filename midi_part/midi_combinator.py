import pretty_midi

midi_files = [
    pretty_midi.PrettyMIDI('./Output/Im_Ecossaise_piano.mid'),
    pretty_midi.PrettyMIDI('./Sounds/Im_Ecossaise_trumpet.mid')
]
midi = pretty_midi.PrettyMIDI()

for midi_file in midi_files:
    instrument = pretty_midi.Instrument(program=midi_file.instruments[0].program)
    for note in midi_file.instruments[0].notes:
        midi_note = pretty_midi.Note(
            velocity=note.velocity,
            pitch=note.pitch,
            start=note.start,
            end=note.end
        )
        instrument.notes.append(midi_note)
    midi.instruments.append(instrument)
    
output_filename = f"./Output/Ecossaise_converted.mid"

midi_file.write(output_filename)