from scipy.optimize import curve_fit
import sys
from reused_scripts.field_fox import *

LONG_ANTENNA = "17.6"
SHORT_ANTENNA = "15.4"


def lorentzian(var, center, width, amp, ver_shift):
    important = (var - center)/width
    return amp/(important**2 + 1) + ver_shift

def lorentzian_full_width_half_max(center, width):
    return center - width, center + width, 2*width

def voltage_log_to_linear(log_data):
    return 10**(log_data/20)

def linear_to_vswr(linear_data):
    return (1 + linear_data)/(1 - linear_data)

def data_lorentzian_fit(x_data, y_data, initial_guess=np.array([2.997375e9, 10e4, 1, 0.4])):
    parameters, covariances = curve_fit(lorentzian, x_data, y_data, p0=initial_guess)[:2]
    center, width, amp, ver_shift = parameters
    quality_fac, coupling_fac = quality_factor_calc(min(1 - y_data), width, center)
    plt.plot(x_data, y_data, "ro", label="Data")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel(r"$1 - \Gamma^{ 2}$")
    plt.title(f"Lorentzian fit to find the quality factor of {round(quality_fac)}")
    plt.plot(x_data, lorentzian(x_data, center, width, amp, ver_shift), "b-", label="Lorentzian fit")
    plt.legend()
    plt.savefig("figure_generation/lorentzian_fit")
    plt.show()
    print(f"Resonant frequency is: {center/10**9} GHz\nLorentzian width is {width/1e3} kHz\n"
          f"Quality factor is {quality_fac}")
    return [center, width, amp, ver_shift], quality_fac, coupling_fac

def quality_factor_calc(min_mlin, lorentzian_width, res_freq):
    g = (1 - min_mlin)/(1 + min_mlin)
    print(f"The coupling factor is: {g}")
    return (1 + g)*res_freq/(2 * lorentzian_width), g


def data_saver(antenna_len, data_file_name, frequencies, reflected, stub_len, temperature, transmitted, quality_factor,
               coupling_factor, lorentzian_parameter_list, phase, sub_group=""):
    with h5py.File(data_file_name, 'r+') as hf:

        if sub_group:
            counter = map_max_key(hf[sub_group])
            new_ant_len = hf[sub_group].create_group(str(counter))
        else:
            counter = map_max_key(hf)
            new_ant_len = hf.create_group(str(counter))

        new_ant_len.create_dataset('antenna_len', data=float(antenna_len))
        new_ant_len.create_dataset('stub_len', data=float(stub_len))
        new_ant_len.create_dataset('temperature', data=float(temperature))
        new_ant_len.create_dataset('s11', data=reflected)
        new_ant_len.create_dataset('s12', data=transmitted)
        new_ant_len.create_dataset('frequencies', data=frequencies)
        new_ant_len.create_dataset("quality", data=quality_factor)
        new_ant_len.create_dataset("coupling", data=coupling_factor)
        new_ant_len.create_dataset("fit para", data=lorentzian_parameter_list)
        new_ant_len.create_dataset("phase", data=phase)


def main():
    if len(sys.argv) != 4:
        print("Not all arguments included")
        exit(1)

    antenna_len = sys.argv[1]
    stub_len = sys.argv[2]
    temperature = sys.argv[3]

    center_frequency = 3.000364476 * 10**9
    span_frequency = 25e6
    num_points = 1500
    fieldfox = set_up_field_fox("TCPIP0::192.168.0.1::inst0::INSTR")
    mode_selection(fieldfox, "NA")
    frequencies = frequency_setup_center(fieldfox, num_points, center_frequency, span_frequency)
    reflected = na_retrieve_data(fieldfox, "S11", "MLOG")
    transmitted = na_retrieve_data(fieldfox, "S12", "MLOG")
    phase = na_retrieve_data(fieldfox, "S11", "PHAS")

    clean_up(fieldfox)

    plt.plot(frequencies, transmitted)
    plt.show()
    plt.plot(frequencies, phase)
    plt.show()

    parameter_list, quality_factor, coupling_factor = \
        data_lorentzian_fit(frequencies, 1 - voltage_log_to_linear(reflected)**2,
                            initial_guess=np.array([center_frequency, 10e4, 1, 0.4]))

    prompt = input('Save data?: ')
    if prompt == "y":
        file_name = input('File name?: ')
        while file_name not in ["left", "right", "both_right_peak", "both_left_peak", "both_lock_box", "lock_box"]:
            "Wrong name, try again!"
            file_name = input('File name?: ')
        data_file_name = f"data/drive_ant/{file_name}_peak_data.h5"
        # subgroup = SHORT_ANTENNA
        # data_saver(antenna_len, data_file_name, frequencies, reflected, stub_len, temperature, transmitted,
        #            quality_factor, coupling_factor, parameter_list, phase, sub_group=subgroup)
        data_saver(antenna_len, data_file_name, frequencies, reflected, stub_len, temperature, transmitted,
                   quality_factor, coupling_factor, parameter_list, phase)


if __name__ == "__main__":
    main()










