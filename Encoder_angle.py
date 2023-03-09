import time
import nidaqmx


device_mane = None
local_system = nidaqmx.system.System.local()
driver_version = local_system.driver_version
print('DAQmx {0}.{1}.{2}'.format(driver_version.major_version, driver_version.minor_version,
                                 driver_version.update_version))
for device in local_system.devices:
    print('Device Name: {0}, Product Category: {1}, Product Type: {2}'.format(
        device.name, device.product_category, device.product_type))
    device_mane = device.name

    task2 = nidaqmx.Task()
    task2.ai_channels.add_ai_voltage_chan(device_mane + '/ai14')
    # task2.timing.cfg_samp_clk_timing(rate=10000, sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=10)
    task2.start()

min_voltage = 1.33
max_voltage = 5
origin = task2.read() - min_voltage
angle_coeff = 360 / (max_voltage - min_voltage)
direction = "concentric"


def get_angle():
    voltage = task2.read() - min_voltage
    actual_voltage = voltage - origin
    angle = 360 - (actual_voltage * angle_coeff) if 0 < actual_voltage < 5 - origin else abs(actual_voltage) * angle_coeff
    return voltage, angle, task2

volt, ang, task = get_angle()
volt_list = []
ang_list = []
i = 0
while i < 200:
    ang_list.append(round(get_angle()[1], 5)/100)
    volt_list.append(round(get_angle()[0], 5))
    time.sleep(0.005)
    i += 1

import matplotlib.pyplot as plt

plt.plot(volt_list)
plt.plot(ang_list)
plt.show()





