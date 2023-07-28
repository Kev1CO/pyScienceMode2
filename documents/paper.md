---
title: "`pyScienceMode`: an Open-Source Python Package for Rehastim electro-stimulator deep-control" (personalized control)

tags:
  - python
  - functional electrical stimulation
  - Rehastim
  - ScienceMode
  - control

authors:
  - name: Kevin Co
    orcid: 0009-0009-0248-3548
    affiliation: "1"
  - name: Amedeo Ceglia
    orcid: 0000-0002-7854-9410
    affiliation: "1"
  - name: Mickael Begon
    orcid: 0000-0002-4107-9160
    affiliation: "1"

affiliations:
  - name: Institute of Biomedical Engineering, Faculty of Medicine, University of Montreal, Canada
    index: 1

date: 2 December 2022 #CHANGE DATE
bibliography: paper.bib
---

# Summary

Functional electrical stimulation (FES) is a rehabilitation technique that uses electrical currents to activate muscles with the objective of producing functional movement.
It is an efficient rehabilitation therapy for patients with neurological disorders [REF] as it bypasses the neural command necessary to muscle activation.
The Rehastim devices (Hasomed Inc., Magdeburg, Germany) are a range of electro-stimulators. 
They are broadly used in the clinical and research field to peripherally stimulate muscles to restore motor functions.
Those stimulators can either be driven through their control panel or with the built-in ScienceMode functionality.
ScienceMode is an exclusive research feature allowing interaction between the stimulator and a computer using serial communication.

`pyScienceMode` is a python open source package enabling the deep control of the Rehastim device. 
This package allows the user to control the stimulator in real-time and to send parametrized pulse trains to the stimulator.
It can also be driven with the MOTOmed (Reck-Technik GmbH & Co. KG, Betzenweiler, Germany) rehabilitation bike to synchronize the stimulation patterns according to pedal angle.
Associated with other tools or sensors such as encoders, electromyography (EMG) sensors, or force sensors, `pyScienceMode` can be used to enable new stimulation strategies and controls during research development.

Currently, the development for the Rehastim 2 device is fully carried out. As for Rehastim p24 stimulator, the programming is still under process (or is still ongoing).


# Statement of Need

Emerging stimulation strategies (ibitoye2016strategies) and controls (rouse2019fes) to optimize a movement (molazadeh2021shared) or muscle force (doll2018dynamic) further pushes the devices capabilities.
Most of the time, the electro stimulation devices are software limited preventing the user to freely control the stimulator.
This limitation is ment to prevent the user from harming himself or the patient.
Therefore, not all the stimulators on the market enables the possibility of controlling the stimulator from an external hardware as it is not approved by medical norm (trouver une ref). 
For this reason, the Rehastim 2 is one of the most used electro-stimulator in research (find a ref).
Thus, a need for a user-friendly python package that allows the user to control the stimulator at his best and in real-time is asked for.
This package will enable the full and intuitive control of Rehastim devices mandatory for the testing of new rehabilitation protocols and further understand the underlying mechanisms of FES.
Another open source program for the Rehastim 2 (ravichandran2022labview) provides the same functionalities but is limited to the Labview environment.
Python being a widely used programming language in the research field, this package will be a great tool for the scientific community.

Providing stimulation parameter customization, reproducibility, and adaptability, `pyScienceMode` will enable the scientific community to pursue their challenging research.


# Features

 The main `pyScienceMode` features are:

 - `Channel(s) Initialisation`: Enables the configuration of each stimulator channel.
 - `Parameters Setting`: Enables the configuration of pulse train frequency, duration and intensity.
 - `Communicating`: real-time communication between computer and stimulator.
 - `Motomed`: real-time communication between computer and Motomed.


## A Stimulation example: Electro stimulation pipeline

`pyScienceMode` provides examples for different rehabilitation tasks such as basic stimulation commands to adaptive stimulation patterns based on MOTOmed pedal angle.

The following example shows how to control the Rehastim 2 stimulator.

```python
from time import sleep

from pyScienceMode2.rehastim_interface import Stimulator as St # Import Stimulator class
from pyScienceMode2 import Channel as Ch # Import Channel class


list_channels = [] # Create a list of channels

# Create all Rehastim 2 available channels (8-Channels) in different ways
channel_1 = Ch.Channel(
    mode="Single", no_channel=1, amplitude=50, pulse_width=100, enable_low_frequency=False, name="Biceps"
)

channel_2 = Ch.Channel()
channel_2.set_mode("Single")
channel_2.set_no_channel(2)
channel_2.set_amplitude(2)
channel_2.set_pulse_width(100)
channel_2.set_name("Triceps")

channel_3 = Ch.Channel("Doublet", 3, 50, 100)
channel_4 = Ch.Channel("Single", 4, 50, 100)
channel_5 = Ch.Channel("Triplet", 5, 50, 100)
channel_6 = Ch.Channel("Single", 6, 50, 100, True)
channel_7 = Ch.Channel("Single", 7, 50, 100)
channel_8 = Ch.Channel("Single", 8, 50, 100)

# Choose which channel will be used
list_channels.append(channel_1)
list_channels.append(channel_3)
list_channels.append(channel_5)
list_channels.append(channel_6)
list_channels.append(channel_7)
list_channels.append(channel_8)

# Create our object Stimulator
# Stimulator port can vary depending on the computer. Kindly check the port used by the Rehastim 2 in your computer device manager.
stimulator = St(
    port="/dev/ttyUSB0",
    show_log=True,
)

"""
Initialise the channels given.
It is possible to modify the list of channels, the stimulation interval and the low_frequency_factor
"""
stimulator.init_channel(stimulation_interval=200, list_channels=list_channels, low_frequency_factor=2)

"""
Start the stimulation.
It is possible to :
- Give a time after which the stimulation will be stopped but not disconnected.
- Update the parameters of the channel by giving a new list of channels. The channel given must have been 
  initialised first.
"""
stimulator.start_stimulation()
# stimulator.start_stimulation(stimulation_duration=10, upd_list_channels=new_list_channel)

# Modify some parameters,
list_channels[0].set_amplitude(10)
# list_channels[3].set_amplitude(15)

# Wait a given time in seconds or an event such as pedal angle or an electromyography signal
sleep(10)

# Update the parameters of the stimulation
stimulator.start_stimulation(upd_list_channels=list_channels)

# Wait a given time in seconds
sleep(5)

"""
Stop the stimulation. But does not disconnect the Rehastim from the computer.
"""
stimulator.stop_stimulation()

"""
Restart a stimulation with the same parameter for 2 seconds.
"""
stimulator.start_stimulation(stimulation_duration=2)

"""
The method init_channel must be called to update the stimulation interval (period).
"""
stimulator.init_channel(stimulation_interval=10, list_channels=list_channels)
stimulator.start_stimulation(stimulation_duration=2)

"""
To disconnect the computer and the Rehastim, use the disconnect method.
"""
stimulator.disconnect()

"""
After a disconnection, init_channel must be called.  
"""
stimulator.init_channel(stimulation_interval=15, list_channels=list_channels)
stimulator.start_stimulation(2, list_channels)
stimulator.disconnect()

"""
close_port method closes the serial port.
"""
stimulator.close_port()
```

The plot for 1 second stimulation at 30Hz frequency, 300us duration and 20mA intensity is shown in the following figure: 

![Stimulation signal display of a 1 second stimulation at 30Hz frequency, 300us duration and 20mA intensity.
\label{fig:emg_plot}](MAKE_THE_PLOT.png)


# How to cite

If you use `pyScienceMode` in your research, please cite the following paper: (article ref)


# Acknowledgements

A special thanks to Arsene Baert for his contribution to the package development and to Benjamin Faresin for the documentation writing.

# References