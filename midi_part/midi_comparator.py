import pretty_midi
import matplotlib.pyplot as plt

midi_ref = pretty_midi.PrettyMIDI('./Output/Ecossaise_Beethoven.mid')
midis_created = pretty_midi.PrettyMIDI('./Output/Ecossaise_converted.mid')
instruments = []
midis = []

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

def get_num_pitch_difference(error_margin, midi_notes):
    """
    Retourne le nombre de note qui ont + ou - une marge d'erreur de pitch
    error_margin à 0 : Les notes qui sont exacts au fichier référence
    error_margin: à 1 : Les notes qui ont + ou - 1 demi-ton de différence avec le fichier de référence
    """
    return sum(abs(note.pitch - midi_notes[i].pitch) <= error_margin
            for i, note in enumerate(inst_created.notes))
    
def plot_bar_with_annotations(ax, labels, values, title="", ylabel="", colors=None, ylim=None, fmt="{:.0f}"):
    bars = ax.bar(labels, values, color=colors)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    ax.tick_params(axis='x', rotation=45)

    for bar, val in zip(bars, values):
        ax.annotate(fmt.format(val),
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom")

def generate_nb_notes_graph():
    for j, (name, ref_count, created_count, _, _, _, _, _) in enumerate(instruments):
        ax = axes[0, j]
        pct = created_count * 100 / ref_count
        labels = [f"{name}_ref", f"{name}_created"]
        values = [ref_count, created_count]
        colors = ["skyblue", "orange"]
        plot_bar_with_annotations(ax, labels, values,
                                title=f"{name} - Nb Notes",
                                ylabel="Notes",
                                colors=colors,
                                fmt="{:.0f}")          
        # ax.annotate(f"{created_count}\n({pct:.1f}%)",
        #             xy=(ax.patches[1].get_x() + ax.patches[1].get_width()/2, created_count),
        #             xytext=(0, 3), textcoords="offset points",
        #             ha="center", va="bottom", fontsize=9)    

def generate_avg_duration_diff_graph():
    ax = axes[0, -1]
    names = [d[0] for d in instruments]
    values = [d[7] for d in instruments]
    plot_bar_with_annotations(ax, names, values,
                              title="Différence moyenne de durée des notes (ms)",
                              ylabel="ms",
                              colors="red",
                              ylim=(0, 1000),
                              fmt="{:.0f}ms")

def generate_avg_start_diff_graph():
    ax = axes[1, -1]
    names = [d[0] for d in instruments]
    values = [d[6] for d in instruments]
    plot_bar_with_annotations(ax, names, values,
                              title="Décalage moyen du début des notes (ms)",
                              ylabel="ms",
                              colors="purple",
                              ylim=(0, 100),
                              fmt="{:.0f}ms")

def generate_pitch_graph():
    for j, (name, _, created_count, pExact, p1, p12, _, _) in enumerate(instruments):
        ax = axes[1, j]
        labels = ["Exact Pitch", "P@1", "P@12"]
        values = [pExact, p1, p12]
        colors = ["lightgreen", "skyblue", "salmon"]
        plot_bar_with_annotations(ax, labels, values,
                                  title=f"{name} - Pitch Accuracy",
                                  ylabel="% correct",
                                  colors=colors,
                                  ylim=(0, created_count),
                                  fmt="{:.0f}")
        # Affichage aussi en %
        for bar, value in zip(ax.patches, values):
            ax.annotate(f"({(value*100)/created_count:.1f}%)",
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                        xytext=(0, 15), textcoords="offset points",
                        ha="center", va="bottom")

def generate_overall_match_graph():
    ax = axes[2, 0]
    names = [s[0] for s in overall_scores]
    values = [s[1] for s in overall_scores]
    plot_bar_with_annotations(ax, names, values,
                              title="Matching global par instrument",
                              ylabel="%",
                              colors="green",
                              ylim=(0, 100),
                              fmt="{:.1f}%")
    
"""
Tableau qui contient le score en % d'à quel point l'instrument est proche du fichier de référence
Les 4 variables du dessous contiennet le poids de chaque éléments sur le score final
"""
overall_scores = []
w_pitch    = 0.4
w_notes    = 0.3
w_start    = 0.2
w_duration = 0.1

"""
Boucle sur chaque instrument du midi de référence et vérifie si l'instrument est bien dans le fichier midi créé

Calcul toutes les statistiques nécessaires à la bonne comparaison des fichiers

On effectue un pré-traitement des notes du fichier référence afin d'avoir le même nombre de note que le fichier créé pour 
pouvoir effectuer les différents calculs
"""
for inst_ref in midi_ref.instruments:
    inst_created = next((i for i in midis_created.instruments if i.program == inst_ref.program), None)

    if inst_created is None or len(inst_created.notes) == 0:
        continue
    
    equivalent_notes_midi = pre_traitement_notes(inst_ref.notes, inst_created.notes)

    ref_count = len(inst_ref.notes)
    created_count = len(inst_created.notes)
    score_notes = (created_count / ref_count) * 100
    
    note_pitch_exact = get_num_pitch_difference(0, equivalent_notes_midi)
    note_pitch_at_1 = get_num_pitch_difference(1, equivalent_notes_midi)
    note_pitch_at_12 = get_num_pitch_difference(12, equivalent_notes_midi)
    score_pitch = (note_pitch_exact / created_count) * 100

    """
    Récupération de la somme des décalage de start pour chaque notes
    
    Récupération de la somme des décalage de durée pour chaque notes
    
    Calcul à la fin de la moyenne de décalage en miliseconde
    """
    starts_difference = sum(abs(note.start - equivalent_notes_midi[i].start)
                            for i, note in enumerate(inst_created.notes))
    duration_difference = sum(abs((note.end - note.start) - (equivalent_notes_midi[i].end - equivalent_notes_midi[i].start))
                            for i, note in enumerate(inst_created.notes))
    avg_start_diff_ms = (starts_difference / created_count) * 1000
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

generate_nb_notes_graph()
# generate_avg_duration_diff_graph()
# generate_avg_start_diff_graph()
# generate_pitch_graph()
# generate_overall_match_graph()

plt.tight_layout()
plt.show()