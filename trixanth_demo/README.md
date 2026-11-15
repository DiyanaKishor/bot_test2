# Trixanth integration dry-run kit (ROS 2 Jazzy)

This is a **software-only** bench-test package, not a working phone-app adapter or hardware controller. Keep existing robot packages untouched.

## Install

Place `trixanth_demo/` inside the **source directory of a workspace that also contains** `trixanth_comms` and `trixanth_interfaces`. In the original Trixanth workspace:

```bash
cd ~/trixanth_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-up-to trixanth_demo trixanth_comms trixanth_interfaces --symlink-install
source install/setup.bash
ros2 launch trixanth_demo bench.launch.py
```

If you cloned this package under `~/ros2_ws/src/bot_test/`, the launch will fail until the Trixanth dependencies are installed in a compatible workspace.

## UDP protocol

Bind UDP port **5005** on the Pi. Send **one JSON object per datagram** from a compatible sender.

IMU example:

```json
{"type":"imu","angular_velocity":{"x":0,"y":0,"z":0.1},"linear_acceleration":{"x":0,"y":0,"z":9.81}}
```

Only include `"orientation":{"x":0,"y":0,"z":0,"w":1}` once converted to a valid calibrated **ROS ENU** orientation.

GPS example:

```json
{"type":"gps","lat":12.9,"lon":77.6,"alt":900,"horizontal_accuracy_m":15,"valid":true}
```

The bridge does **not** understand raw SensaGram packets, auto-detect phone mounting orientation, or convert Android coordinate conventions. To use a phone app, inspect its actual UDP payload and adapt the bridge accordingly. Phone data is not wheel odometry.

## Bench tests

```bash
ros2 topic echo /imu/data --once
ros2 topic echo /gps/fix --once
```

The gate starts in IDLE. The dry-run sink prints `/cmd_vel`; it never drives hardware.

## Safety and limitations

- No GPIO, serial output, or motors are controlled by this package.
- Existing Trixanth dual-EKF configuration expects `/odom/wheel`; phone-only GPS and IMU do not replace that.
- AMCL requires a known map and laser-like observations.
- The original Trixanth archive contains no FlySky i-BUS/SBUS receiver decoder.
- Do not launch full robot bringup until missing hardware, robot description and E-stop are addressed.
