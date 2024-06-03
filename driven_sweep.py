import time
from enum import Enum

import matplotlib.pyplot as plt
from scipy.signal import argrelextrema
from field_fox


class Trigger(Enum):
    external = "EXT"
    rf_burst = "RFB"
    free_run = "FREE"



def manual_sweep(field_fox, num_point_sweep, center_freq, freq_span, cw_power, acquisition_span=10e6,
                 local_num_points=100, sleep_time=0.1, trigger_mode="FREE", trigger_level=-25):

    if acquisition_span < freq_span:
        acquisition_span = freq_span

    sweep = np.zeros(num_point_sweep)
    start_freq = center_freq - freq_span / 2
    end_freq = center_freq + freq_span / 2
    sweep_frequency = np.linspace(start_freq, end_freq, num_point_sweep)
    field_fox.write("CALC:LIM:SOUN OFF")
    mode_selection(fieldfox, "SA")
    frequency_setup_center(fieldfox, local_num_points, center_freq, acquisition_span)
    field_fox.write(f"TRIG:SOUR {trigger_mode}")
    field_fox.write(f"TRIG:LEV {trigger_level}")


    for index, frequency in enumerate(sweep_frequency):
        if cw_power < -9:
            sa_source(field_fox, frequency, cw_power)
            time.sleep(sleep_time)
            peak_power = max(sa_retrieve_data(field_fox))
            sweep[index] = peak_power

    print(sweep_frequency[np.argmin(sweep)])
    sa_source(field_fox, sweep_frequency[np.argmin(sweep)], cw_power)


    return sweep_frequency, sweep


# def manual_sweep_2(field_fox, num_point_sweep, center_freq, freq_span, local_num_points=100, local_frequency_span=50e3,
#                    sleep_time=0.1, trigger_mode="FREE"):
#     sweep = np.zeros(num_point_sweep)
#     start_freq = center_freq - freq_span / 2
#     end_freq = center_freq + freq_span / 2
#     sweep_frequency = np.linspace(start_freq, end_freq, num_point_sweep)
#     field_fox.write("CALC:LIM:SOUN OFF")
#     mode_selection(fieldfox, "SA")
#     field_fox.write(f"TRIG:SOUR {trigger_mode}")

#     for index, frequency in enumerate(sweep_frequency):
#         frequency_setup_center(fieldfox, local_num_points, frequency, local_frequency_span)
#         sa_source(field_fox, frequency, -7)
#         time.sleep(sleep_time)
#         peak_power = max(sa_retrieve_data(field_fox))
#         sweep[index] = peak_power


#     return sweep_frequency, sweep

def grid(axis):
    # Show the major grid and style it slightly.
    axis.grid(which='major', color='#DDDDDD', linewidth=0.8)
    # Show the minor grid as well. Style it in very light gray as a thin,
    # dotted line.
    axis.grid(which='minor', color='#EEEEEE', linestyle=':', linewidth=0.5)
    # Make the minor ticks and gridlines show.
    axis.minorticks_on()
    axis.set_axisbelow(True)

def label_traces_plot(x_data_list, y_data_list, label_list, color_list, xlabel="", ylabel="", title="",
                      row_len=15, col_len=7, fig=None, ax=None, log_scale=False, display="o", thick=2):
    if ax is None:
        fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(row_len, col_len))

    for x_data, y_data, fig_label, line_color in zip(x_data_list, y_data_list, label_list, color_list):
        ax.plot(x_data, y_data, f"{line_color}{display}", label=fig_label, linewidth=thick)
    if log_scale:
        ax.set_yscale('log')
    ax.set_xlabel(xlabel, fontweight="bold", size=10)
    ax.set_ylabel(ylabel, fontweight="bold", size=10)
    ax.set_title(title, fontweight="bold", size=10)
    ax.legend()
    grid(ax)

    return fig, ax


def reflection_sweep(frequencies, sweep_trace):
    minimum_indices = argrelextrema(sweep_1, np.less)[0][:]
    label_traces_plot([frequencies], [sweep_trace], ["reflected"], ["b"])
    for min_index in minimum_indices:
        plt.axvline(x=freq_1[min_index], color='g', linestyle='--', )
    actual_min = 0
    for min_index in minimum_indices:
        current_min = sweep_1[min_index]
        if current_min < sweep_1[actual_min]:
            actual_min = min_index
    print(f"frequency: {freq_1[actual_min]} at {min(sweep_1) - max(sweep_1)}")

def transmission_sweep(frequencies, sweep_trace):
    minimum_indices = argrelextrema(sweep_1, np.greater)[0][:]
    sweep_trace = sweep_trace - min(sweep_trace)
    label_traces_plot([frequencies], [sweep_trace], ["reflected"], ["b"])
    for min_index in minimum_indices:
        plt.axvline(x=freq_1[min_index], color='g', linestyle='--', )



if __name__ == "__main__":
    fieldfox = set_up_field_fox("TCPIP0::192.168.0.1::inst0::INSTR")
    signal_power = -11
    frequency_span = 15e6
    frequency_center = 2.997375e9
    number_of_points_used = 401
    freq_1, sweep_1 = manual_sweep(fieldfox, number_of_points_used, frequency_center, frequency_span, signal_power,
                                   trigger_mode=Trigger.rf_burst.value, sleep_time=0.5,
                                   acquisition_span=15e6, local_num_points=201, trigger_level=-30)


    plt.plot(freq_1, sweep_1 - max(sweep_1))
    plt.show()
    reflection_sweep(freq_1, sweep_1)
    plt.show()

    file_path = 'data/archive_data/reflection_curve.txt'

    # Write the arrays to the text file
    with open(file_path, 'w') as file:
        np.savetxt(file, freq_1[None], fmt='%d', delimiter=' ')
        np.savetxt(file, sweep_1[None], fmt='%d', delimiter=' ')

    data_file_name = 'data/archive_data/reflection_curve.h5'


    with h5py.File(data_file_name, 'r+') as hf:
        try:
            counter = int(max(hf.keys())) + 1
        except ValueError:
            counter = 0
        dataset = hf.create_group(str(counter))
        dataset.create_dataset('frequencies', data=freq_1)
        dataset.create_dataset('s11', data=sweep_1)




