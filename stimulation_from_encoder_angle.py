import threading
import time
import nidaqmx
from pyScienceMode2.rehastim_interface import Stimulator as St
from pyScienceMode2 import Channel as Ch


class RehastimEncoder:

    def __init__(self):
        # Create a list of channels
        self.list_channels = []

        # Create all channels possible
        channel_1 = Ch.Channel(mode="Single", no_channel=1, amplitude=0, pulse_width=150, name="Triceps_r")
        channel_2 = Ch.Channel(mode="Single", no_channel=2, amplitude=0, pulse_width=150, name="Biceps_r")
        # channel_3 = Ch.Channel(mode="Single", no_channel=3, amplitude=0, pulse_width=150, name="Delt_ant_r")
        # channel_4 = Ch.Channel(mode="Single", no_channel=4, amplitude=0, pulse_width=150, name="Delt_post_r")
        # channel_5 = Ch.Channel(mode="Single", no_channel=5, amplitude=0, pulse_width=150, name="Triceps_l")
        # channel_6 = Ch.Channel(mode="Single", no_channel=6, amplitude=0, pulse_width=150, name="Biceps_l")
        # channel_7 = Ch.Channel(mode="Single", no_channel=7, amplitude=0, pulse_width=150, name="Delt_ant_l")
        # channel_8 = Ch.Channel(mode="Single", no_channel=8, amplitude=0, pulse_width=150, name="Delt_post_l")

        # Choose which channel will be used
        self.list_channels.append(channel_1)
        self.list_channels.append(channel_2)
        # self.list_channels.append(channel_3)
        # self.list_channels.append(channel_4)
        # self.list_channels.append(channel_5)
        # self.list_channels.append(channel_6)
        # self.list_channels.append(channel_7)
        # self.list_channels.append(channel_8)

        # Set the intensity for each muscles
        self.biceps_r_intensity = 20
        self.triceps_r_intensity = 20
        self.delt_ant_r_intensity = 20
        self.delt_post_r_intensity = 20
        self.biceps_l_intensity = 20
        self.triceps_l_intensity = 20
        self.delt_ant_l_intensity = 20
        self.delt_post_l_intensity = 20

        # Create our object Stimulator
        self.stimulator = St(port="COM4", with_motomed=False, show_log=False, fast_mode=True)
        self.stimulator.init_channel(stimulation_interval=30, list_channels=self.list_channels, low_frequency_factor=0)

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

            # Not used in ths program
            # from nidaqmx.constants import AcquisitionType
            # self.task2.timing.cfg_samp_clk_timing(rate=1000,
            #                                       sample_mode=AcquisitionType.CONTINUOUS,
            #                                       samps_per_chan=10)

            self.task2.start()

            self.min_voltage = 1.33
            max_voltage = 5
            self.origin = self.task2.read() - self.min_voltage
            self.angle_coeff = 360/(max_voltage-self.min_voltage)
            # Future development with eccentric mode
            direction = "concentric"

    def get_angle(self):
        voltage = self.task2.read() - self.min_voltage
        self.actual_voltage = voltage - self.origin
        self.angle = 360 - (self.actual_voltage * self.angle_coeff) if 0 < self.actual_voltage <= 5 - self.origin else \
                     abs(self.actual_voltage) * self.angle_coeff

    def stimulate(self):

        self.stimulator.start_stimulation(upd_list_channels=self.list_channels)

        # trigger_list = [0, 0]

        self.stimulation_state = {"Triceps_r": False, "Biceps_r": False, "Delt_ant_r": False, "Delt_post_r": False,
                                  "Triceps_l": False, "Biceps_l": False, "Delt_ant_l": False, "Delt_post_l": False}

        while 1:
            # start_time = time.time()

            self.get_angle()

            # Phase 1 / From 0° to 10°
            # right biceps and deltoid posterior activated
            if 0 <= self.angle < 10 and self.stimulation_state["Biceps_r"] + self.stimulation_state["Delt_post_r"] != 2:
                for list_chan in self.list_channels:
                    list_chan.set_amplitude(0)
                self.list_channels[1].set_amplitude(self.biceps_r_intensity)
                # self.list_channels[3].set_amplitude(self.delt_post_r_intensity)
                self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
                for stim_state in self.stimulation_state:
                    self.stimulation_state[stim_state] = False
                self.stimulation_state["Biceps_r"] = True
                self.stimulation_state["Delt_post_r"] = True
                # trigger_list.append(1)

                print("angle : ", self.angle, "phase : ", 1)

            # Phase 2 / From 10° to 20°
            # no muscle activated
            elif 10 <= self.angle < 20 and all(a == 0 for a in self.stimulation_state.values()) is False:
                for list_chan in self.list_channels:
                    list_chan.set_amplitude(0)
                self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
                for stim_state in self.stimulation_state:
                    self.stimulation_state[stim_state] = False
                # trigger_list.append(2)

                print("angle : ", self.angle, "phase : ", 2)

            # Phase 3 / From 20° to 40°
            # right triceps and deltoid anterior activated
            elif 20 <= self.angle < 40 and self.stimulation_state["Triceps_r"] + self.stimulation_state["Delt_ant_r"] != 2:
                for list_chan in self.list_channels:
                    list_chan.set_amplitude(0)
                self.list_channels[0].set_amplitude(self.triceps_r_intensity)
                # self.list_channels[2].set_amplitude(self.delt_ant_r_intensity)
                self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
                for stim_state in self.stimulation_state:
                    self.stimulation_state[stim_state] = False
                self.stimulation_state["Triceps_r"] = True
                self.stimulation_state["Delt_ant_r"] = True
                # trigger_list.append(3)

                print("angle : ", self.angle, "phase : ", 3)

            # Phase 4 / From 40° to 180°
            # right triceps, right deltoid anterior, left biceps and left deltoid posterior activated
            elif 40 <= self.angle < 180 and self.stimulation_state["Triceps_r"] + self.stimulation_state["Delt_ant_r"]\
                    + self.stimulation_state["Biceps_l"] + self.stimulation_state["Delt_post_l"] != 4:
                for list_chan in self.list_channels:
                    list_chan.set_amplitude(0)
                self.list_channels[0].set_amplitude(self.triceps_r_intensity)
                # self.list_channels[2].set_amplitude(self.delt_ant_r_intensity)
                # self.list_channels[5].set_amplitude(self.biceps_l_intensity)
                # self.list_channels[7].set_amplitude(self.delt_post_l_intensity)
                self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
                for stim_state in self.stimulation_state:
                    self.stimulation_state[stim_state] = False
                self.stimulation_state["Triceps_r"] = True
                self.stimulation_state["Delt_ant_r"] = True
                self.stimulation_state["Biceps_l"] = True
                self.stimulation_state["Delt_post_l"] = True
                # trigger_list.append(4)

                print("angle : ", self.angle, "phase : ", 4)

            # Phase 5 / From 180° to 190°
            # left biceps and left deltoid posterior activated
            elif 180 <= self.angle < 190 and self.stimulation_state["Triceps_r"] + self.stimulation_state["Delt_ant_r"]\
                    + self.stimulation_state["Biceps_l"] + self.stimulation_state["Delt_post_l"] != 2:
                for list_chan in self.list_channels:
                    list_chan.set_amplitude(0)
                # self.list_channels[5].set_amplitude(self.biceps_l_intensity)
                # self.list_channels[7].set_amplitude(self.delt_post_l_intensity)
                self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
                for stim_state in self.stimulation_state:
                    self.stimulation_state[stim_state] = False
                self.stimulation_state["Biceps_l"] = True
                self.stimulation_state["Delt_post_l"] = True
                # trigger_list.append(5)

                print("angle : ", self.angle, "phase : ", 5)

            # Phase 6 / From 190° to 200°
            # no muscle activated
            elif 190 <= self.angle < 200 and all(a == 0 for a in self.stimulation_state.values()) is False:
                for list_chan in self.list_channels:
                    list_chan.set_amplitude(0)
                self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
                for stim_state in self.stimulation_state:
                    self.stimulation_state[stim_state] = False
                # trigger_list.append(6)

                print("angle : ", self.angle, "phase : ", 6)

            # Phase 7 / From 200° to 220°
            # left triceps and left deltoid anterior activated
            elif 200 <= self.angle < 220 and self.stimulation_state["Triceps_l"] + self.stimulation_state["Delt_ant_l"] != 2:
                for list_chan in self.list_channels:
                    list_chan.set_amplitude(0)
                # self.list_channels[4].set_amplitude(self.triceps_l_intensity)
                # self.list_channels[6].set_amplitude(self.delt_ant_l_intensity)
                self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
                for stim_state in self.stimulation_state:
                    self.stimulation_state[stim_state] = False
                self.stimulation_state["Triceps_l"] = True
                self.stimulation_state["Delt_ant_l"] = True
                # trigger_list.append(7)

                print("angle : ", self.angle, "phase : ", 7)

            # Phase 8 / From 220° to 360°
            # right biceps, right deltoid posterior, left triceps and left deltoid anterior activated
            elif 220 <= self.angle < 360 and self.stimulation_state["Biceps_r"] + self.stimulation_state["Delt_post_r"]\
                    + self.stimulation_state["Triceps_l"] + self.stimulation_state["Delt_ant_l"] != 4:
                for list_chan in self.list_channels:
                    list_chan.set_amplitude(0)
                self.list_channels[1].set_amplitude(self.biceps_r_intensity)
                # self.list_channels[3].set_amplitude(self.delt_post_r_intensity)
                # self.list_channels[4].set_amplitude(self.triceps_l_intensity)
                # self.list_channels[6].set_amplitude(self.delt_ant_l_intensity)
                self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
                for stim_state in self.stimulation_state:
                    self.stimulation_state[stim_state] = False
                self.stimulation_state["Biceps_r"] = True
                self.stimulation_state["Delt_post_r"] = True
                self.stimulation_state["Triceps_l"] = True
                self.stimulation_state["Delt_ant_l"] = True
                # trigger_list.append(8)

                print("angle : ", self.angle, "phase : ", 8)

            # if trigger_list[-1] != trigger_list[-2]:
            #     a += 1
            #     trigger_list = [trigger_list[-1], trigger_list[-1]]
            #     self.stimulator.start_stimulation(upd_list_channels=self.list_channels)
            #     print("angle : ", self.angle, trigger_list[-1])
            #     self.get_angle()
            #     print("current angle : ", self.angle)
            #     print("voltage : ", self.actual_voltage)

            # end_time = time.time()
            # loop_time = end_time - start_time
            # print("loop time : ", loop_time)


if __name__ == "__main__":
    stim_class = RehastimEncoder()
    stim_class.stimulate()

    # creating thread
    # t1 = threading.Thread(target=stim_class.get_angle)
    # t2 = threading.Thread(target=stim_class.stimulate)
    #
    # # starting thread 1
    # t1.start()
    # # starting thread 2
    # t2.start()
    #
    # # wait until thread 1 is completely executed
    # t1.join()
    # # wait until thread 2 is completely executed
    # t2.join()
    #
    # start_time = time.time()
