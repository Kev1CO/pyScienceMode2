# import threading
import time
from datetime import datetime
import nidaqmx
from pyScienceMode2.rehastim_interface import Stimulator as St
from pyScienceMode2 import Channel as Ch
from gui.Stimulation_GUI import Ui_MainWindow
# from gui.Cursor_widget import Ui_MainWindow as Ui_CursorMainWindow

import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, QThread, pyqtSignal


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    angle_signal = pyqtSignal(float)
    activation_signal = pyqtSignal(dict)

    def __init__(self, motomed: dict = None):
        super(Worker, self).__init__()
        # Create a list of channels
        self.list_channels = []

        # Create all channels possible
        channel_1 = Ch.Channel(mode="Single", no_channel=1, amplitude=0, pulse_width=300, name="Triceps_r")
        channel_2 = Ch.Channel(mode="Single", no_channel=2, amplitude=0, pulse_width=300, name="Biceps_r")
        channel_3 = Ch.Channel(mode="Single", no_channel=3, amplitude=0, pulse_width=300, name="Delt_ant_r")
        channel_4 = Ch.Channel(mode="Single", no_channel=4, amplitude=0, pulse_width=300, name="Delt_post_r")
        channel_5 = Ch.Channel(mode="Single", no_channel=5, amplitude=0, pulse_width=300, name="Triceps_l")
        channel_6 = Ch.Channel(mode="Single", no_channel=6, amplitude=0, pulse_width=300, name="Biceps_l")
        channel_7 = Ch.Channel(mode="Single", no_channel=7, amplitude=0, pulse_width=300, name="Delt_ant_l")
        channel_8 = Ch.Channel(mode="Single", no_channel=8, amplitude=0, pulse_width=300, name="Delt_post_l")

        # Choose which channel will be used
        self.list_channels.append(channel_1)
        self.list_channels.append(channel_2)
        self.list_channels.append(channel_3)
        self.list_channels.append(channel_4)
        self.list_channels.append(channel_5)
        self.list_channels.append(channel_6)
        self.list_channels.append(channel_7)
        self.list_channels.append(channel_8)

        # Set the intensity for each muscles
        self.biceps_r_intensity = 0
        self.triceps_r_intensity = 0
        self.delt_ant_r_intensity = 0
        self.delt_post_r_intensity = 0
        self.biceps_l_intensity = 0
        self.triceps_l_intensity = 0
        self.delt_ant_l_intensity = 0
        self.delt_post_l_intensity = 0

        # Create our object Stimulator
        if motomed is not None:
            self.stimulator = St(port="COM4", with_motomed=True, show_log=False, fast_mode=False)
            self.direction = motomed['direction']
            self.mode = motomed['active']
            self.speed = motomed['speed']
            self.gear = motomed['gear']
            self.motomed = 1
        else:
            self.stimulator = St(port="COM4", with_motomed=False, show_log=False, fast_mode=False)

        self.stimulator.init_channel(stimulation_interval=30, list_channels=self.list_channels,
                                     low_frequency_factor=0)

        self.angle = 0

        device_mane = None
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

    def get_angle(self):
        voltage = self.task2.read() - self.min_voltage
        self.actual_voltage = voltage - self.origin
        self.angle = 360 - (self.actual_voltage * self.angle_coeff) if 0 < self.actual_voltage <= 5 - self.origin else \
            abs(self.actual_voltage) * self.angle_coeff

    def stimulate(self):
        self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
        self.stimulation_state = {"Triceps_r": False, "Biceps_r": False, "Delt_ant_r": False, "Delt_post_r": False,
                                  "Triceps_l": False, "Biceps_l": False, "Delt_ant_l": False, "Delt_post_l": False}
        if self.motomed is not None:
            self.stimulator.motomed.init_phase_training(arm_training=True)
            self.stimulator.motomed.start_phase(speed=self.speed, gear=self.gear, active=self.mode, go_forward=self.direction, spasm_detection=True)

        while 1:
            while self.threadactive is True:
                # start_time = time.time()
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

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
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
                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
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

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
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

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
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

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
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
                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
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

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
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

                    self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
                    for stim_state in self.stimulation_state:
                        self.stimulation_state[stim_state] = False
                    self.stimulation_state["Biceps_r"] = True
                    self.stimulation_state["Delt_post_r"] = True
                    self.stimulation_state["Triceps_l"] = True
                    self.stimulation_state["Delt_ant_l"] = True
                    self.activation_signal.emit(self.stimulation_state)
                    # print("angle : ", self.angle, "phase : ", 8)

                time.sleep(0.001)

                # end_time = time.time()
                # loop_time = end_time - start_time
                # print("loop time : ", loop_time)


class App(QtWidgets.QMainWindow):
    def __init__(self):
        super(App, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # self.ui_cursor = Ui_CursorMainWindow()

        # --- Stimulator Tab --- #
        self.worker = None
        self.ui.Set_0_pushButton.clicked.connect(self.set_0_values)
        self.ui.Start_pushButton.clicked.connect(self.start_stimulation_program)
        self.ui.Stop_pushButton.clicked.connect(self.stop_program)
        self.ui.Triceps_right_minus5_intensity_pushButton.clicked.connect(
            lambda: self.set_triceps_right_value(value=-5))
        self.ui.Triceps_right_minus1_intensity_pushButton.clicked.connect(
            lambda: self.set_triceps_right_value(value=-1))
        self.ui.Triceps_right_plus1_intensity_pushButton.clicked.connect(lambda: self.set_triceps_right_value(value=1))
        self.ui.Triceps_right_plus5_intensity_pushButton.clicked.connect(lambda: self.set_triceps_right_value(value=5))
        self.ui.Biceps_right_minus5_intensity_pushButton.clicked.connect(lambda: self.set_biceps_right_value(value=-5))
        self.ui.Biceps_right_minus1_intensity_pushButton.clicked.connect(lambda: self.set_biceps_right_value(value=-1))
        self.ui.Biceps_right_plus1_intensity_pushButton.clicked.connect(lambda: self.set_biceps_right_value(value=1))
        self.ui.Biceps_right_plus5_intensity_pushButton.clicked.connect(lambda: self.set_biceps_right_value(value=5))
        self.ui.Deltoid_anterior_right_minus5_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_anterior_right_value(value=-5))
        self.ui.Deltoid_anterior_right_minus1_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_anterior_right_value(value=-1))
        self.ui.Deltoid_anterior_right_plus1_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_anterior_right_value(value=1))
        self.ui.Deltoid_anterior_right_plus5_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_anterior_right_value(value=5))
        self.ui.Deltoid_posterior_right_minus5_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_posterior_right_value(value=-5))
        self.ui.Deltoid_posterior_right_minus1_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_posterior_right_value(value=-1))
        self.ui.Deltoid_posterior_right_plus1_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_posterior_right_value(value=1))
        self.ui.Deltoid_posterior_right_plus5_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_posterior_right_value(value=5))
        self.ui.Triceps_left_minus5_intensity_pushButton.clicked.connect(
            lambda: self.set_triceps_left_value(value=-5))
        self.ui.Triceps_left_minus1_intensity_pushButton.clicked.connect(
            lambda: self.set_triceps_left_value(value=-1))
        self.ui.Triceps_left_plus1_intensity_pushButton.clicked.connect(lambda: self.set_triceps_left_value(value=1))
        self.ui.Triceps_left_plus5_intensity_pushButton.clicked.connect(lambda: self.set_triceps_left_value(value=5))
        self.ui.Biceps_left_minus5_intensity_pushButton.clicked.connect(lambda: self.set_biceps_left_value(value=-5))
        self.ui.Biceps_left_minus1_intensity_pushButton.clicked.connect(lambda: self.set_biceps_left_value(value=-1))
        self.ui.Biceps_left_plus1_intensity_pushButton.clicked.connect(lambda: self.set_biceps_left_value(value=1))
        self.ui.Biceps_left_plus5_intensity_pushButton.clicked.connect(lambda: self.set_biceps_left_value(value=5))
        self.ui.Deltoid_anterior_left_minus5_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_anterior_left_value(value=-5))
        self.ui.Deltoid_anterior_left_minus1_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_anterior_left_value(value=-1))
        self.ui.Deltoid_anterior_left_plus1_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_anterior_left_value(value=1))
        self.ui.Deltoid_anterior_left_plus5_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_anterior_left_value(value=5))
        self.ui.Deltoid_posterior_left_minus5_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_posterior_left_value(value=-5))
        self.ui.Deltoid_posterior_left_minus1_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_posterior_left_value(value=-1))
        self.ui.Deltoid_posterior_left_plus1_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_posterior_left_value(value=1))
        self.ui.Deltoid_posterior_left_plus5_intensity_pushButton.clicked.connect(
            lambda: self.set_deltoid_posterior_left_value(value=5))
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)

        self.ui.Triceps_right_spinBox.valueChanged.connect(lambda: self.update_current(1))
        self.ui.Biceps_right_spinBox.valueChanged.connect(lambda: self.update_current(2))
        self.ui.Deltoide_anterior_right_spinBox.valueChanged.connect(lambda: self.update_current(3))
        self.ui.Deltoide_posterior_right_spinBox.valueChanged.connect(lambda: self.update_current(4))
        self.ui.Triceps_left_spinBox.valueChanged.connect(lambda: self.update_current(5))
        self.ui.Biceps_left_spinBox.valueChanged.connect(lambda: self.update_current(6))
        self.ui.Deltoide_anterior_left_spinBox.valueChanged.connect(lambda: self.update_current(7))
        self.ui.Deltoide_posterior_left_spinBox.valueChanged.connect(lambda: self.update_current(8))

        self.ui.Set_previous_intensity_pushButton.clicked.connect(self.set_to_previous_current)

        self.ui.Triceps_right_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : red;" "}")
        self.ui.Biceps_right_activation_checkBox.setStyleSheet("QCheckBox::indicator" "{" "background-color : red;" "}")
        self.ui.Deltoide_anterior_right_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : red;" "}")
        self.ui.Deltoide_posterior_right_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : red;" "}")
        self.ui.Triceps_left_activation_checkBox.setStyleSheet("QCheckBox::indicator" "{" "background-color : red;" "}")
        self.ui.Biceps_left_activation_checkBox.setStyleSheet("QCheckBox::indicator" "{" "background-color : red;" "}")
        self.ui.Deltoide_anterior_left_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : red;" "}")
        self.ui.Deltoide_posterior_left_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : red;" "}")
        self.ui.Close_pushButton.clicked.connect(lambda: self.close())

        self.previous_triceps_right_intensity = 0
        self.previous_biceps_right_intensity = 0
        self.previous_deltoid_anterior_right_intensity = 0
        self.previous_deltoid_posterior_right_intensity = 0
        self.previous_triceps_left_intensity = 0
        self.previous_biceps_left_intensity = 0
        self.previous_deltoid_anterior_left_intensity = 0
        self.previous_deltoid_posterior_left_intensity = 0

        self.ui.Save_modifications_pushButton.clicked.connect(self.folder_name_modification)
        self.folder = None
        self.start_state = False
        self.file_handle = None
        self.save = False

        # --- Motomed Tab ---#
        self.motomed_start_state = False
        self.ui.Passive_radioButton.toggled.connect(self.motomed_mode)
        self.ui.Active_radioButton.toggled.connect(self.motomed_mode)
        self.ui.Start_motomed_pushButton.clicked.connect(self.start_motomed)
        self.ui.Pause_motomed_pushButton.clicked.connect(self.pause_motomed)
        self.ui.Stop_motomed_pushButton.clicked.connect(self.stop_motomed)
        self.ui.Save_motomed_pushButton.clicked.connect(self.save_motomed)
        self.ui.Close_pushButton_1.clicked.connect(lambda: self.close())
        self.ui.Display_pushButton.clicked.connect(self.cursor)
        self.stimulator = None

    def start_stimulation_program(self):
        self.ui.Start_pushButton.setEnabled(False)
        if self.start_state is False:
            # Step 2: Create a QThread object
            self.thread = QThread()
            # Step 3: Create a worker object
            if self.ui.With_motomed_checkBox.isChecked():
                direction = True if self.ui.Forward_radioButton.isChecked() else False
                mode = False if self.ui.Passive_radioButton.isChecked() else True
                speed = self.ui.Speed_spinBox.value()
                gear = self.ui.Gear_spinBox.value()
                self.worker = Worker(motomed={'direction': direction, 'active': mode, 'speed': speed, 'gear': gear})
            else:
                self.worker = Worker(motomed=None)
            # Step 4: Move worker to the thread
            self.worker.moveToThread(self.thread)
            # Step 5: Connect signals and slots
            self.thread.started.connect(self.worker.stimulate)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            # Step 6: Start the thread
            self.thread.start()
            self.worker.angle_signal.connect(self.angle_display)
            self.worker.activation_signal.connect(self.activation_color)
            self.start_state = True
            self.worker.threadactive = True
            self.ui.With_motomed_checkBox.setEnabled(False)
            self.ui.Stop_pushButton.setEnabled(True)
            self.ui.Close_pushButton.setEnabled(False)
            self.ui.Save_modifications_pushButton.setEnabled(False)
            if self.save is True:
                self.save_modification()

    def stop_program(self):
        self.ui.Stop_pushButton.setEnabled(False)
        self.worker.threadactive = False
        self.ui.Start_pushButton.setEnabled(True)
        self.ui.Close_pushButton.setEnabled(True)
        self.ui.Save_modifications_pushButton.setEnabled(True)
        self.start_state = False
        if self.ui.With_motomed_checkBox.isChecked():
            self.motomed_start_state = False

    def set_0_values(self):
        self.previous_triceps_right_intensity = self.ui.Triceps_right_spinBox.value()
        self.previous_biceps_right_intensity = self.ui.Biceps_right_spinBox.value()
        self.previous_deltoid_anterior_right_intensity = self.ui.Deltoide_anterior_right_spinBox.value()
        self.previous_deltoid_posterior_right_intensity = self.ui.Deltoide_posterior_right_spinBox.value()
        self.previous_triceps_left_intensity = self.ui.Triceps_left_spinBox.value()
        self.previous_biceps_left_intensity = self.ui.Biceps_left_spinBox.value()
        self.previous_deltoid_anterior_left_intensity = self.ui.Deltoide_anterior_left_spinBox.value()
        self.previous_deltoid_posterior_left_intensity = self.ui.Deltoide_posterior_left_spinBox.value()
        self.ui.Triceps_right_spinBox.setValue(0)
        self.ui.Biceps_right_spinBox.setValue(0)
        self.ui.Deltoide_anterior_right_spinBox.setValue(0)
        self.ui.Deltoide_posterior_right_spinBox.setValue(0)
        self.ui.Triceps_left_spinBox.setValue(0)
        self.ui.Biceps_left_spinBox.setValue(0)
        self.ui.Deltoide_anterior_left_spinBox.setValue(0)
        self.ui.Deltoide_posterior_left_spinBox.setValue(0)
        if self.save is True and self.start_state is True:
            self.save_modification()

    def set_to_previous_current(self):
        self.ui.Triceps_right_spinBox.setValue(self.previous_triceps_right_intensity)
        self.ui.Biceps_right_spinBox.setValue(self.previous_biceps_right_intensity)
        self.ui.Deltoide_anterior_right_spinBox.setValue(self.previous_deltoid_anterior_right_intensity)
        self.ui.Deltoide_posterior_right_spinBox.setValue(self.previous_deltoid_posterior_right_intensity)
        self.ui.Triceps_left_spinBox.setValue(self.previous_triceps_left_intensity)
        self.ui.Biceps_left_spinBox.setValue(self.previous_biceps_left_intensity)
        self.ui.Deltoide_anterior_left_spinBox.setValue(self.previous_deltoid_anterior_left_intensity)
        self.ui.Deltoide_posterior_left_spinBox.setValue(self.previous_deltoid_posterior_left_intensity)
        if self.save is True and self.start_state is True:
            self.save_modification()

    def folder_name_modification(self):
        folder = str(
            QFileDialog.getSaveFileName(None, "Save the time modification", '', "Text file (*.txt);;All Files (*)"))
        self.folder = folder[2:-23]
        self.save = True

    def save_modification(self):
        self.file_handle = open(self.folder, "a")
        self.file_handle.write(str(datetime.now()) + " --> Triceps right: " + str(self.ui.Triceps_right_spinBox.value())
                               + "mA ; Biceps right: " + str(self.ui.Biceps_right_spinBox.value())
                               + "mA ; Deltoid anterior right: " + str(self.ui.Deltoide_anterior_right_spinBox.value())
                               + "mA ; Deltoid posterior right: " + str(
            self.ui.Deltoide_posterior_right_spinBox.value())
                               + "mA ; Triceps left: " + str(self.ui.Triceps_left_spinBox.value())
                               + "mA ; Biceps left: " + str(self.ui.Biceps_left_spinBox.value())
                               + "mA ; Deltoid anterior left: " + str(self.ui.Deltoide_anterior_left_spinBox.value())
                               + "mA ; Deltoid posterior left: " + str(self.ui.Deltoide_posterior_left_spinBox.value())
                               + "mA\n")
        self.file_handle.close()

    def set_triceps_right_value(self, value: int):
        current_value = self.ui.Triceps_right_spinBox.value()
        self.previous_triceps_right_intensity = current_value
        self.ui.Triceps_right_spinBox.setValue(current_value + value)
        if self.save is True and self.start_state is True:
            self.save_modification()

    def set_biceps_right_value(self, value: int):
        current_value = self.ui.Biceps_right_spinBox.value()
        self.previous_biceps_right_intensity = current_value
        self.ui.Biceps_right_spinBox.setValue(current_value + value)
        if self.save is True and self.start_state is True:
            self.save_modification()

    def set_deltoid_anterior_right_value(self, value: int):
        current_value = self.ui.Deltoide_anterior_right_spinBox.value()
        self.previous_deltoid_anterior_right_intensity = current_value
        self.ui.Deltoide_anterior_right_spinBox.setValue(current_value + value)
        if self.save is True and self.start_state is True:
            self.save_modification()

    def set_deltoid_posterior_right_value(self, value: int):
        current_value = self.ui.Deltoide_posterior_right_spinBox.value()
        self.previous_deltoid_posterior_right_intensity = current_value
        self.ui.Deltoide_posterior_right_spinBox.setValue(current_value + value)
        if self.save is True and self.start_state is True:
            self.save_modification()

    def set_triceps_left_value(self, value: int):
        current_value = self.ui.Triceps_left_spinBox.value()
        self.previous_triceps_left_intensity = current_value
        self.ui.Triceps_left_spinBox.setValue(current_value + value)
        if self.save is True and self.start_state is True:
            self.save_modification()

    def set_biceps_left_value(self, value: int):
        current_value = self.ui.Biceps_left_spinBox.value()
        self.previous_biceps_left_intensity = current_value
        self.ui.Biceps_left_spinBox.setValue(current_value + value)
        if self.save is True and self.start_state is True:
            self.save_modification()

    def set_deltoid_anterior_left_value(self, value: int):
        current_value = self.ui.Deltoide_anterior_left_spinBox.value()
        self.previous_deltoid_anterior_left_intensity = current_value
        self.ui.Deltoide_anterior_left_spinBox.setValue(current_value + value)
        if self.save is True and self.start_state is True:
            self.save_modification()

    def set_deltoid_posterior_left_value(self, value: int):
        current_value = self.ui.Deltoide_posterior_left_spinBox.value()
        self.previous_deltoid_posterior_left_intensity = current_value
        self.ui.Deltoide_posterior_left_spinBox.setValue(current_value + value)
        if self.save is True and self.start_state is True:
            self.save_modification()

    def update_current(self, val):
        if self.start_state is False:
            return
        if val == 1:
            self.worker.triceps_r_intensity = self.ui.Triceps_right_spinBox.value()
        elif val == 2:
            self.worker.biceps_r_intensity = self.ui.Biceps_right_spinBox.value()
        elif val == 3:
            self.worker.delt_ant_r_intensity = self.ui.Deltoide_anterior_right_spinBox.value()
        elif val == 4:
            self.worker.delt_post_r_intensity = self.ui.Deltoide_posterior_right_spinBox.value()
        elif val == 5:
            self.worker.triceps_l_intensity = self.ui.Triceps_left_spinBox.value()
        elif val == 6:
            self.worker.biceps_l_intensity = self.ui.Biceps_left_spinBox.value()
        elif val == 7:
            self.worker.delt_ant_l_intensity = self.ui.Deltoide_anterior_left_spinBox.value()
        elif val == 8:
            self.worker.delt_post_l_intensity = self.ui.Deltoide_posterior_left_spinBox.value()

    @QtCore.pyqtSlot(float)
    def angle_display(self, value: float):
        value = round(value)
        self.ui.angle_progressBar.setValue(value)
        self.ui.angle_label.setText(f"{value}°")

    @QtCore.pyqtSlot(dict)
    def activation_color(self, activation_list: dict):
        color_list = ["red"] * 8
        i = -1
        for stim_state in activation_list:
            i += 1
            if activation_list[stim_state] is True:
                color_list[i] = "green"

        self.ui.Triceps_right_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : " f"{color_list[0]};" "}")
        self.ui.Biceps_right_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : " f"{color_list[1]};" "}")
        self.ui.Deltoide_anterior_right_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : " f"{color_list[2]};" "}")
        self.ui.Deltoide_posterior_right_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : " f"{color_list[3]};" "}")
        self.ui.Triceps_left_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : " f"{color_list[4]};" "}")
        self.ui.Biceps_left_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : " f"{color_list[5]};" "}")
        self.ui.Deltoide_anterior_left_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : " f"{color_list[6]};" "}")
        self.ui.Deltoide_posterior_left_activation_checkBox.setStyleSheet(
            "QCheckBox::indicator" "{" "background-color : " f"{color_list[7]};" "}")

    def motomed_mode(self):
        if self.ui.Passive_radioButton.isChecked():
            self.ui.Gear_spinBox.setEnabled(False)
            self.ui.Speed_spinBox.setEnabled(True)
        else:
            self.ui.Gear_spinBox.setEnabled(True)
            self.ui.Speed_spinBox.setEnabled(False)

    def start_motomed(self):
        if self.ui.Forward_radioButton.isChecked():
            self.ui.Backward_radioButton.setEnabled(False)
        else:
            self.ui.Forward_radioButton.setEnabled(False)
        if self.ui.Passive_radioButton.isChecked():
            self.ui.Active_radioButton.setEnabled(False)
        else:
            self.ui.Passive_radioButton.setEnabled(False)
        self.ui.Start_motomed_pushButton.setEnabled(False)
        self.ui.Save_motomed_pushButton.setEnabled(False)
        self.ui.Pause_motomed_pushButton.setEnabled(True)
        self.ui.Stop_motomed_pushButton.setEnabled(True)

        self.speed = self.ui.Speed_spinBox.value()
        self.gear = self.ui.Gear_spinBox.value()
        self.direction = True if self.ui.Forward_radioButton.isChecked() else False
        self.mode = False if self.ui.Passive_radioButton.isChecked() else True

        if self.stimulator is None:
            self.stimulator = St(port="COM4", with_motomed=True, show_log=False, fast_mode=False)
            self.stimulator.motomed.init_phase_training(arm_training=True)

        self.stimulator.motomed.start_phase(speed=self.speed, gear=self.gear, active=self.mode,
                                            go_forward=self.direction, spasm_detection=True)

    def pause_motomed(self):
        if self.ui.Forward_radioButton.isChecked():
            self.ui.Backward_radioButton.setEnabled(True)
        else:
            self.ui.Forward_radioButton.setEnabled(True)
        if self.ui.Passive_radioButton.isChecked():
            self.ui.Active_radioButton.setEnabled(True)
        else:
            self.ui.Passive_radioButton.setEnabled(True)
        self.ui.Start_motomed_pushButton.setEnabled(True)
        self.ui.Pause_motomed_pushButton.setEnabled(False)
        self.ui.Stop_motomed_pushButton.setEnabled(True)

        self.stimulator.motomed.pause_training()

    def stop_motomed(self):
        if self.ui.Forward_radioButton.isChecked():
            self.ui.Backward_radioButton.setEnabled(True)
        else:
            self.ui.Forward_radioButton.setEnabled(True)
        if self.ui.Passive_radioButton.isChecked():
            self.ui.Active_radioButton.setEnabled(True)
        else:
            self.ui.Passive_radioButton.setEnabled(True)
        self.ui.Start_motomed_pushButton.setEnabled(True)
        self.ui.Save_motomed_pushButton.setEnabled(True)
        self.ui.Pause_motomed_pushButton.setEnabled(False)
        self.ui.Stop_motomed_pushButton.setEnabled(False)

        self.stimulator.motomed.stop_training()

    def save_motomed(self):
        folder = str(
            QFileDialog.getSaveFileName(None, "Save the time modification", '', "Text file (*.txt);;All Files (*)"))
        # self.folder = folder[2:-23]
        # self.save = True

    # def cursor_display(self):
    #     # Step 2: Create a QThread object
    #     self.thread = QThread()
    #     # Step 3: Create a worker object
    #     self.cursor_worker = Cursor()
    #     # Step 4: Move worker to the thread
    #     self.cursor_worker.moveToThread(self.thread)
    #     # Step 5: Connect signals and slots
    #     self.thread.started.connect(self.cursor_worker.stimulate)
    #     self.cursor_worker.finished.connect(self.thread.quit)
    #     self.cursor_worker.finished.connect(self.cursor_worker.deleteLater)
    #     self.thread.finished.connect(self.thread.deleteLater)
    #     # Step 6: Start the thread
    #     self.thread.start()
    #     self.cursor_worker.threadactive = True

# class Cursor(QObject):
#     def __init__(self):
#         super(Cursor, self).__init__()
#         self.window = QtWidgets.QMainWindow()
#         self.ui_cursor = Ui_CursorMainWindow()
#         self.ui_cursor.setupUi(self.window)
#         sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
#         sizePolicy.setHorizontalStretch(0)
#         sizePolicy.setVerticalStretch(0)
#
#         self.ui_cursor.horizontalSlider = QtWidgets.QSlider()
#         self.ui_cursor.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
#         self.ui_cursor.horizontalSlider.setMinimumSize(QtCore.QSize(0, 50))
#         self.ui_cursor.horizontalSlider.setMaximumSize(QtCore.QSize(20000, 100))
#         self.ui_cursor.horizontalSlider.setObjectName("horizontalSlider")
#         self.ui_cursor.horizontalSlider.setSizePolicy(sizePolicy)
#         self.ui_cursor.gridLayout.addWidget(self.ui_cursor.horizontalSlider, 0, 0, 0, 0)
#         self.ui_cursor.horizontalSlider.setMaximum(100)
#         self.ui_cursor.horizontalSlider.setValue(50)
#         self.ui_cursor.horizontalSlider.setEnabled(False)
#
#         self.window.show()
#
#         self.ui_cursor.Start_pushButton.clicked.connect(self.cursor_display)
#
#
#     def cursor_display(self):
#         # Step 2: Create a QThread object
#         self.thread = QThread()
#         # Step 3: Create a worker object
#         self.cursor_worker = Cursor()
#         # Step 4: Move worker to the thread
#         self.cursor_worker.moveToThread(self.thread)
#         # Step 5: Connect signals and slots
#         self.thread.started.connect(self.cursor_worker.stimulate)
#         self.cursor_worker.finished.connect(self.thread.quit)
#         self.cursor_worker.finished.connect(self.cursor_worker.deleteLater)
#         self.thread.finished.connect(self.thread.deleteLater)
#         # Step 6: Start the thread
#         self.thread.start()
#         self.cursor_worker.threadactive = True

    # def position:


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = App()
    gui.show()
    app.exec()
