import pretty_midi
import matplotlib.pyplot as plt
import numpy as np

from collections import defaultdict

midi_ref = pretty_midi.PrettyMIDI('./Sounds/Ecossaise_Beethoven.mid')
midi_created = pretty_midi.PrettyMIDI('./Sounds.mid')
instruments = []

def pre_traitement_notes(notes_ref, notes_created, tol=0.05):
    """
    Associe chaque note du fichier créé avec une note du fichier de référence.
    Retourne un tableau de même taille que notes_created.
    """
    matched = []

    for note_c in notes_created:
        candidates = [n for n in notes_ref if abs(n.start - note_c.start) <= tol]

        if not candidates:
            best_ref = min(notes_ref, key=lambda n: abs(n.start - note_c.start))
        else:
            best_ref = min(candidates, key=lambda n: abs(n.pitch - note_c.pitch))

        matched.append(best_ref)

    return matched

def get_sum_pitch_difference(error_margin, midi_notes):
    return sum(abs(note.pitch - midi_notes[i].pitch) <= error_margin
            for i, note in enumerate(inst_created.notes))

overall_scores = []
w_pitch    = 0.4
w_notes    = 0.3
w_start    = 0.2
w_duration = 0.1

for inst_ref in midi_ref.instruments:
    inst_created = next((i for i in midi_created.instruments if i.program == inst_ref.program), None)

    if inst_created is None or len(inst_created.notes) == 0:
        continue

    ref_count = len(inst_ref.notes)
    created_count = len(inst_created.notes)
    score_notes = (created_count / ref_count) * 100

    
    equivalent_notes_midi = pre_traitement_notes(inst_ref.notes, inst_created.notes)
    note_pitch_exact = get_sum_pitch_difference(0, equivalent_notes_midi)
    note_pitch_at_1 = get_sum_pitch_difference(1, equivalent_notes_midi)
    note_pitch_at_12 = get_sum_pitch_difference(12, equivalent_notes_midi)
    score_pitch = (note_pitch_exact / created_count) * 100

    starts_difference = sum(abs(note.start - equivalent_notes_midi[i].start)
                            for i, note in enumerate(inst_created.notes))
    duration_difference = sum(abs((note.end - note.start) - (equivalent_notes_midi[i].end - equivalent_notes_midi[i].start))
                            for i, note in enumerate(inst_created.notes))
    avg_start_diff_ms = (starts_difference / created_count) * 1000  # en ms
    avg_duration_diff_ms = (duration_difference / created_count) * 1000
    score_start = max(0, 100 - (avg_start_diff_ms / 100 * 100))
    score_duration = max(0, 100 - (avg_duration_diff_ms / 1000 * 100))
    
    score_global = (
        w_notes     * score_notes +
        w_pitch     * score_pitch +
        w_start     * score_start +
        w_duration  * score_duration
    ) / (w_notes + w_pitch + w_start + w_duration)
    overall_scores.append((inst_ref.name, score_global))

    instruments.append((inst_ref.name, ref_count, created_count, note_pitch_exact, note_pitch_at_1, note_pitch_at_12, avg_start_diff_ms, avg_duration_diff_ms))

nbInst = len(instruments)

fig, axes = plt.subplots(3, nbInst+1, figsize=(6*(nbInst+1), 12))

if nbInst == 1:
    axes = axes.reshape(3, nbInst+1)

for j, (name, ref_count, created_count, _, _, _, _, _) in enumerate(instruments):
    ax = axes[0, j]
    pct = created_count * 100 / ref_count
    bars = ax.bar([f"{name}_ref", f"{name}_created"],
                  [ref_count, created_count],
                  color=["skyblue", "orange"])
    ax.set_title(f"{name} - Nb Notes")
    ax.set_ylabel("Notes")
    for bar, value in zip(bars, [ref_count, created_count]):
        txt = f"{value}\n({pct:.1f}%)" if value == created_count else f"{value}"
        ax.annotate(txt, xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                    xytext=(0,3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9)

# --- Ligne 1, dernière colonne : Décalage moyen des starts ---
ax_delay = axes[1, -1]
names = [d[0] for d in instruments]
delays_start = [d[6] for d in instruments]   # colonne 6 = avg_start_diff_ms
bars = ax_delay.bar(names, delays_start, color="purple")
ax_delay.set_title("Décalage moyen du début des notes (ms)")
ax_delay.set_ylabel("ms")
ax_delay.set_ylim(0, 100)  # fixe l'axe Y à 100ms
ax_delay.tick_params(axis='x', rotation=45)

for bar, val in zip(bars, delays_start):
    ax_delay.annotate(f"{val:.0f}ms",
                      xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                      xytext=(0,3), textcoords="offset points",
                      ha="center", va="bottom")

# --- Ligne 2, dernière colonne : Différence moyenne des durées ---
ax_duration = axes[0, -1]
names = [d[0] for d in instruments]
delays_duration = [d[7] for d in instruments]  # colonne 7 = avg_duration_diff_ms
bars = ax_duration.bar(names, delays_duration, color="red")
ax_duration.set_title("Différence moyenne de durée des notes (ms)")
ax_duration.set_ylabel("ms")
ax_duration.set_ylim(0, 1000)  # échelle plus large pour la durée
ax_duration.tick_params(axis='x', rotation=45)

for bar, val in zip(bars, delays_duration):
    ax_duration.annotate(f"{val:.0f}ms",
                         xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                         xytext=(0,3), textcoords="offset points",
                         ha="center", va="bottom")

for j, (name, _, created_count, pExact, p1, p12, _, _) in enumerate(instruments):
    ax = axes[1, j]
    bars = ax.bar(["Exact Pitch", "P@1", "P@12"], [pExact, p1, p12], color=["lightgreen", "skyblue", "salmon"])
    ax.set_ylim(0, created_count)
    ax.set_title(f"{name} - Pitch Accuracy")
    ax.set_ylabel("% correct")
    for bar, value in zip(bars, [pExact, p1, p12]):
        txt = f"{value}\n({((value* 100) / created_count):.1f}%)"
        ax.annotate(txt,
                    xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                    xytext=(0,3), textcoords="offset points",
                    ha="center", va="bottom")
   
ax_overall = axes[2, 0]     
names = [s[0] for s in overall_scores]
scores = [s[1] for s in overall_scores]

bars = ax_overall.bar(names, scores, color="green")
ax_overall.set_ylim(0, 100)
ax_overall.set_ylabel("%")
ax_overall.set_title("Matching global par instrument")

for bar, val in zip(bars, scores):
    ax_overall.annotate(f"{val:.1f}%",
                xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                xytext=(0,3), textcoords="offset points",
                ha="center", va="bottom")

plt.tight_layout()
plt.show()