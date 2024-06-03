from typing import Callable
import matplotlib.pyplot as plt
import h5py
import pyvisa as visa
import numpy as np


DEBUG = False
def Errcheck(fieldfox):
    myError = []
    ErrorList = fieldfox.query("SYST:ERR?").split(',')
    Error = ErrorList[0]
    if int(Error) == 0:
        print("+0, No Error!")
    else:
        while int(Error) != 0:
            print("Error #: " + ErrorList[0])
            print("Error Description: " + ErrorList[1])
            myError.append(ErrorList[0])
            myError.append(ErrorList[1])
            ErrorList = fieldfox.query("SYST:ERR?").split(',')
            Error = ErrorList[0]
            myError = list(myError)
    return myError

def error_printer(func: Callable):
    def wrapper(fieldfox, *args, **kwargs):
        if DEBUG:
            print(Errcheck(fieldfox))
        return func(fieldfox, *args, **kwargs)
    return wrapper

def set_up_field_fox(address):
    rm = visa.ResourceManager()
    field_fox = rm.open_resource(address)
    del field_fox.timeout
    print("Connected to field fox!!")
    field_fox.write("*CLS")
    preset = field_fox.query_ascii_values("SYST:PRES;*OPC?")
    print("Preset complete, *OPC? returned : " + str(preset[0]))
    print(Errcheck(field_fox))

    return field_fox

def frequency_setup_center(fieldfox, numPoints, center_freq, span_freq, bandwidth=1e3):
    start_freq = center_freq - span_freq / 2
    end_freq = center_freq + span_freq / 2

    fieldfox.write("SENS:SWE:POIN " + str(numPoints))
    fieldfox.write("SENS:FREQ:CENT " + str(center_freq))
    fieldfox.write("SENS:FREQ:SPAN " + str(span_freq))
    fieldfox.write(f"BWID {bandwidth};*OPC?")
    fieldfox.write(f"BAND {bandwidth};*OPC?")
    print("FieldFox start frequency = " + str(start_freq) + " stop frequency = " + str(end_freq))
    print(f"Bandwidth set to {bandwidth}")

    return np.linspace(start_freq, end_freq, numPoints)


def frequency_setup_start_end(fieldfox, numPoints, start_freq, end_freq, bandwidth=1e3):
    center_freq = (start_freq + end_freq)/2
    span_freq = (-start_freq + end_freq)/2

    print(str(center_freq) + "±" + str(span_freq))

    fieldfox.write("SENS:SWE:POIN " + str(numPoints))
    fieldfox.write("SENS:FREQ:STAR " + str(start_freq))
    fieldfox.write("SENS:FREQ:STOP " + str(end_freq))
    fieldfox.write(f"BWID {bandwidth};*OPC?")
    fieldfox.write(f"BAND {bandwidth};*OPC?")
    print("FieldFox start frequency = " + str(start_freq) + " stop frequency = " + str(end_freq))
    print(f"Bandwidth set to {bandwidth}")

    return np.linspace(start_freq, end_freq, numPoints)


def mode_selection(fieldfox, mode):
    fieldfox.write(f"INST:SEL '{mode}';*OPC?")
    print(f"{mode} mode selected successfully")


def na_retrieve_data(fieldfox, mode, mode_format):

    fieldfox.write("CALC:PAR1:DEF " + mode)
    fieldfox.write("CALC:PAR1:SEL")
    fieldfox.write("CALC:FORM " + mode_format)
    fieldfox.write("INIT:CONT 0")
    print("Asking for data")
    fieldfox.query_ascii_values("INIT:IMM;*OPC?")
    measurement = fieldfox.query_ascii_values("CALC:DATA:FDATa?", container=np.array)
    print(f"Max value = {max(measurement)}\nMin Value = {min(measurement)}")

    return measurement


def sa_source(fieldfox, drive_frequency, power):
    fieldfox.write("SOUR:ENAB ON")
    fieldfox.write("SOUR:MODE CW")
    fieldfox.write(f"SOUR:POW {power}")
    fieldfox.write(f"SOUR:FREQ {drive_frequency}")

def sa_retrieve_data(fieldfox):

    fieldfox.write("INIT:CONT OFF;*OPC?")
    fieldfox.read()

    fieldfox.write("INIT:IMM;*OPC?")
    fieldfox.write("TRACE:DATA?")
    raw_data = fieldfox.read()
    measurement = [float(x) for x in raw_data.split(",")]

    print(f"Max value = {max(measurement)}\nMin Value = {min(measurement)}")

    fieldfox.write("INIT:CONT ON")

    return measurement

@error_printer
def clean_up(fieldfox):
    fieldfox.write("INIT:CONT ON")
    fieldfox.close()


def map_max_key(hf):
    try:
        counter = int(max(hf.keys())) + 1
    except ValueError:
        counter = 0
    return counter

def hdf5_data_saver(data_file_name, sub_group="", **kwargs):
    with h5py.File(data_file_name, 'r+') as hf:

        if sub_group:
            counter = map_max_key(hf[sub_group])
            new_group = hf[sub_group].create_group(str(counter))
        else:
            counter = map_max_key(hf)
            new_group = hf.create_group(str(counter))

        for group_name in kwargs["kwargs"].keys():
            print(group_name)
            print(kwargs["kwargs"][group_name])
            new_group.create_dataset(group_name, data=kwargs["kwargs"][group_name])


def main_test():
    center_frequency = 1.5 * 10 ** 9
    span_frequency = 1.4e9
    num_points = 201
    fieldfox = set_up_field_fox("TCPIP0::192.168.0.1::inst0::INSTR")
    frequencies = frequency_setup_center(fieldfox, num_points, center_frequency, span_frequency)
    reflected = sa_retrieve_data(fieldfox)
    plt.plot(frequencies, reflected)
    plt.show()
    clean_up(fieldfox)


if __name__ == "__main__":
    main_test()

