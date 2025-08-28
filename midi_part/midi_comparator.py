import pretty_midi
import matplotlib.pyplot as plt

midi_ref = pretty_midi.PrettyMIDI('./Output/Ecossaise_Beethoven.mid')
midis_file_path = [
    './Output/Ecossaise_converted_1.mid',
    './Output/Ecossaise_converted_2.mid',
    './Output/detected_notes0.mid',
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
        self.avg_duration_diff = 0
        self.avg_start_diff = 0
        self.overall_score = 0
        self.color = None

def get_file_color(name):
    if name not in file_colors:
        idx = len(file_colors) % 10
        file_colors[name] = plt.cm.tab10(idx / 10)
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

def get_num_pitch_difference(error_margin, created_notes, matched_notes):
    """
    Retourne le nombre de notes qui ont + ou - une marge d'erreur de pitch
    """
    return sum(abs(created_notes[i].pitch - matched_notes[i].pitch) <= error_margin
              for i in range(len(created_notes)))

def plot_bar_with_annotations(ax, labels, values, title="", ylabel="", ylim=None, fmt="{:.0f}", colors=None):
    bars = ax.bar(labels, values, color=colors)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=6)

    for bar, val in zip(bars, values):
        ax.annotate(fmt.format(val),
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom")

def generate_nb_notes_graph(axes, midis):
    for j, (inst_name, files) in enumerate(midis.items()):
        if j >= axes.shape[1]:
            break
        
        ax = axes[0, j]
        
        # Créer une couleur pour la référence (gris)
        ref_color = 'lightgray'
        
        labels = [f"{inst_name}_ref"] + [f"{data.name}_created" for data in files]
        values = [files[0].ref_count] + [data.created_count for data in files]
        colors = [ref_color] + [data.color for data in files]

        plot_bar_with_annotations(ax, labels, values,
                                  title=f"{inst_name} - Nb Notes",
                                  ylabel="Notes", colors=colors)

def generate_avg_duration_diff_graph(axes, midis):
    # Utiliser la dernière colonne disponible
    col_idx = min(len(midis), axes.shape[1] - 1)
    ax = axes[0, col_idx]

    labels = []
    values = []
    colors = []

    for inst_name, files in midis.items():
        for data in files:
            labels.append(f"{inst_name}_{data.name}")
            values.append(data.avg_duration_diff)
            colors.append(data.color)

    plot_bar_with_annotations(
        ax, labels, values,
        title="Différence moyenne de durée des notes (ms)",
        ylabel="ms",
        ylim=(0, max(values) * 1.2 if values else 1000),
        fmt="{:.0f}ms",
        colors=colors
    )

def generate_avg_start_diff_graph(axes, midis):
    # Utiliser la dernière colonne disponible
    col_idx = min(len(midis), axes.shape[1] - 1)
    ax = axes[1, col_idx]

    labels = []
    values = []
    colors = []

    for inst_name, files in midis.items():
        for data in files:
            labels.append(f"{inst_name}_{data.name}")
            values.append(data.avg_start_diff)
            colors.append(data.color)

    plot_bar_with_annotations(
        ax, labels, values,
        title="Différence moyenne de début des notes (ms)",
        ylabel="ms",
        ylim=(0, max(values) * 1.2 if values else 100),
        fmt="{:.0f}ms",
        colors=colors
    )

def generate_pitch_graph(axes, midis):
    for j, (inst_name, files) in enumerate(midis.items()):
        if j >= axes.shape[1]:
            break

        ax = axes[1, j]

        labels, values, colors, data_refs = [], [], [], []

        # D'abord Exact
        for d in files:
            labels.append(f"{d.name}_Exact")
            values.append(d.pitch_exact)
            colors.append(d.color)
            data_refs.append(d)

        # Puis P@1
        for d in files:
            labels.append(f"{d.name}_P@1")
            values.append(d.pitch_at_1)
            colors.append(d.color)
            data_refs.append(d)

        plot_bar_with_annotations(
            ax, labels, values,
            title=f"{inst_name} - Pitch Accuracy",
            ylabel="Notes correctes",
            ylim=(0, d.ref_count),
            fmt="{:.0f}",
            colors=colors
        )

        # Annotation avec % en utilisant directement data_refs
        for bar, value, d in zip(ax.patches, values, data_refs):
            percent = (value * 100 / d.created_count) if d.created_count else 0
            ax.annotate(f"({percent:.1f}%)",
                        xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                        xytext=(0, 15), textcoords="offset points",
                        ha="center", va="bottom", fontsize=8)



def generate_overall_match_graph(axes, midis):
    for i, (inst_name, files) in enumerate(midis.items()):
        if i >= axes.shape[1]:
            break

        ax = axes[2, i]
        names = [data.name + '_' + inst_name for data in files]
        values = [data.overall_score for data in files]
        colors = [data.color for data in files]

        plot_bar_with_annotations(ax, names, values,
                                title="Matching global - " + inst_name,
                                ylabel="%",
                                ylim=(0, 100),
                                fmt="{:.1f}%",
                                colors=colors)

# Poids pour le calcul du score global
w_pitch = 0.4
w_notes = 0.3
w_start = 0.2
w_duration = 0.1

# Traitement des fichiers MIDI
for midi_path in midis_file_path:
    try:
        midi_data = pretty_midi.PrettyMIDI(midi_path)
        midi_name = midi_path.split('/')[-1].replace('.mid', '')

        for inst_ref in midi_ref.instruments:
            # Chercher l'instrument correspondant
            inst_created = None
            for inst in midi_data.instruments:
                if inst.program == inst_ref.program or inst.name == inst_ref.name:
                    inst_created = inst
                    break
            
            if not inst_created or not inst_created.notes:
                continue

            ref_notes = inst_ref.notes
            created_notes = inst_created.notes
            created_count = len(created_notes)
            ref_count = len(ref_notes)

            if created_count == 0:
                continue

            # Match des notes
            equivalent_notes_midi = pre_traitement_notes(ref_notes, created_notes)

            # Calcul des métriques
            score_notes = (created_count / ref_count * 100) if ref_count else 0

            note_pitch_exact = get_num_pitch_difference(0, created_notes, equivalent_notes_midi)
            note_pitch_at_1 = get_num_pitch_difference(1, created_notes, equivalent_notes_midi)
            note_pitch_at_12 = get_num_pitch_difference(12, created_notes, equivalent_notes_midi)
            score_pitch = (note_pitch_exact / created_count * 100) if created_count else 0

            starts_diff = sum(abs(created_notes[i].start - equivalent_notes_midi[i].start) 
                             for i in range(len(created_notes)))
            duration_diff = sum(abs((created_notes[i].end - created_notes[i].start) - 
                                   (equivalent_notes_midi[i].end - equivalent_notes_midi[i].start))
                               for i in range(len(created_notes)))

            avg_start_diff_ms = (starts_diff / created_count * 1000) if created_count else 0
            avg_duration_diff_ms = (duration_diff / created_count * 1000) if created_count else 0

            # Calcul des scores (limités entre 0 et 100)
            score_start = max(0, min(100, 100 - avg_start_diff_ms / 10))  # Ajusté la division
            score_duration = max(0, min(100, 100 - avg_duration_diff_ms / 100))  # Ajusté la division

            score_global = (
                w_notes * min(score_notes, 100) +
                w_pitch * score_pitch +
                w_start * score_start +
                w_duration * score_duration
            )

            # Création de l'objet FileData
            data = FileData(midi_name)
            data.created_count = created_count
            data.avg_duration_diff = avg_duration_diff_ms
            data.avg_start_diff = avg_start_diff_ms
            data.pitch_at_1 = note_pitch_at_1
            data.pitch_exact = note_pitch_exact
            data.ref_count = ref_count
            data.overall_score = score_global
            data.color = get_file_color(midi_name)
            
            midis.setdefault(inst_ref.name, []).append(data)

    except Exception as e:
        print(f"Erreur lors du traitement de {midi_path}: {e}")

# Vérification qu'il y a des données à traiter
if not midis:
    print("Aucune donnée à traiter. Vérifiez les chemins des fichiers MIDI.")
    exit()

# Création des graphiques
nbInst = len(midis.keys())
ncols = max(3, nbInst + 1)  # Au moins 3 colonnes

fig, axes = plt.subplots(3, ncols, figsize=(5*ncols, 12))

# S'assurer que axes est bien un tableau 2D
if len(axes.shape) == 1:
    axes = axes.reshape(3, ncols)

# Génération des graphiques
generate_nb_notes_graph(axes, midis)
generate_avg_duration_diff_graph(axes, midis)
generate_avg_start_diff_graph(axes, midis)
generate_pitch_graph(axes, midis)
generate_overall_match_graph(axes, midis)

# Masquer les axes inutilisés
for i in range(3):
    for j in range(ncols):
        if j >= nbInst and not (i == 0 and j == ncols-1) and not (i == 1 and j == ncols-1) and not (i == 2 and j == 0):
            axes[i, j].set_visible(False)

plt.tight_layout()
plt.show()