import time
from datetime import datetime
import nidaqmx
from pyScienceMode2 import RehastimP24 as St
from pyScienceMode2 import Channel as Ch
from pyScienceMode2 import Device

import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal


from pyScienceMode2 import Channel, Point, Device, Modes
from pyScienceMode2 import RehastimP24 as St

"""
This example shows how to use the RehastimP24 device for a hand cycling purpose.
Because the RehastimP24 device is not compatible with the MotoMed, this example will showcase the use of an encoder.
Therefore the nidaqmx library will be used to recover the pedal angle of the bike.
"""

class HandCyclingP24:
    def __init__(self):
        super(HandCyclingP24, self).__init__()
        channel_muscle_name = ["Triceps_r", "Biceps_r", "Delt_ant_r", "Delt_post_r", "Triceps_l", "Biceps_l", "Delt_ant_l",
                               "Delt_post_l"]
        self.list_channels = [Ch(mode=Modes.SINGLE, no_channel=i, amplitude=0, pulse_width=300, frequency=10, name=channel_muscle_name[i], device_type=Device.Rehastimp24) for i in range(1, 9)]

        # Set the intensity for each muscles
        self.biceps_r_intensity = 10
        self.triceps_r_intensity = 10
        self.delt_ant_r_intensity = 10
        self.delt_post_r_intensity = 10
        self.biceps_l_intensity = 10
        self.triceps_l_intensity = 10
        self.delt_ant_l_intensity = 10
        self.delt_post_l_intensity = 10

        # Create our object Stimulator
        self.stimulator = St(port="COM4", show_log=True)
        self.stimulator.init_stimulation(list_channels=self.list_channels)
        self.angle = 0

        # This is to initialize the encoder for the pedal angle
        device_name = None
        local_system = nidaqmx.system.System.local()
        driver_version = local_system.driver_version
        print('DAQmx {0}.{1}.{2}'.format(driver_version.major_version, driver_version.minor_version,
                                         driver_version.update_version))
        for device in local_system.devices:
            print('Device Name: {0}, Product Category: {1}, Product Type: {2}'.format(
                device.name, device.product_category, device.product_type))
            device_mane = device.name
            self.task2 = nidaqmx.Task()
            self.task2.ai_channels.add_ai_voltage_chan(device_mane + '/ai14')
            self.task2.start()

            self.min_voltage = 1.33
            max_voltage = 5
            self.origin = self.task2.read() - self.min_voltage
            self.angle_coeff = 360 / (max_voltage - self.min_voltage)
            self.actual_voltage = None
            # Future development with eccentric mode
            direction = "concentric"

            self.stimulation_state = None
            self.motomed = motomed

    def get_angle(self):
        voltage = self.task2.read() - self.min_voltage
        self.actual_voltage = voltage - self.origin
        self.angle = 360 - (self.actual_voltage * self.angle_coeff) if 0 < self.actual_voltage <= 5 - self.origin else \
            abs(self.actual_voltage) * self.angle_coeff

    def stimulate(self):
        self.stimulator.start_stimulation(upd_list_channels=self.list_channels, stimulation_duration=0.01)
        self.stimulation_state = {"Triceps_r": False, "Biceps_r": False, "Delt_ant_r": False, "Delt_post_r": False,
                                  "Triceps_l": False, "Biceps_l": False, "Delt_ant_l": False, "Delt_post_l": False}

        while 1:
            while self.threadactive is True:
                self.get_angle()
                self.angle_signal.emit(self.angle)
                # Phase 1 / From 0° to 10°
                # right biceps and deltoid posterior activated
                if 0 <= self.angle < 10 and self.stimulation_state["Biceps_r"] + self.stimulation_state["Delt_post_r"] \
                        + self.stimulation_state["Triceps_l"] + self.stimulation_state["Delt_ant_l"] != 2:
                    for list_chan in self.list_channels:
                        list_chan.set_amplitude(0)
                    self.list_channels[1].set_amplitude(self.biceps_r_intensity)

                    self.list_channels[3].set_amplitude(self.delt_post_r_intensity)

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels, stimulation_duration=10)
                    for stim_state in self.stimulation_state:
                        self.stimulation_state[stim_state] = False
                    self.stimulation_state["Biceps_r"] = True
                    self.stimulation_state["Delt_post_r"] = True
                    self.activation_signal.emit(self.stimulation_state)
                    # print("angle : ", self.angle, "phase : ", 1)

                # Phase 2 / From 10° to 20°
                # no muscle activated
                elif 10 <= self.angle < 20 and all(a == 0 for a in self.stimulation_state.values()) is False:
                    for list_chan in self.list_channels:
                        list_chan.set_amplitude(0)
                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels, stimulation_duration=10)
                    for stim_state in self.stimulation_state:
                        self.stimulation_state[stim_state] = False
                    self.activation_signal.emit(self.stimulation_state)
                    # print("angle : ", self.angle, "phase : ", 2)

                # Phase 3 / From 20° to 40°
                # right triceps and deltoid anterior activated
                elif 20 <= self.angle < 40 and self.stimulation_state["Triceps_r"] + self.stimulation_state[
                    "Delt_ant_r"] != 2:
                    for list_chan in self.list_channels:
                        list_chan.set_amplitude(0)
                    self.list_channels[0].set_amplitude(self.triceps_r_intensity)
                    self.list_channels[2].set_amplitude(self.delt_ant_r_intensity)

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels, stimulation_duration=10)
                    for stim_state in self.stimulation_state:
                        self.stimulation_state[stim_state] = False
                    self.stimulation_state["Triceps_r"] = True
                    self.stimulation_state["Delt_ant_r"] = True
                    self.activation_signal.emit(self.stimulation_state)
                    # print("angle : ", self.angle, "phase : ", 3)

                # Phase 4 / From 40° to 180°
                # right triceps, right deltoid anterior, left biceps and left deltoid posterior activated
                elif 40 <= self.angle < 180 and self.stimulation_state["Triceps_r"] + self.stimulation_state[
                    "Delt_ant_r"] \
                        + self.stimulation_state["Biceps_l"] + self.stimulation_state["Delt_post_l"] != 4:
                    for list_chan in self.list_channels:
                        list_chan.set_amplitude(0)
                    self.list_channels[0].set_amplitude(self.triceps_r_intensity)

                    self.list_channels[2].set_amplitude(self.delt_ant_r_intensity)
                    self.list_channels[5].set_amplitude(self.biceps_l_intensity)
                    self.list_channels[7].set_amplitude(self.delt_post_l_intensity)

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels, stimulation_duration=10)
                    for stim_state in self.stimulation_state:
                        self.stimulation_state[stim_state] = False
                    self.stimulation_state["Triceps_r"] = True
                    self.stimulation_state["Delt_ant_r"] = True
                    self.stimulation_state["Biceps_l"] = True
                    self.stimulation_state["Delt_post_l"] = True
                    self.activation_signal.emit(self.stimulation_state)
                    # print("angle : ", self.angle, "phase : ", 4)

                # Phase 5 / From 180° to 190°
                # left biceps and left deltoid posterior activated
                elif 180 <= self.angle < 190 and self.stimulation_state["Triceps_r"] + self.stimulation_state[
                    "Delt_ant_r"] \
                        + self.stimulation_state["Biceps_l"] + self.stimulation_state["Delt_post_l"] != 2:
                    for list_chan in self.list_channels:
                        list_chan.set_amplitude(0)

                    self.list_channels[5].set_amplitude(self.biceps_l_intensity)
                    self.list_channels[7].set_amplitude(self.delt_post_l_intensity)

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels, stimulation_duration=10)
                    for stim_state in self.stimulation_state:
                        self.stimulation_state[stim_state] = False
                    self.stimulation_state["Biceps_l"] = True
                    self.stimulation_state["Delt_post_l"] = True
                    self.activation_signal.emit(self.stimulation_state)
                    # print("angle : ", self.angle, "phase : ", 5)

                # Phase 6 / From 190° to 200°
                # no muscle activated
                elif 190 <= self.angle < 200 and all(a == 0 for a in self.stimulation_state.values()) is False:
                    for list_chan in self.list_channels:
                        list_chan.set_amplitude(0)
                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels, stimulation_duration=10)
                    for stim_state in self.stimulation_state:
                        self.stimulation_state[stim_state] = False
                    self.activation_signal.emit(self.stimulation_state)
                    # print("angle : ", self.angle, "phase : ", 6)

                # Phase 7 / From 200° to 220°
                # left triceps and left deltoid anterior activated
                elif 200 <= self.angle < 220 and self.stimulation_state["Triceps_l"] + self.stimulation_state[
                    "Delt_ant_l"] != 2:
                    for list_chan in self.list_channels:
                        list_chan.set_amplitude(0)

                    self.list_channels[4].set_amplitude(self.triceps_l_intensity)
                    self.list_channels[6].set_amplitude(self.delt_ant_l_intensity)

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels, stimulation_duration=10)
                    for stim_state in self.stimulation_state:
                        self.stimulation_state[stim_state] = False
                    self.stimulation_state["Triceps_l"] = True
                    self.stimulation_state["Delt_ant_l"] = True
                    self.activation_signal.emit(self.stimulation_state)
                    # print("angle : ", self.angle, "phase : ", 7)

                # Phase 8 / From 220° to 360°
                # right biceps, right deltoid posterior, left triceps and left deltoid anterior activated
                elif 220 <= self.angle < 360 and self.stimulation_state["Biceps_r"] + self.stimulation_state[
                    "Delt_post_r"] \
                        + self.stimulation_state["Triceps_l"] + self.stimulation_state["Delt_ant_l"] != 4:
                    for list_chan in self.list_channels:
                        list_chan.set_amplitude(0)
                    self.list_channels[1].set_amplitude(self.biceps_r_intensity)

                    self.list_channels[3].set_amplitude(self.delt_post_r_intensity)
                    self.list_channels[4].set_amplitude(self.triceps_l_intensity)
                    self.list_channels[6].set_amplitude(self.delt_ant_l_intensity)

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels, stimulation_duration=10)
                    for stim_state in self.stimulation_state:
                        self.stimulation_state[stim_state] = False
                    self.stimulation_state["Biceps_r"] = True
                    self.stimulation_state["Delt_post_r"] = True
                    self.stimulation_state["Triceps_l"] = True
                    self.stimulation_state["Delt_ant_l"] = True
                    self.activation_signal.emit(self.stimulation_state)
                    # print("angle : ", self.angle, "phase : ", 8)

                time.sleep(0.001)

if __name__ == "__main__":
    HandCyclingP24().stimulate()
