import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json
from copy import deepcopy
from matplotlib.figure import Figure
import scipy.stats as stats

PLAYER_MODE = 0
# eeg data analysis
# csv contains 2 second window with each channel showing its frequency and power i think

# epoch, channel1_frequency1, channel1_frequency2, channel1_frequency3, channel2f_requency1, ... , Game_Modality, Game_Action, Game_Performance
# epoch1, channel1frequency1power, channel1frequency2power,...                                   , none, none, none
# epoch2, channel1frequency1power, channel1frequency2power, channel1frequency3power, channel2frequency1power, ..., audio, missed, INATTENTION_ERROR
#

# process csv to turn into df
# pd.read_csv('eeg_data.csv')  # Replace with your actual CSV file path
# then calculate engagement index tbr, tar, and frontal alpha asymmetry

# all calculate functions return a pandas dataframe with epoch and the value at each epoch
# thus can then give someone their average value over whole session, or plot the value over time to see how it changes
# also can plot it against game data to see how it changes with game events


# task engagement index per timestamp:
# channels Fz, Cz, Pz
# return pandas dataframe with columns: time, engagement_index
def calculate_task_engagement(df, channels=['Fz', 'Cz', 'Pz']):

    # find the beta power column in each channel with this block of code:
    # basically make the column names what they are in the dataframe
    beta_columns = []
    for ch in channels:
        beta_columns.append(f"{ch}_Beta")

    # find alpha power
    alpha_columns = []
    for ch in channels:
        alpha_columns.append(f"{ch}_Alpha")

    # find theta power
    theta_columns = []
    for ch in channels:
        theta_columns.append(f"{ch}_Theta")

    # averages beta, alpha, and theta power across all chosen channels
    # average beta power across all chosen channels
    beta_power = df[beta_columns].mean(axis=1)
    # average alpha power across all chosen channels
    alpha_power = df[alpha_columns].mean(axis=1)
    # average theta power across all chosen channels
    theta_power = df[theta_columns].mean(axis=1)

    result = pd.DataFrame({
        'Epoch': df['Epoch'],  # whatever its called in the file we are given
        # task engagement index
        'tei': beta_power / (alpha_power + theta_power + 1e-10)
    })

    return result


def calculate_tbr(df, channels):

    # find theta columns
    theta_columns = []
    for ch in channels:
        theta_columns.append(f"{ch}_Theta")

    # find beta columns
    beta_columns = []
    for ch in channels:
        beta_columns.append(f"{ch}_Beta")

    # average theta power across all chosen channels
    theta_power = df[theta_columns].mean(axis=1)
    # average beta power across all chosen channels
    beta_power = df[beta_columns].mean(axis=1)

    result = pd.DataFrame({
        'Epoch': df['Epoch'],  # whatever its called in the file we are given
        'tbr': theta_power / (beta_power + 1e-10)  # theta/beta ratio
    })

    return result


# channels1 is frontal channels for theta, channels 2 is parietal channels for alpha
def calculate_tar(df, channels1=['Fz', 'F3', 'F4'], channels2=['Pz', 'P3', 'P4']):
    theta_columns = []
    for ch in channels1:
        theta_columns.append(f"{ch}_Theta")

    alpha_columns = []
    for ch in channels2:
        alpha_columns.append(f"{ch}_Alpha")

    # average theta power across all chosen channels
    theta_power = df[theta_columns].mean(axis=1)
    alpha_power = df[alpha_columns].mean(axis=1)  # average alpha power across

    result = pd.DataFrame({
        'Epoch': df['Epoch'],  # whatever its called in the file we are given
        'tar': theta_power / (alpha_power + 1e-10)  # theta/alpha ratio
    })

    return result


# calculate frontal alpha asymmetry, channels1 is left hemisphere, channels2 is right hemisphere
def calculate_faa(df, channels1=['F3'], channels2=['F4']):
    alpha_columns1 = []
    for ch in channels1:
        alpha_columns1.append(f"{ch}_Alpha")

    alpha_columns2 = []
    for ch in channels2:
        alpha_columns2.append(f"{ch}_Alpha")

    # average alpha power across all chosen channels
    alpha_power1 = df[alpha_columns1].mean(axis=1)
    # average alpha power across all chosen channels
    alpha_power2 = df[alpha_columns2].mean(axis=1)

    result = pd.DataFrame({
        'Epoch': df['Epoch'],  # whatever its called in the file we are given
        # frontal alpha asymmetry
        'faa': np.log(alpha_power1 + 1e-10) - np.log(alpha_power2 + 1e-10)
    })

    return result


def get_beta(df, channels):
    beta_columns = []
    for ch in channels:
        beta_columns.append(f"{ch}_Beta")

    beta_power = df[beta_columns].mean(axis=1)

    result = pd.DataFrame({
        'Epoch': df['Epoch'],
        'beta': beta_power
    })
    return result


def plot_ratio_over_time(df, ratio_column):
    plt.figure(figsize=(10, 6))
    plt.plot(df['Epoch'], df[ratio_column], label=ratio_column, color='blue')
    plt.xlabel('Epochs')
    plt.ylabel(ratio_column)
    plt.title(f'{ratio_column} Over Time')
    plt.legend()
    plt.grid()
    plt.show()


# plot task engagement over time
def plot_task_engagement(tei_df):
    plt.figure(figsize=(10, 6))
    plt.plot(tei_df['Epoch'], tei_df['tei'],
             label='Task Engagement Index', color='blue')
    plt.xlabel('Epochs')
    plt.ylabel('Task Engagement Index')
    plt.title('Task Engagement Index Over Time')
    plt.legend()
    plt.grid()
    plt.show()


# game data analysis
# csv has columns: epoch,modality,action,Game_Performance
# accuracy = number of correct actions / total actions
def _performance_counts(df):
    """Return correct and total response counts for each EEG epoch."""
    valid_outcomes = {'CORRECT_HIT', 'INATTENTION_ERROR', 'IMPULSIVITY_ERROR'}

    def count_outcomes(value):
        outcomes = str(value).split(' | ')
        correct_count = sum(outcome == 'CORRECT_HIT' for outcome in outcomes)
        total_count = sum(outcome in valid_outcomes for outcome in outcomes)
        return correct_count, total_count

    counts = df['Game_Performance'].map(count_outcomes)
    return (
        counts.map(lambda count: count[0]).astype(int),
        counts.map(lambda count: count[1]).astype(int),
    )


def calculate_dprime(df):
    """Calculate d' (d-prime) for signal detection theory:
    d' = Z(hit rate) - Z(false alarm rate)
    Uses the log-linear correction (Hautus, 1995) applied to counts,
    so it's well-defined even at 0% or 100% rates or zero trials.
    """
    hits = len(df[df['Game_Performance'] == 'CORRECT_HIT'])
    false_alarms = len(df[df['Game_Performance'] == 'IMPULSIVITY_ERROR'])
    misses = len(df[df['Game_Performance'] == 'INATTENTION_ERROR'])

    # Correct Rejections: everything else (rows where nothing went wrong
    # and no target was missed)
    total_events = hits + false_alarms + misses
    correct_rejections = len(df) - total_events

    if correct_rejections < 0:
        raise ValueError(
            f"correct_rejections came out negative ({correct_rejections}); "
            "Game_Performance values don't add up to len(df) — check for "
            "unexpected labels in the column."
        )

    n_targets = hits + misses
    n_nontargets = false_alarms + correct_rejections

    if n_targets == 0 or n_nontargets == 0:
        # No target trials or no non-target trials in this window —
        # d' isn't meaningfully defined.
        return float('nan')

    # Log-linear correction applied to counts (avoids 0/1 rates and
    # divide-by-zero entirely, no special-casing needed)
    hit_rate = (hits + 0.5) / (n_targets + 1)
    fa_rate = (false_alarms + 0.5) / (n_nontargets + 1)

    d_prime = stats.norm.ppf(hit_rate) - stats.norm.ppf(fa_rate)

    return d_prime


def calculate_accuracy(df):
    correct_counts, total_counts = _performance_counts(df)
    total_actions = total_counts.sum()
    correct_actions = correct_counts.sum()
    accuracy = correct_actions / total_actions if total_actions > 0 else 0
    return accuracy


def running_accuracy(df):
    correct_counts, total_counts = _performance_counts(df)
    running_accuracy = (
        correct_counts.cumsum() / total_counts.cumsum().replace(0, np.nan)
    ).ffill().fillna(0) * 100

    result = pd.DataFrame({
        'Epoch': df['Epoch'],
        'running_accuracy': running_accuracy
    })
    return result


def rolling_average_accuracy(df, window_size=4):
    correct_counts, total_counts = _performance_counts(df)
    rolling_correct = correct_counts.rolling(
        window=window_size, min_periods=1).sum()
    rolling_total = total_counts.rolling(
        window=window_size, min_periods=1).sum().replace(0, np.nan)
    result = pd.DataFrame({
        'Epoch': df['Epoch'],
        'rolling_average_accuracy': (rolling_correct / rolling_total).ffill().fillna(0) * 100
    })
    return result


def plot_all_ratios(tei_df, tbr_df, tar_df):
    plt.figure(figsize=(10, 6))
    plt.plot(tei_df['Epoch'], tei_df['tei'],
             label='Task Engagement Index', color='blue')
    plt.plot(tbr_df['Epoch'], tbr_df['tbr'],
             label='Theta Beta Ratio', color='red')
    plt.plot(tar_df['Epoch'], tar_df['tar'],
             label='Theta Alpha Ratio', color='green')
    plt.xlabel('Epochs')
    plt.ylabel('Ratios')
    plt.title('Ratios Over Time')
    plt.legend()
    plt.grid()
    plt.show()


def plot_both_accuracies_matplotlib(running_accuracy_df, rolling_average_accuracy_df):
    plt.figure(figsize=(10, 6))
    plt.plot(running_accuracy_df['Epoch'], running_accuracy_df['running_accuracy'],
             label='Running Accuracy', color='blue')
    plt.plot(rolling_average_accuracy_df['Epoch'], rolling_average_accuracy_df['rolling_average_accuracy'],
             label='Rolling Average Accuracy', color='orange')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy (%)')
    plt.title('Running and Rolling Average Accuracy Over Time')
    plt.legend()
    plt.grid()
    plt.show()


def plot_both_accuracies(running_accuracy_df, rolling_average_accuracy_df):
    # 1. Create an explicit Figure object instead of using plt.figure()
    fig = Figure(figsize=(10, 6), dpi=100)
    fig.patch.set_facecolor("#2b2b2b")
    fig.patch.set_edgecolor("#2b2b2b")
    fig.patch.set_linewidth(0)
    ax = fig.add_subplot(111)

    # customize the graph's appearance to match the dark theme
    ax.set_facecolor("#2b2b2b")
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color("#50B5CA")

    # 2. Plot on the explicit axis (ax) instead of pyplot (plt)
    ax.plot(running_accuracy_df['Epoch'], running_accuracy_df['running_accuracy'],
            label='Running Accuracy', color="#50B5CA", linewidth=2, marker='o')
    ax.plot(rolling_average_accuracy_df['Epoch'], rolling_average_accuracy_df['rolling_average_accuracy'],
            label='Rolling Average Accuracy', color="#FF9900", linewidth=2, marker='o')
    ax.fill_between(
        running_accuracy_df['Epoch'], running_accuracy_df['running_accuracy'], color="#50B5CA", alpha=0.1)
    ax.fill_between(rolling_average_accuracy_df['Epoch'],
                    rolling_average_accuracy_df['rolling_average_accuracy'], color="#FF9900", alpha=0.1)

    ax.set_xlabel('Epochs', color='white', fontsize=12,
                  fontname='Comic Sans MS')
    ax.set_ylabel('Accuracy (%)', color='white',
                  fontsize=12, fontname='Comic Sans MS')
    ax.set_title('Running and Rolling Average Accuracy Over Time',
                 color='white', fontsize=16, fontname='Comic Sans MS')
    ax.legend()
    ax.grid(True)

    # 3. Return the figure so the GUI can capture it
    return fig

# df1 is tei, df2 is tbr, df3 is tar


def plot_eeg_data(df1, df2, df3):
    # 1. Create an explicit Figure object instead of using plt.figure()
    fig = Figure(figsize=(10, 6), dpi=100)
    fig.patch.set_facecolor("#2b2b2b")
    fig.patch.set_edgecolor("#2b2b2b")
    fig.patch.set_linewidth(0)
    ax = fig.add_subplot(111)

    # customize the graph's appearance to match the dark theme
    ax.set_facecolor("#2b2b2b")
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color("#50B5CA")

    # 2. Plot on the explicit axis (ax) instead of pyplot (plt)
    ax.plot(df1['Epoch'], df1['tei'], label='TEI',
            color="#50B5CA", linewidth=2, marker='o')
    ax.fill_between(df1['Epoch'], df1['tei'], color="#50B5CA", alpha=0.1)

    ax.plot(df2['Epoch'], df2['tbr'], label='TBR',
            color="#FF9900", linewidth=2, marker='o')
    ax.fill_between(df2['Epoch'], df2['tbr'], color="#FF9900", alpha=0.1)

    ax.plot(df3['Epoch'], df3['tar'], label='TAR',
            color="#FF5555", linewidth=2, marker='o')
    ax.fill_between(df3['Epoch'], df3['tar'], color="#FF5555", alpha=0.1)

    ax.set_xlabel('Epochs', color='white', fontsize=12,
                  fontname='Comic Sans MS')
    ax.set_ylabel("Ratio", color='white',
                  fontsize=12, fontname='Comic Sans MS')
    ax.set_title(f'EEG Ratios Over Time', color='white',
                 fontsize=16, fontname='Comic Sans MS')
    ax.legend()
    ax.grid(True)

    return fig


def decide_game_state(config, dprime, beta_df, tar, baseline_beta_df, baseline_tar_df):
    highdprime = False
    hightar = False
    lowtar = False
    betatrend = 0  # 0 stable, 1 increase, 2 decrease
    lowbeta = False
    new_config = deepcopy(config)

    # calculate high and low value for tar based on baseline_tar_df, if the average tar is more than 2 standard deviations above the mean of baseline_tar_df, then high tar, if less than 2 standard deviations below the mean of baseline_tar_df, then low tar
    baseline_tar_mean = baseline_tar_df['tar'].mean()
    baseline_tar_std = baseline_tar_df['tar'].std()
    if tar > baseline_tar_mean + 2 * baseline_tar_std:
        hightar = True
    elif tar < baseline_tar_mean - 2 * baseline_tar_std:
        lowtar = True

    if dprime > 1.5:
        highdprime = True
    if beta_df['beta'].mean() < baseline_beta_df['baseline_beta'].mean():
        lowbeta = True
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        beta_df['Epoch'], beta_df['beta']
    )
    if p_value < 0.05:
        betatrend = 1 if slope > 0 else 2
    else:
        betatrend = 0

    print(betatrend)
    print(hightar)
    print(highdprime)
    print(lowtar)
    print(lowbeta)

    if hightar and betatrend == 0 and highdprime:
        playerstate = "optimal"

    elif hightar and betatrend == 2 and not highdprime:
        playerstate = "overload"

    elif lowtar and highdprime:
        playerstate = "bored"

    elif lowtar and lowbeta:
        playerstate = "abandoned"

    else:
        playerstate = "normal"

    
    if playerstate == "optimal":
        # increase n
        if new_config["n_back"] < 4:
            new_config["n_back"] += 1
        else:
            pass
    print(playerstate)
    if playerstate == "overload":
        if new_config["use_audio"]:
            new_config["use_audio"] = False
        elif new_config["use_color"]:
            new_config["use_color"] = False
        # dont reduce n back unless everything else is already off, and n back is greater than 2
        elif new_config["n_back"] > 2:
            new_config["n_back"] -= 1
        else:
            # already at easiest setting
            new_config["use_audio"] = False
            new_config["use_color"] = False
            new_config["n_back"] = 2

    if playerstate == "bored":
        if not new_config["use_color"]:
            new_config["use_color"] = True
        elif not new_config["use_audio"]:
            new_config["use_audio"] = True
        elif new_config["n_back"] < 4:
            new_config["n_back"] += 1
        else:
            new_config["n_back"] += 1

    if playerstate == "abandoned":
        # decrease n back first, and then turn off color and audio if n back is already at 2
        if new_config["n_back"] > 2:
            new_config["n_back"] -= 1
        elif new_config["use_color"]:
            new_config["use_color"] = False
        elif new_config["use_audio"]:
            new_config["use_audio"] = False
        else:
            # already at easiest setting
            new_config["use_audio"] = False
            new_config["use_color"] = False
            new_config["n_back"] = 2

    else:
        # do nothing keep config the same
        pass
    PLAYER_MODE = 1
    return new_config


# update the game state
def update_game_state(FILE_PATH):
    # Read the JSON file
    try:
        with open(FILE_PATH, "r") as f:
            gamestate = json.load(f)
    except FileNotFoundError:
        # If the file doesn't exist, bleh
        print(f"[ERROR] game_state.json not found.")

    # game_state is json file containing:
        # config, use_space/use_audio/use_color:true or false, n-back: number
        # dprime_accuracy, beta_power, tar_ratio, tei_index, tbr_ratio
        # baseline eeg data


    tar_df = pd.Series(gamestate["tar"]["tar"], name="tar").to_frame()
    beta_df = pd.DataFrame(gamestate["beta"])
    # baseline beta, make sure this is from the game that starts after the 60 sec
    # make baseline tar also from game that starts after 60 sec
    baseline_beta_df = pd.DataFrame(gamestate["baseline_beta"])
    baseline_beta_df = baseline_beta_df.rename(
        columns={"beta": "baseline_beta"})
    baseline_tar_df = pd.Series(
        gamestate["baseline_tar"]["tar"], name="tar").to_frame()
    dprime = gamestate["dprime"]
    avg_tar = tar_df['tar'].mean()
    config = gamestate["config"]

    new_config = decide_game_state(
        config, dprime, beta_df, avg_tar, baseline_beta_df, baseline_tar_df)

    gamestate["config"] = new_config
    
    with open(FILE_PATH, "w") as f:
        json.dump(gamestate, f, indent=4)

    return


# what if we have an attention/challenged score based on tar, beta, and maybe tei, and also a skill score based on accuracy. Bam two axes
# def analysis_chart():


def fetch_synced_data(filename="synced_data_alan_focused.csv"):
    # fetch synced data from the directory datafiles which is in the parent directory of this script
    script_dir = Path(__file__).resolve().parent
    datafiles_dir = script_dir.parent / "datafiles"
    if filename is None:
        matching_files = []
    elif Path(filename).is_absolute():
        requested_path = Path(filename)
        matching_files = [requested_path] if requested_path.is_file() else []
    else:
        matching_files = sorted(
            datafiles_dir.glob(filename),
            key=lambda path: path.stat().st_mtime,
        )
    if not matching_files:
        raise FileNotFoundError(
            f"No EEG data file matching {filename!r} found in {datafiles_dir}"
        )

    eeg_path = matching_files[-1]

    df = pd.read_csv(eeg_path)

    return df


