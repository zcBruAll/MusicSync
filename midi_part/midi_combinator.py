import pretty_midi

def combine_midis(piano_file_path, trumpet_file_path, output_file_path):
    midi_files = [
        pretty_midi.PrettyMIDI(piano_file_path),
        pretty_midi.PrettyMIDI(trumpet_file_path)
    ]
    combined = pretty_midi.PrettyMIDI()

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
        combined.instruments.append(instrument)

    combined.write(output_file_path)