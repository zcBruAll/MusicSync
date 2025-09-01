import librosa
import mido
from collections import defaultdict
from mido import MidiFile, MidiTrack
import numpy as np

class NoteEvent:
    def __init__(self, note_name, isPiano, frequency, start_time, strength):
        self.note_name = note_name
        self.isPiano = isPiano
        self.frequency = frequency
        self.start_time = start_time
        self.end_time = start_time
        self.max_strength = strength
        self.last_seen_time = start_time
        self.is_active = True
    
    def update(self, time, strength):
        """Update note with new detection"""
        self.end_time = time
        self.last_seen_time = time
        self.max_strength = max(self.max_strength, strength)
    
    def get_duration(self):
        """Get note duration in seconds"""
        return self.end_time - self.start_time
    
    def __str__(self):
        return f"{self.note_name}: {self.start_time:.2f}s - {self.end_time:.2f}s ({self.get_duration():.2f}s)"

class NoteTracker:
    def __init__(self, smoothing_time=0.25, min_duration=0.1, detection_threshold=0.3):
        self.smoothing_time = smoothing_time
        self.min_duration = min_duration
        self.detection_threshold = detection_threshold
        self.active_notes = {}  # note_name -> NoteEvent
        self.completed_notes = []  # List of completed NoteEvent objects
        self.note_tolerance_hz = 5  # Hz tolerance for considering notes the same
    
    def _get_note_key(self, note_name, frequency):
        """Create a key for tracking notes, allowing for slight frequency variations"""
        # Round frequency to nearest 5 Hz to group similar frequencies
        rounded_freq = round(frequency / self.note_tolerance_hz) * self.note_tolerance_hz
        return f"{note_name}_{rounded_freq:.0f}"
    
    def update_note_tracker_with_prediction(self, current_time, detected_notes):
        """
        Enhanced update method that includes note onset prediction.
        Replace the existing update method in NoteTracker class.
        """
        # Convert to dict for easier lookup
        current_detections = {}
        for freq, strength, note_name, isPiano in detected_notes:
            if strength >= self.detection_threshold:
                key = self._get_note_key(note_name, freq)
                current_detections[key] = (note_name, isPiano, freq, strength)
        
        # Update existing notes or mark for potential closure
        notes_to_remove = []
        for key, note_event in self.active_notes.items():
            if key in current_detections:
                # Note is still being detected
                note_name, isPiano, freq, strength = current_detections[key]
                note_event.update(current_time, strength)
            else:
                # Note not detected this frame
                gap_duration = current_time - note_event.last_seen_time
                if gap_duration > self.smoothing_time:
                    # Gap is too long, close this note
                    note_event.is_active = False
                    if note_event.get_duration() >= self.min_duration:
                        self.completed_notes.append(note_event)
                    notes_to_remove.append(key)
        
        # Remove notes that have ended
        for key in notes_to_remove:
            del self.active_notes[key]
        
        # Add new notes with onset-based timing adjustment
        for key, (note_name, isPiano, freq, strength) in current_detections.items():
            if key not in self.active_notes:
                # Adjust start time if we're likely detecting late
                adjusted_start_time = current_time
                
                # Check if this might be a late detection by looking at strength
                if strength > self.detection_threshold * 1.5:  # Strong signal suggests we're late
                    adjusted_start_time = max(0, current_time - 0.05)  # Back-date by 50ms
                
                self.active_notes[key] = NoteEvent(note_name, isPiano, freq, adjusted_start_time, strength)
    
    def finalize(self, final_time):
        """Finalize all remaining active notes"""
        for note_event in self.active_notes.values():
            note_event.end_time = final_time
            note_event.is_active = False
            if note_event.get_duration() >= self.min_duration:
                self.completed_notes.append(note_event)
        self.active_notes.clear()
    
    def get_active_notes(self):
        """Get currently active notes"""
        return list(self.active_notes.values())
    
    def get_completed_notes(self):
        """Get all completed notes"""
        return self.completed_notes
    
    def export_to_midi(self, output_file, tempo_bpm=120, velocity_min=64, velocity_max=127, program=0):
        """
        Export detected notes to a MIDI file.
        
        Args:
            output_file: Path to output MIDI file
            tempo_bpm: Tempo in beats per minute
            velocity_min: Minimum MIDI velocity (for weakest notes)
            velocity_max: Maximum MIDI velocity (for strongest notes)
            program: MIDI program number (0 = Acoustic Grand Piano)
        """
        # Create MIDI file and track
        mid = MidiFile()
        track = MidiTrack()
        mid.tracks.append(track)
        
        # Set tempo (microseconds per beat)
        tempo = mido.bpm2tempo(tempo_bpm)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))
        
        # Set program (instrument)
        track.append(mido.Message('program_change', program=program, time=0))
        
        # Prepare all notes for MIDI export
        all_notes = [n for n in self.completed_notes.copy() if (program == 0 and n.isPiano) or (program != 0 and not n.isPiano)]
        
        # Add any remaining active notes (finalized)
        for note_event in self.active_notes.values():
            if ((program == 0 and note_event.isPiano) or (program != 0 and not note_event.isPiano)) and not note_event.is_active and note_event.get_duration() >= self.min_duration:
                all_notes.append(note_event)
        
        if not all_notes:
            print("No notes to export to MIDI.")
            return
        
        # Sort notes by start time
        all_notes.sort(key=lambda x: x.start_time)
        
        # Calculate velocity range
        if len(all_notes) > 1:
            strengths = [note.max_strength for note in all_notes]
            min_strength = min(strengths)
            max_strength = max(strengths)
            strength_range = max_strength - min_strength
        else:
            min_strength = max_strength = all_notes[0].max_strength
            strength_range = 1.0
        
        # Convert notes to MIDI events
        midi_events = []  # List of (time, event_type, midi_note, velocity)
        
        for note_event in all_notes:
            try:
                # Convert frequency to MIDI note number
                midi_note = int(round(librosa.hz_to_midi(note_event.frequency)))
                
                # Clamp to valid MIDI range
                midi_note = max(0, min(127, midi_note))
                
                # Calculate velocity based on note strength
                if strength_range > 0:
                    norm_strength = (note_event.max_strength - min_strength) / strength_range
                else:
                    norm_strength = 0.5
                
                velocity = int(velocity_min + norm_strength * (velocity_max - velocity_min))
                velocity = max(1, min(127, velocity))  # Ensure valid MIDI velocity
                
                # Add note on and note off events
                midi_events.append((note_event.start_time, 'note_on', midi_note, velocity))
                midi_events.append((note_event.end_time, 'note_off', midi_note, velocity))
                
            except Exception as e:
                print(f"Warning: Could not convert note {note_event.note_name} at {note_event.frequency:.1f} Hz to MIDI: {e}")
                continue
        
        if not midi_events:
            print("No valid MIDI events to export.")
            return
        
        # Sort events by time
        midi_events.sort(key=lambda x: x[0])
        
        # Convert to MIDI messages with proper timing
        current_time = 0.0
        ticks_per_second = mid.ticks_per_beat * (tempo_bpm / 60.0)
        
        for event_time, event_type, midi_note, velocity in midi_events:
            # Calculate delta time in ticks
            delta_time_sec = event_time - current_time
            delta_ticks = int(round(delta_time_sec * ticks_per_second))
            delta_ticks = max(0, delta_ticks)  # Ensure non-negative
            
            if event_type == 'note_on':
                track.append(mido.Message('note_on', note=midi_note, velocity=velocity, time=delta_ticks))
            elif event_type == 'note_off':
                track.append(mido.Message('note_off', note=midi_note, velocity=velocity, time=delta_ticks))
            
            current_time = event_time
        
        # Save MIDI file
        try:
            mid.save(output_file)
            print(f"\nMIDI file exported successfully: {output_file}")
            print(f"  - {len(all_notes)} notes exported")
            print(f"  - Tempo: {tempo_bpm} BPM")
            print(f"  - Program: {program}")
            print(f"  - Velocity range: {velocity_min}-{velocity_max}")
            print(f"  - Duration: {max(note.end_time for note in all_notes):.2f} seconds")
        except Exception as e:
            print(f"Error saving MIDI file: {e}")
    
    def print_note_summary(self):
        """Print summary of all detected notes"""
        print("\n" + "="*60)
        print("NOTE TIMING SUMMARY")
        print("="*60)
        
        all_notes = self.completed_notes + [n for n in self.active_notes.values() if not n.is_active]
        all_notes.sort(key=lambda x: x.start_time)
        
        if not all_notes:
            print("No notes detected with sufficient duration.")
            return
        
        print(f"Total notes detected: {len(all_notes)}")
        print(f"Time range: {all_notes[0].start_time:.2f}s - {all_notes[-1].end_time:.2f}s")
        print("\nDetailed note list:")
        print("-" * 60)
        
        for i, note in enumerate(all_notes, 1):
            print(f"{i:2d}. {note}")
        
        # Statistics by note name
        note_stats = defaultdict(list)
        for note in all_notes:
            note_stats[note.note_name].append(note.get_duration())
        
        print("\nNote statistics:")
        print("-" * 30)
        for note_name, durations in sorted(note_stats.items()):
            avg_duration = np.mean(durations)
            total_duration = sum(durations)
            count = len(durations)
            print(f"{note_name:>6s}: {count:2d} occurrences, avg {avg_duration:.2f}s, total {total_duration:.2f}s")
