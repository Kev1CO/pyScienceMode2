import time

from pyScienceMode2.rehastim_interface import Stimulator as St
from pyScienceMode2 import Channel as Ch


# Create a list of channels
list_channels = []

# Create all channels possible
channel_1 = Ch.Channel(mode="Single", no_channel=1, amplitude=0, pulse_width=150, name="Triceps_r")
channel_2 = Ch.Channel(mode="Single", no_channel=2, amplitude=0, pulse_width=150, name="Biceps_r")
channel_3 = Ch.Channel(mode="Single", no_channel=3, amplitude=0, pulse_width=150, name="Delt_ant_r")
channel_4 = Ch.Channel(mode="Single", no_channel=4, amplitude=0, pulse_width=150, name="Delt_post_r")
channel_5 = Ch.Channel(mode="Single", no_channel=5, amplitude=0, pulse_width=150, name="Triceps_l")
channel_6 = Ch.Channel(mode="Single", no_channel=6, amplitude=0, pulse_width=150, name="Biceps_l")
channel_7 = Ch.Channel(mode="Single", no_channel=7, amplitude=0, pulse_width=150, name="Delt_ant_l")
channel_8 = Ch.Channel(mode="Single", no_channel=8, amplitude=0, pulse_width=150, name="Delt_post_l")

# Choose which channel will be used
list_channels.append(channel_1)
# list_channels.append(channel_2)
# list_channels.append(channel_3)
# list_channels.append(channel_4)
# list_channels.append(channel_5)
# list_channels.append(channel_6)
# list_channels.append(channel_7)
# list_channels.append(channel_8)

# Create our object Stimulator
stimulator = St(port="COM4", with_motomed=False, show_log=False, fast_mode=False)
stimulator.init_channel(stimulation_interval=30, list_channels=list_channels, low_frequency_factor=0)

triceps_r_intensity = 20
biceps_r_intensity = 20
delt_ant_r_intensity = 20
delt_post_r_intensity = 20

triceps_l_intensity = 20
biceps_l_intensity = 20
delt_ant_l_intensity = 20
delt_post_l_intensity = 20
#
stim_intensity_list = [triceps_r_intensity,
                       biceps_r_intensity,
                       delt_ant_r_intensity,
                       delt_post_r_intensity,
                       triceps_l_intensity,
                       biceps_l_intensity,
                       delt_ant_l_intensity,
                       delt_post_l_intensity]


if any(x > 50 for x in stim_intensity_list):
    raise RuntimeError("Exceed intensity for upperlimb")
    
list_channels[0].set_amplitude(triceps_r_intensity)
# list_channels[1].set_amplitude(delt_post_r_intensity)
# list_channels[2].set_amplitude(delt_post_r_intensity)
# list_channels[3].set_amplitude(delt_post_r_intensity)
# list_channels[4].set_amplitude(triceps_l_intensity)
# list_channels[5].set_amplitude(biceps_l_intensity)
# list_channels[6].set_amplitude(delt_ant_l_intensity)
# list_channels[7].set_amplitude(delt_post_r_intensity)

print("stim_start")
stimulator.start_stimulation(stimulation_duration=1.5, upd_list_channels=list_channels)
print("stim_end")
time.sleep(1)
print("stim_start")
stimulator.start_stimulation(stimulation_duration=1.5, upd_list_channels=list_channels)
print("stim_end")

stimulator.stop_stimulation()
stimulator.disconnect()
