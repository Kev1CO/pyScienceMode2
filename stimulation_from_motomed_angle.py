from pyScienceMode2.rehastim_interface import Stimulator as St
from pyScienceMode2 import Channel as Ch

biceps_r_intensity = 20
triceps_r_intensity = 20
delt_ant_r_intensity = 20
delt_post_r_intensity = 20
biceps_l_intensity = 20
triceps_l_intensity = 20
delt_ant_l_intensity = 20
delt_post_l_intensity = 20


def init_rehastim():
    # Create a list of channels
    list_channels = []

    # Create all channels possible
    channel_1 = Ch.Channel(mode="Single", no_channel=7, amplitude=10, pulse_width=150, name="Triceps_r")
    channel_2 = Ch.Channel(mode="Single", no_channel=8, amplitude=10, pulse_width=150, name="Biceps_r")
    channel_3 = Ch.Channel(mode="Single", no_channel=3, amplitude=10, pulse_width=150, name="Delt_ant_r")
    channel_4 = Ch.Channel(mode="Single", no_channel=4, amplitude=10, pulse_width=150, name="Delt_post_r")
    channel_5 = Ch.Channel(mode="Single", no_channel=5, amplitude=10, pulse_width=150, name="Triceps_l")
    channel_6 = Ch.Channel(mode="Single", no_channel=6, amplitude=10, pulse_width=150, name="Biceps_l")
    channel_7 = Ch.Channel(mode="Single", no_channel=7, amplitude=10, pulse_width=150, name="Delt_ant_l")
    channel_8 = Ch.Channel(mode="Single", no_channel=8, amplitude=10, pulse_width=150, name="Delt_post_l")

    # Choose which channel will be used
    list_channels.append(channel_1)
    list_channels.append(channel_2)
    list_channels.append(channel_3)
    list_channels.append(channel_4)
    list_channels.append(channel_5)
    list_channels.append(channel_6)
    list_channels.append(channel_7)
    list_channels.append(channel_8)

    # Create our object Stimulator
    stimulator = St(port="COM4", with_motomed=True, show_log=False)
    stimulator.init_channel(stimulation_interval=30, list_channels=list_channels, low_frequency_factor=0)

    return stimulator, list_channels


if __name__ == "__main__":

    stimulator, list_channels = init_rehastim()
    motomed = stimulator.motomed

    list_channels[0].set_amplitude(0)
    list_channels[1].set_amplitude(0)
    list_channels[2].set_amplitude(0)
    list_channels[3].set_amplitude(0)
    list_channels[4].set_amplitude(0)
    list_channels[5].set_amplitude(0)
    list_channels[6].set_amplitude(0)
    list_channels[7].set_amplitude(0)

    # motomed.start_basic_training(arm_training=True)
    stimulator.start_stimulation(upd_list_channels=list_channels)
    # motomed.set_speed(60)
    motomed.init_phase_training(arm_training=True)
    motomed.start_phase(speed=30, gear=5, active=False, go_forward=True, spasm_detection=True)

    a = 0
    trigger_list = [0, 0]

    while 1:

        angle_crank = motomed.get_angle()
        # print(angle_crank)

        # Phase 1 / From 0° to 10°
        # right biceps and deltoid posterior activated
        if 0 <= angle_crank < 10:
            for list_chan in list_channels:
                list_chan.set_amplitude(0)
            list_channels[1].set_amplitude(biceps_r_intensity)
            list_channels[3].set_amplitude(delt_post_r_intensity)
            trigger_list.append(1)

        # Phase 2 / From 10° to 20°
        # no muscle activated
        elif 10 <= angle_crank < 20:
            for list_chan in list_channels:
                list_chan.set_amplitude(0)
            trigger_list.append(2)

        # Phase 3 / From 20° to 40°
        # right triceps and deltoid anterior activated
        elif 20 <= angle_crank < 40:
            for list_chan in list_channels:
                list_chan.set_amplitude(0)
            list_channels[0].set_amplitude(triceps_r_intensity)
            list_channels[2].set_amplitude(delt_ant_r_intensity)
            trigger_list.append(3)

        # Phase 4 / From 40° to 180°
        # right triceps, right deltoid anterior, left biceps and left deltoid posterior activated
        elif 40 <= angle_crank < 180:
            for list_chan in list_channels:
                list_chan.set_amplitude(0)
            list_channels[0].set_amplitude(triceps_r_intensity)
            list_channels[2].set_amplitude(delt_ant_r_intensity)
            list_channels[5].set_amplitude(biceps_l_intensity)
            list_channels[7].set_amplitude(delt_post_l_intensity)
            trigger_list.append(4)

        # Phase 5 / From 180° to 190°
        # left biceps and left deltoid posterior activated
        elif 180 <= angle_crank < 190:
            for list_chan in list_channels:
                list_chan.set_amplitude(0)
            list_channels[5].set_amplitude(biceps_l_intensity)
            list_channels[7].set_amplitude(delt_post_l_intensity)
            trigger_list.append(5)

        # Phase 6 / From 190° to 200°
        # no muscle activated
        elif 190 <= angle_crank < 200:
            for list_chan in list_channels:
                list_chan.set_amplitude(0)
            trigger_list.append(6)

        # Phase 7 / From 200° to 220°
        # left triceps and left deltoid anterior activated
        elif 200 <= angle_crank < 220:
            for list_chan in list_channels:
                list_chan.set_amplitude(0)
            list_channels[4].set_amplitude(triceps_l_intensity)
            list_channels[6].set_amplitude(delt_ant_l_intensity)
            trigger_list.append(7)

        # Phase 8 / From 220° to 360°
        # right biceps, right deltoid posterior, left triceps and left deltoid anterior activated
        elif 220 <= angle_crank < 360:
            for list_chan in list_channels:
                list_chan.set_amplitude(0)
            list_channels[1].set_amplitude(biceps_r_intensity)
            list_channels[3].set_amplitude(delt_post_r_intensity)
            list_channels[4].set_amplitude(triceps_l_intensity)
            list_channels[6].set_amplitude(delt_ant_l_intensity)
            trigger_list.append(8)

        if trigger_list[-1] != trigger_list[-2]:
            a += 1
            trigger_list = [trigger_list[-1], trigger_list[-1]]
            stimulator.start_stimulation(upd_list_channels=list_channels)
            print("angle : ", angle_crank, trigger_list[-1])
