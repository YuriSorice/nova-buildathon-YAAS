import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.figure import Figure



# eeg data analysis
# csv contains 2 second window with each channel showing its frequency and power i think
#window1, channel1(frequency1power, frequency2power,...), channel2, channel3, 
#window2, channel1frequency1power, channel1frequency2power, channel1frequency3power, channel2frequency1power, ...
#

#process csv to turn into df 
# pd.read_csv('eeg_data.csv')  # Replace with your actual CSV file path
# then calculate engagement index tbr, tar, and frontal alpha asymmetry

#all calculate functions return a pandas dataframe with timestamp and the value at each timestamp
#thus can then give someone their average value over whole session, or plot the value over time to see how it changes
#also can plot it against game data to see how it changes with game events



#task engagement index per timestamp:
#channels Fz, Cz, Pz
#return pandas dataframe with columns: time, engagement_index
def calculate_task_engagement(df, channels = ['Fz', 'Cz', 'Pz']):

    #find the beta power column in each channel with this block of code:
    #basically make the column names what they are in the dataframe
    beta_columns = []
    for ch in channels:
        beta_columns.append(f"{ch}_beta")

    #find alpha power
    alpha_columns = []
    for ch in channels:
        alpha_columns.append(f"{ch}_alpha")

    #find theta power
    theta_columns = []
    for ch in channels:
        theta_columns.append(f"{ch}_theta")

    #averages beta, alpha, and theta power across all chosen channels
    beta_power = df[[beta_columns]].mean(axis=1) #average beta power across all chosen channels
    alpha_power = df[[alpha_columns]].mean(axis=1) #average alpha power across all chosen channels   
    theta_power = df[[theta_columns]].mean(axis=1) #average theta power across all chosen channels

    result = pd.DataFrame({
        'time_stamp': df['time_stamp'], #whatever its called in the file we are given
        'tei': beta_power / (alpha_power + theta_power + 1e-10) #task engagement index
    })
    
    return result



def calculate_tbr(df, channels):

    #find theta columns
    theta_columns = []
    for ch in channels:
        theta_columns.append(f"{ch}_theta")

    #find beta columns
    beta_columns = []
    for ch in channels:
        beta_columns.append(f"{ch}_beta")

    theta_power = df[[theta_columns]].mean(axis=1) #average theta power across all chosen channels
    beta_power = df[[beta_columns]].mean(axis=1) #average beta power across all chosen channels 

    result = pd.DataFrame({
        'time_stamp': df['time_stamp'], #whatever its called in the file we are given
        'tbr': theta_power / (beta_power + 1e-10) #theta/beta ratio
    })

    return result



#channels1 is frontal channels for theta, channels 2 is parietal channels for alpha
def calculate_tar(df, channels1 = ['Fz', 'F3', 'F4'], channels2 = ['Pz', 'P3', 'P4']):
    theta_columns = []
    for ch in channels1:
        theta_columns.append(f"{ch}_theta")

    alpha_columns = []
    for ch in channels2:
        alpha_columns.append(f"{ch}_alpha")

    theta_power = df[[theta_columns]].mean(axis=1) #average theta power across all chosen channels
    alpha_power = df[[alpha_columns]].mean(axis=1) #average alpha power across

    result = pd.DataFrame({
        'time_stamp': df['time_stamp'], #whatever its called in the file we are given
        'tar': theta_power / (alpha_power + 1e-10) #theta/alpha ratio
    })

    return result


#calculate frontal alpha asymmetry, channels1 is left hemisphere, channels2 is right hemisphere
def calculate_faa(df, channels1 = ['F3'], channels2 = ['F4']):
    alpha_columns1 = []
    for ch in channels1:
        alpha_columns1.append(f"{ch}_alpha")

    alpha_columns2 = []
    for ch in channels2:
        alpha_columns2.append(f"{ch}_alpha")

    alpha_power1 = df[[alpha_columns1]].mean(axis=1) #average alpha power across all chosen channels
    alpha_power2 = df[[alpha_columns2]].mean(axis=1) #average alpha power across all chosen channels

    result = pd.DataFrame({
        'time_stamp': df['time_stamp'], #whatever its called in the file we are given
        'faa': np.log(alpha_power1 + 1e-10) - np.log(alpha_power2 + 1e-10) #frontal alpha asymmetry
    })

    return result


def plot_ratio_over_time(df, ratio_column):
    plt.figure(figsize=(10, 6))
    plt.plot(df['time_stamp'], df[ratio_column], label=ratio_column, color='blue')
    plt.xlabel('Time (seconds)')
    plt.ylabel(ratio_column)
    plt.title(f'{ratio_column} Over Time')
    plt.legend()
    plt.grid()
    plt.show()


#plot task engagement over time
def plot_task_engagement(tei_df):
    plt.figure(figsize=(10, 6))
    plt.plot(tei_df['time_stamp'], tei_df['tei'], label='Task Engagement Index', color='blue')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Task Engagement Index')
    plt.title('Task Engagement Index Over Time')
    plt.legend()
    plt.grid()
    plt.show()




#game data analysis
#csv has columns: timestamp,modality,action,performance_state
#accuracy = number of correct actions / total actions
def calculate_accuracy(df):
    total_actions = len(df)
    correct_actions = len(df[df['performance_state'] == 'CORRECT_HIT'])
    accuracy = correct_actions / total_actions if total_actions > 0 else 0
    return accuracy

def running_accuracy(df):
    #turn correct hit into a 1
    correct_bool = df['performance_state'] == 'CORRECT_HIT'
    result = pd.DataFrame({
        'timestamp': df['timestamp'],
        'running_accuracy': correct_bool.expanding().mean() * 100
    })
    return result

def rolling_average_accuracy(df, window_size=4):

    correct_bool = df['performance_state'] == 'CORRECT_HIT'
    result = pd.DataFrame({
        'timestamp': df['timestamp'],
        'rolling_average_accuracy': correct_bool.rolling(window=window_size, min_periods=1).mean() * 100 
        
    })
    return result



#plot accuracies
def plot_accuracy_over_time(accuracy_df, accuracy_column):
    plt.figure(figsize=(10, 6))
    plt.plot(accuracy_df['timestamp'], accuracy_df[accuracy_column], label=accuracy_column, color='blue')
    plt.xlabel('Time (seconds)')
    plt.ylabel(accuracy_column)
    plt.title(f'{accuracy_column} Over Time')
    plt.legend()
    plt.grid()
    plt.show()


def plot_both_accuracies(running_accuracy_df, rolling_average_accuracy_df):
    # 1. Create an explicit Figure object instead of using plt.figure()
    fig = Figure(figsize=(15, 10), dpi=100)
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
    ax.plot(running_accuracy_df['timestamp'], running_accuracy_df['running_accuracy'], label='Running Accuracy', color="#50B5CA", linewidth = 2, marker = 'o')
    ax.plot(rolling_average_accuracy_df['timestamp'], rolling_average_accuracy_df['rolling_average_accuracy'], label='Rolling Average Accuracy', color="#FF9900", linewidth = 2, marker = 'o')
    ax.fill_between(running_accuracy_df['timestamp'], running_accuracy_df['running_accuracy'], color="#50B5CA", alpha=0.1)
    ax.fill_between(rolling_average_accuracy_df['timestamp'], rolling_average_accuracy_df['rolling_average_accuracy'], color="#FF9900", alpha=0.1)
    
    ax.set_xlabel('Time (seconds)', color = 'white', fontsize = 12, fontname = 'Comic Sans MS')
    ax.set_ylabel('Accuracy (%)', color = 'white', fontsize = 12, fontname = 'Comic Sans MS')
    ax.set_title('Running and Rolling Average Accuracy Over Time', color = 'white', fontsize = 16, fontname = 'Comic Sans MS')
    ax.legend()
    ax.grid(True)

    # 3. Return the figure so the GUI can capture it
    return fig

def fetch_game_data():
    script_dir = Path(__file__).resolve().parent.parent
    raw_path = script_dir.parent / "game_session_log.csv"
    dfgame = pd.read_csv(raw_path)  # Replace with your actual CSV file path
    return dfgame


# dfgame = fetch_game_data()  # Use the function to fetch game data
# #df = pd.read_csv('eeg_data.csv')  # Replace with your actual CSV file path
# accuracy = calculate_accuracy(dfgame)
# print(accuracy)
# running_accuracy = running_accuracy(dfgame)
# print(running_accuracy)
# rolling_average_accuracy = rolling_average_accuracy(dfgame, window_size=6)
# print(rolling_average_accuracy)

# running_accuracy_df = running_accuracy(dfgame)
# print(running_accuracy_df)
# rolling_average_accuracy_df = rolling_average_accuracy(dfgame, window_size=6)
# print(rolling_average_accuracy_df)

#tei_df = calculate_task_engagement(df)
#tbr_df = calculate_tbr(df, channels=['Fz', 'Cz', 'Pz']) 
#tar_df = calculate_tar(df)
#faa_df = calculate_faa(df)

#average ratios over entire session:
#average_tei = tei_df['tei'].mean()
#average_tbr = tbr_df['tbr'].mean()
#average_tar = tar_df['tar'].mean()
#average_faa = faa_df['faa'].mean()



