from pyScienceMode2 import Channel, Point, Device, Modes
from pyScienceMode2 import RehastimP24 as St
from pyScienceMode2 import Rehastim2 as St2
import random
from time import sleep
from sciencemode import sciencemode
from biosiglive import ViconClient, DeviceType
import numpy as np


def get_trigger():
    interface = init_trigger()
    interface.get_frame()
    interface.add_device(
        nb_channels=2,
        device_type=DeviceType.Generic,
        name="stim",
        rate=10000,
    )
    # break when everything is started
    while True:
        trigger_data = interface.get_device_data(device_name="stim")[1:, :]
        idx = np.argwhere(trigger_data > 1.5)
        if len(idx) > 0:
            stimulator2.start_stimulation(upd_list_channels=list_channels, stimulation_duration=1)
            # break

#
# def init_trigger(self):
#     self.interface = ViconClient(ip="127.0.0.1", system_rate=100, init_now=True)

def init_trigger():
    interface = ViconClient(ip="192.168.1.211", system_rate=100, init_now=True)
    return interface

# stimulator2 = St2(port="COM3", show_log=True)


def test_custom_shape_pulse():
    """
    Test of the new feature : custom shape pulse
    """

    channel_1 = Channel(no_channel=1, name="Biceps", amplitude=30, frequency=20,
                        device_type=Device.Rehastimp24)

    list_channels.append(channel_1)

    stimulatorp24.init_stimulation(list_channels=list_channels)

    # Test pulse with only one point
    point1 = channel_1.add_point(300, 20)
    stimulatorp24.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2, safety=False)

    # Test biphasic pulse
    point2 = channel_1.add_point(300, -20)
    stimulatorp24.update_stimulation(upd_list_channels=list_channels)

    # Test random shape pulse with 6 points
    point3 = channel_1.add_point(300, 10)
    point4 = channel_1.add_point(300, -10)
    point5 = channel_1.add_point(300, 5)
    point6 = channel_1.add_point(300, -5)
    stimulatorp24.update_stimulation(upd_list_channels=list_channels)

    # Test random shape pulse with 16 points
    channel_1.list_point.clear()  # Clear the list of points to create a new one
    for i in range(16):
        amplitude = random.randint(-130, 130)
        duration = random.randint(0, 4095)
        channel_1.add_point(duration, amplitude)
    stimulatorp24.update_stimulation(upd_list_channels=list_channels)
    stimulatorp24.end_stimulation()
    list_channels.clear()
    channel_1.list_point.clear()


def test_single_doublet_triplet(device: Device):
    """
    Mode test (single, doublet, triplet)
    """
    if device == Device.Rehastimp24:
        channel_1 = Channel(mode=Modes.SINGLE, no_channel=1, name="Biceps", amplitude=30, pulse_width=350, frequency=20,
                            device_type=Device.Rehastimp24)
        channel_2 = Channel(mode=Modes.DOUBLET, no_channel=2, name="Biceps", amplitude=30, frequency=20,
                            pulse_width=350,
                            device_type=Device.Rehastimp24)
        channel_3 = Channel(mode=Modes.TRIPLET, no_channel=3, name="Biceps", amplitude=30, frequency=20,
                            pulse_width=350,
                            device_type=Device.Rehastimp24)

        list_channels.append(channel_1)
        list_channels.append(channel_2)
        list_channels.append(channel_3)

        stimulatorp24.init_stimulation(list_channels=list_channels)
        stimulatorp24.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2, safety=True)

        channel_1.set_mode(Modes.DOUBLET)
        channel_2.set_mode(Modes.TRIPLET)
        channel_3.set_mode(Modes.SINGLE)

        stimulatorp24.update_stimulation(upd_list_channels=list_channels)
        channel_1.set_mode(Modes.TRIPLET)
        channel_2.set_mode(Modes.SINGLE)
        channel_3.set_mode(Modes.DOUBLET)

        stimulatorp24.update_stimulation(upd_list_channels=list_channels)
        stimulatorp24.end_stimulation()
        list_channels.clear()
        channel_1.list_point.clear()
        channel_2.list_point.clear()
        channel_3.list_point.clear()
    if device == Device.Rehastim2:
        channel_1 = Channel(mode=Modes.SINGLE, no_channel=1, name="Biceps", amplitude=30, pulse_width=350,
                            device_type=Device.Rehastim2)
        channel_2 = Channel(mode=Modes.DOUBLET, no_channel=2, name="Biceps", amplitude=30,
                            pulse_width=350,
                            device_type=Device.Rehastim2)
        channel_3 = Channel(mode=Modes.TRIPLET, no_channel=3, name="Biceps", amplitude=30,
                            pulse_width=350,
                            device_type=Device.Rehastim2)

        list_channels.append(channel_1)
        list_channels.append(channel_2)
        list_channels.append(channel_3)
        # TODO example pour montrer que pour changer de mode il faut reinitialiser le channel a nouveau.
        stimulator2.init_channel(list_channels=list_channels, stimulation_interval=8)
        stimulator2.start_stimulation(stimulation_duration=2)
        channel_1.set_mode(Modes.DOUBLET)
        channel_2.set_mode(Modes.TRIPLET)
        channel_3.set_mode(Modes.SINGLE)
        stimulator2.init_channel(list_channels=list_channels, stimulation_interval=8)
        stimulator2.start_stimulation(stimulation_duration=2)
        channel_1.set_mode(Modes.TRIPLET)
        channel_2.set_mode(Modes.SINGLE)
        channel_3.set_mode(Modes.DOUBLET)
        stimulator2.init_channel(list_channels=list_channels, stimulation_interval=8)
        stimulator2.start_stimulation(stimulation_duration=2)
        stimulator2.end_stimulation()

        list_channels.clear()


def test_frequency(device: Device):
    if device == Device.Rehastimp24:
        channel_1 = Channel(mode=Modes.SINGLE, no_channel=1, name="Biceps", amplitude=30, pulse_width=350, frequency=20,
                            device_type=Device.Rehastimp24)
        list_channels.append(channel_1)

        # Test with 20Hz
        stimulatorp24.init_stimulation(list_channels=list_channels)
        stimulatorp24.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2, safety=True)

        # Test with 10Hz
        channel_1.set_frequency(10)
        stimulatorp24.update_stimulation(upd_list_channels=list_channels)

        # Test with 100Hz
        channel_1.set_frequency(100)
        stimulatorp24.update_stimulation(upd_list_channels=list_channels)

        # Test 3 channels with different frequencies
        channel_1.set_frequency(25)
        channel_2 = Channel(mode=Modes.SINGLE, no_channel=2, name="Biceps", amplitude=30, pulse_width=350, frequency=10,
                            device_type=Device.Rehastimp24)
        channel_3 = Channel(mode=Modes.SINGLE, no_channel=3, name="Biceps", amplitude=30, pulse_width=350, frequency=50,
                            device_type=Device.Rehastimp24)
        list_channels.append(channel_2)
        list_channels.append(channel_3)
        stimulatorp24.init_stimulation(list_channels=list_channels)

        stimulatorp24.update_stimulation(upd_list_channels=list_channels)
        stimulatorp24.end_stimulation()
        list_channels.clear()
        channel_1.list_point.clear()
    else:
        channel_1 = Channel(mode=Modes.SINGLE, no_channel=1, name="Biceps", amplitude=30, pulse_width=350,
                            device_type=Device.Rehastim2)
        list_channels.append(channel_1)
        stimulator2.init_channel(list_channels=list_channels, stimulation_interval=100)
        stimulator2.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2)
        stimulator2.init_channel(list_channels=list_channels, stimulation_interval=20)
        stimulator2.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2)
        stimulator2.init_channel(list_channels=list_channels, stimulation_interval=10)
        stimulator2.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2)
        stimulator2.end_stimulation()
        list_channels.clear()

def test_force_rehastim2():
    channel_1 = Channel(mode=Modes.SINGLE, no_channel=1, name="Biceps", amplitude=30, pulse_width=300,
                        device_type=Device.Rehastim2)

    list_channels.append(channel_1)
    for i in range(10):
        stimulator2.init_channel(list_channels=list_channels, stimulation_interval=33)
        stimulator2.start_stimulation(stimulation_duration=1)
        sleep(1)
    stimulator2.end_stimulation()
    stimulator2.disconnect()
    list_channels.clear()


def test_force_rehastimp24():
    # channel_1 = Channel(mode=Modes.SINGLE, no_channel=1, name="Biceps", amplitude=30, pulse_width=300, frequency=30.3,
    #                     device_type=Device.Rehastimp24)
    # list_channels.append(channel_1)
    point11 = Point(300, 20)
    point22 = Point(300, -20)
    list_points.append(point11)
    list_points.append(point22)
    for i in range(5):
        stimulatorp24.start_stim_one_channel_stimulation(no_channel=1, points=list_points, pulse_duration=0.3,
                                                         total_duration=1, pulse_interval=33, safety=True)
        sleep(1)
    # stimulatorp24.init_stimulation(list_channels=list_channels)
    # for i in range(10):
    #     stimulatorp24.init_stimulation(list_channels=list_channels)
    #     stimulatorp24.start_stimulation(upd_list_channels=list_channels, stimulation_duration=1, safety=True)
    #     stimulatorp24.end_stimulation()
    #     sleep(1)
    # stimulatorp24.end_stimulation()
    list_channels.clear()
    list_points.clear()


def more_than_16_points():
    channel_1 = Channel(no_channel=1, name="Biceps", frequency=20, device_type=Device.Rehastimp24)

    # Need to remove the max_point condition in channel.py (add_point function)
    list_channels.append(channel_1)
    stimulatorp24.init_stimulation(list_channels=list_channels)
    for i in range(8):
        channel_1.add_point(300, 20)
        channel_1.add_point(300, -20)
    print(len(channel_1.list_point))
    stimulatorp24.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2, safety=False)
    # channel_1.add_point(300, 20)
    stimulatorp24.update_stimulation(upd_list_channels=list_channels)
    stimulatorp24.end_stimulation()

    # Same thing but with the low level mode
    for point in channel_1.list_point:
        list_points.append(point)
    print(len(list_points))
    point17 = Point(300, 20)
    list_points.append(
        point17)  # Raise an error IndexError: index too large for cdata 'Smpt_point[16]' (expected 16 < 16)

    stimulatorp24.start_stim_one_channel_stimulation(no_channel=1, points=list_points, stim_sequence=100,
                                                     pulse_interval=33,
                                                     safety=False)
    stimulatorp24.end_stim_one_channel()

    list_channels.clear()
    list_points.clear()
    channel_1.list_point.clear()


def update_parameters():
    channel_1 = Channel(mode=Modes.SINGLE, no_channel=1, name="Biceps", amplitude=20, pulse_width=350, frequency=50,
                        device_type=Device.Rehastimp24)
    list_channels.append(channel_1)
    stimulatorp24.init_stimulation(list_channels=list_channels)
    stimulatorp24.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2, safety=True)
    channel_1.set_frequency(10)
    stimulatorp24.update_stimulation(upd_list_channels=list_channels)
    channel_1.set_amplitude(10)
    stimulatorp24.update_stimulation(upd_list_channels=list_channels)
    channel_1.set_pulse_width(500)
    stimulatorp24.update_stimulation(upd_list_channels=list_channels)
    channel_1.set_mode(Modes.TRIPLET)
    stimulatorp24.update_stimulation(upd_list_channels=list_channels)
    channel_1.set_frequency(20)
    channel_1.set_amplitude(20)
    channel_1.set_pulse_width(350)
    channel_1.set_mode(Modes.SINGLE)
    channel_1.set_no_channel(2)
    stimulatorp24.init_stimulation(list_channels=list_channels)
    sleep(2)
    stimulatorp24.update_stimulation(upd_list_channels=list_channels)
    stimulatorp24.end_stimulation()

    list_channels.clear()
    channel_1.list_point.clear()


def test_diff_frequency_ll_ml(frequency):
    channel_1 = Channel(no_channel=1, name="Biceps", amplitude=20, pulse_width=350,
                        frequency=frequency,
                        device_type=Device.Rehastimp24)
    list_channels.append(channel_1)
    stimulatorp24.init_stimulation(list_channels=list_channels)

    channel_1.add_point(300, 20)
    channel_1.add_point(300, -20)
    # channel_1.add_point(300, 20)
    # channel_1.add_point(300, -20)

    stimulatorp24.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2, safety=True)
    stimulatorp24.end_stimulation()

    for point in channel_1.list_point:
        list_points.append(point)
        print(point.pulse_width, point.amplitude)
    sleep(2)
    stimulatorp24.start_stim_one_channel_stimulation(no_channel=1, points=list_points, stim_sequence=100,
                                                     pulse_interval=1000 / frequency)
    stimulatorp24.end_stim_one_channel()
    stimulatorp24.ll_init()
    compteur = 0
    sleep(2)
    while compteur < 200:
        stimulatorp24.single_pulse(no_channel=1, points=list_points)
        sleep(1 / frequency)
        compteur += 1
    stimulatorp24.end_stim_one_channel()
    list_channels.clear()
    list_points.clear()
    channel_1.list_point.clear()


def communication_speed():
    """
    For RehastimP24
    change the function to just send a pulse with no predefined frequency.
    """
    stimulatorp24.ll_init()  # 15140 - 1530
    point1 = Point(100, 20)
    point2 = Point(100, -20)
    list_points.append(point1)
    list_points.append(point2)

    waiting_time = 1
    ll_config = sciencemode.ffi.new("Smpt_ll_channel_config*")
    ll_config.enable_stimulation = True
    ll_config.channel = sciencemode.Smpt_Channel_Red
    ll_config.connector = sciencemode.Smpt_Connector_Yellow
    ll_config.number_of_points = len(list_points)
    ll_config.points[0].time = list_points[0].pulse_width
    ll_config.points[0].current = list_points[0].amplitude
    ll_config.points[1].time = list_points[1].pulse_width
    ll_config.points[1].current = list_points[1].amplitude
    while True:
        ll_config.packet_number = sciencemode.smpt_packet_number_generator_next(stimulatorp24.device)
        sciencemode.lib.smpt_send_ll_channel_config(stimulatorp24.device, ll_config)
        # stimulatorp24.single_pulse(no_channel=1, points=list_points)

        sleep(waiting_time)
        waiting_time *= 0.9
        print(waiting_time)


def test_limit(device: Device):
    if device == Device.Rehastimp24:
        channel_1 = Channel(no_channel=1, name="Biceps",
                            frequency=15,
                            device_type=Device.Rehastimp24)
        list_channels.append(channel_1)
        for i in range(8):
            channel_1.add_point(4095, 130)
            channel_1.add_point(4095, -130)
        stimulatorp24.init_stimulation(list_channels=list_channels)
        stimulatorp24.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2, safety=True)
        stimulatorp24.end_stimulation()
        list_channels.clear()
        channel_1.list_point.clear()
    else:
        list_channels.clear()
        channel_1 = Channel(mode=Modes.SINGLE, no_channel=1, pulse_width=500, amplitude=130, name="Biceps",
                            device_type=Device.Rehastim2)
        list_channels.append(channel_1)
        stimulator2.init_channel(list_channels=list_channels, stimulation_interval=8)
        stimulator2.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2)


def communication_speed_r2():
    channel_1 = Channel(
        mode=Modes.SINGLE,
        no_channel=2,
        amplitude=10,
        pulse_width=100,
        name="Biceps",
        device_type=Device.Rehastim2,
    )

    list_channels.append(channel_1)
    stimulator2.init_channel(stimulation_interval=8, list_channels=list_channels)
    amplitude = 10

    waiting_time = 1
    while True:
        stimulator2.start_stimulation(stimulation_duration=0.025)
        amplitude *= 1.01
        channel_1.set_amplitude(amplitude)
        sleep(waiting_time)
        waiting_time *= 0.9
        print(waiting_time)


def decalage(freq1, freq2, freq3, device: Device):
    if device == Device.Rehastimp24:
        channel_1 = Channel(mode=Modes.SINGLE, no_channel=1, name="Biceps", amplitude=20, pulse_width=350,
                            frequency=freq1,
                            device_type=Device.Rehastimp24)
        channel_2 = Channel(mode=Modes.TRIPLET, no_channel=2, name="Biceps", amplitude=20, pulse_width=350,
                            frequency=freq2,
                            device_type=Device.Rehastimp24)
        channel_3 = Channel(mode=Modes.TRIPLET, no_channel=3, name="Biceps", amplitude=20, pulse_width=350,
                            frequency=freq3,
                            device_type=Device.Rehastimp24)
        list_channels.append(channel_1)
        list_channels.append(channel_2)
        list_channels.append(channel_3)
        stimulatorp24.init_stimulation(list_channels=list_channels)
        stimulatorp24.start_stimulation(upd_list_channels=list_channels, stimulation_duration=3, safety=True)
        stimulatorp24.end_stimulation()
        list_channels.clear()
        channel_1.list_point.clear()
        channel_2.list_point.clear()
        channel_3.list_point.clear()
    if device == Device.Rehastim2:
        list_channels.clear()
        channel_1 = Channel(mode=Modes.SINGLE, no_channel=1, name="Biceps", amplitude=20, pulse_width=350,
                            device_type=Device.Rehastim2)
        channel_2 = Channel(mode=Modes.TRIPLET, no_channel=2, name="Biceps", amplitude=20, pulse_width=350,
                            device_type=Device.Rehastim2)
        channel_3 = Channel(mode=Modes.TRIPLET, no_channel=3, name="Biceps", amplitude=20, pulse_width=350,
                            device_type=Device.Rehastim2)
        list_channels.append(channel_1)
        list_channels.append(channel_2)
        list_channels.append(channel_3)
        stimulator2.init_channel(list_channels=list_channels, stimulation_interval=50)
        stimulator2.start_stimulation(stimulation_duration=3)
        stimulator2.end_stimulation()
        stimulator2.disconnect()


def exe():
    channel_1 = Channel(no_channel=1, name="Biceps", amplitude=20, pulse_width=350, frequency=50,
                        device_type=Device.Rehastimp24)
    list_channels.append(channel_1)
    stimulatorp24.init_stimulation(list_channels=list_channels)
    channel_1.add_point(350, 20)
    channel_1.add_point(350, -20)
    channel_1.add_point(350, 10)
    channel_1.add_point(350, -10)

    stimulatorp24.start_stimulation(upd_list_channels=list_channels, stimulation_duration=2, safety=True)
    stimulatorp24.end_stimulation()
    list_channels.clear()
    channel_1.list_point.clear()


# test_force_rehastim2()
# test_force_rehastimp24()
# test_frequency()
# test_single_doublet_triplet(Device.Rehastim2)
# test_custom_shape_pulse()
# more_than_16_points()
# update_parameters()
# test_diff_frequency_ll_ml(50)
# communication_speed()
# test_limit(device=Device.Rehastim2)
# communication_speed_r2()
# decalage(50, 25, 25, Device.Rehastim2)
# exe()

if __name__ == '__main__':

    stimulator2 = St2(port="COM5", show_log=False)
    list_points = []
    list_channels = []
    channel_1 = Channel(mode=Modes.SINGLE, no_channel=1, name="Biceps", amplitude=30, pulse_width=350,
                        device_type=Device.Rehastim2)
    list_channels.append(channel_1)
    stimulator2.init_channel(stimulation_interval=8, list_channels=list_channels)
    get_trigger()
