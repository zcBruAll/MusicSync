import pretty_midi
import matplotlib.pyplot as plt

midi_ref = pretty_midi.PrettyMIDI('./Output/Ecossaise_Beethoven.mid')
midis_file_path = [
        './Output/Ecossaise_converted.mid',
        './Output/Ecossaise_Piano.mid'
    ]
instruments = []
midis = {}
file_colors = {}

class FileData:
    def __init__(self, name):
        self.name = name
        self.ref_count = 0
        self.created_count = 0
        self.pitch_exact = 0
        self.pitch_at_1 = 0
        self.pitch_at_12 = 0
        self.avg_duration_diff = 0
        self.avg_start_diff = 0
        self.overall_score = 0
        self.color = None

def get_file_color(name):
    if name not in file_colors:
        idx = len(file_colors) % 10  # boucle dans tab10
        file_colors[name] = plt.cm.tab10(idx / 10)  # normalisation [0,1]
    return file_colors[name]

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
    
def plot_bar_with_annotations(ax, labels, values, title="", ylabel="", ylim=None, fmt="{:.0f}", colors=None):
    bars = ax.bar(labels, values, color=colors)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=6)  # taille des labels X

    for bar, val in zip(bars, values):
        ax.annotate(fmt.format(val),
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom")

def generate_nb_notes_graph():
    for j, (inst_name, files) in enumerate(midis.items()):
        files = midis.get(inst_name)
        if not files:
            continue

        ax = axes[0, j]
        labels = [f"{inst_name}_ref"] + [f"{data.name}_created" for data in files]
        values = [files[0].ref_count] + [data.created_count for data in files]
        colors = [data.color for data in files]

        # Générer autant de couleurs que de labels
        plot_bar_with_annotations(ax, labels, values,
                                  title=f"{inst_name} - Nb Notes",
                                  ylabel="Notes",colors=colors)

def generate_avg_duration_diff_graph():
    ax = axes[0, -1]

    labels = []
    values = []

    for inst_name, files in midis.items():
        labels = [f"{inst_name}_{data.name}" for data in files]
        values = [data.avg_duration_diff for data in files]
        colors = [data.color for data in files]

    plot_bar_with_annotations(
        ax, labels, values,
        title="Différence moyenne de durée des notes (ms)",
        ylabel="ms",
        ylim=(0, 1000),
        fmt="{:.0f}ms",
        colors=colors
    )

def generate_avg_start_diff_graph():
    ax = axes[1, -1]

    labels = []
    values = []

    for inst_name, files in midis.items():
        labels = [f"{inst_name}_{data.name}" for data in files]
        values = [data.avg_start_diff for data in files]
        colors = [data.color for data in files]

    plot_bar_with_annotations(
        ax, labels, values,
        title="Différence moyenne de début des notes (ms)",
        ylabel="ms",
        ylim=(0, 100),
        fmt="{:.0f}ms",
        colors=colors
    )

def generate_pitch_graph():
    for j, (inst_name, files) in enumerate(midis.items()):
        ax = axes[1, j]

        labels = []
        values = []
        colors = []

        for data in files:
            labels.extend([f"{data.name}_Exact", f"{data.name}_P@1", f"{data.name}_P@12"])
            values.extend([data.pitch_exact, data.pitch_at_1, data.pitch_at_12])
            colors.extend(data.color)  # Répéter la couleur pour chaque barre

        plot_bar_with_annotations(ax, labels, values,
                                  title=f"{inst_name} - Pitch Accuracy",
                                  ylabel="Notes correctes",
                                  ylim=(0, max(values) * 1.1),
                                  fmt="{:.0f}")

        # Affichage aussi en %
        for idx, (bar, value) in enumerate(zip(ax.patches, values)):
            # retrouver le created_count du bon fichier
            file_index = idx // 3  # car 3 barres par fichier
            data = files[file_index]

            percent = (value * 100 / data.created_count) if data.created_count else 0
            ax.annotate(f"({percent:.1f}%)",
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                        xytext=(0, 15), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8)

def generate_overall_match_graph():
    ax = axes[2, 0]
    names = [data.name + '_' + inst_name for inst_name, files in midis.items() for data in files]
    values = [data.overall_score for files in midis.values() for data in files]
    colors = [data.color for files in midis.values() for data in files]
    plot_bar_with_annotations(ax, names, values,
                              title="Matching global par instrument",
                              ylabel="%",
                              ylim=(0, 100),
                              fmt="{:.1f}%",
                              colors=colors)
    
"""
Tableau qui contient le score en % d'à quel point l'instrument est proche du fichier de référence
Les 4 variables du dessous contiennet le poids de chaque éléments sur le score final
"""
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
for midi in midis_file_path:
    midi_data = pretty_midi.PrettyMIDI(midi)
    midi_name = midi.split('/')[-1]

    for inst_ref in midi_ref.instruments:
        inst_created = next((i for i in midi_data.instruments if i.program == inst_ref.program), None)
        if not inst_created or not inst_created.notes:
            continue

        ref_notes = inst_ref.notes
        created_notes = inst_created.notes
        created_count = len(created_notes)

        # Match des notes
        equivalent_notes_midi = pre_traitement_notes(ref_notes, created_notes)

        # Scores
        ref_count = len(ref_notes)
        score_notes = (created_count / ref_count * 100) if ref_count else 0

        note_pitch_exact = get_num_pitch_difference(0, equivalent_notes_midi)
        note_pitch_at_1 = get_num_pitch_difference(1, equivalent_notes_midi)
        note_pitch_at_12 = get_num_pitch_difference(12, equivalent_notes_midi)
        score_pitch = (note_pitch_exact / created_count * 100) if created_count else 0

        starts_diff = sum(abs(n.start - equivalent_notes_midi[i].start) for i, n in enumerate(created_notes))
        duration_diff = sum(abs((n.end - n.start) - (equivalent_notes_midi[i].end - equivalent_notes_midi[i].start))
                            for i, n in enumerate(created_notes))

        avg_start_diff_ms = (starts_diff / created_count * 1000) if created_count else 0
        avg_duration_diff_ms = (duration_diff / created_count * 1000) if created_count else 0

        score_start = max(0, 100 - avg_start_diff_ms / 100 * 100)
        score_duration = max(0, 100 - avg_duration_diff_ms / 1000 * 100)

        score_global = (
            w_notes    * score_notes +
            w_pitch    * score_pitch +
            w_start    * score_start +
            w_duration * score_duration
        ) / (w_notes + w_pitch + w_start + w_duration)

        data = FileData(midi_name)
        data.created_count = created_count
        data.avg_duration_diff = avg_duration_diff_ms
        data.avg_start_diff = avg_start_diff_ms
        data.pitch_at_1 = note_pitch_at_1
        data.pitch_at_12 = note_pitch_at_12
        data.pitch_exact = note_pitch_exact
        data.ref_count = ref_count
        data.overall_score = score_global
        data.color = get_file_color(midi_name)
        midis.setdefault(inst_ref.name, []).append(data)

nbInst = len(midis.keys())

fig, axes = plt.subplots(3, 3, figsize=(5*(nbInst+1), 12))

if nbInst == 1:
    axes = axes.reshape(3, 3)

generate_nb_notes_graph()
generate_avg_duration_diff_graph()
generate_avg_start_diff_graph()
generate_pitch_graph()
generate_overall_match_graph()

plt.tight_layout()
plt.show()