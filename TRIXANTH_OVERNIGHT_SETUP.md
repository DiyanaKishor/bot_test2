# Overnight preflight — Raspberry Pi 5, Samsung M36, ROS 2 Jazzy

**This branch is deliberately hardware-disabled.** It prepares interfaces and tests without pretending missing sensors exist. It does not include the original 14-package Trixanth source archive.

## Get it on the Pi

```bash
cd ~/ros2_ws/src/bot_test
git pull --ff-only origin main
source /opt/ros/jazzy/setup.bash
cd ~/ros2_ws
sudo apt update
rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y
colcon build --packages-select trixanth_demo --symlink-install
source install/setup.bash
ros2 launch trixanth_demo preflight.launch.py
```

The original Trixanth archive uploaded by the team should be placed **separately** in `~/trixanth_ws`; it is NOT uploaded by this Git commit. If you have the archive on the laptop (often `~/Downloads/trixanth_ws-main.zip`), send it using `scp`, not ChatGPT artifact download:

```bash
# laptop terminal
scp ~/Downloads/trixanth_ws-main.zip trixanth@192.168.0.102:~/
# pi terminal
cd ~ && unzip trixanth_ws-main.zip
mv trixanth_ws-main trixanth_ws
cd ~/trixanth_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src --rosdistro jazzy -r -y
colcon build --packages-up-to trixanth_interfaces trixanth_comms trixanth_localization --symlink-install
```

Keep the workspaces separate; don't source both install/setup.bash in one shell until interfaces and overlays are checked.

## What to run tonight

1. **Raw phone packets:** `ros2 run trixanth_demo phone_packet_inspector` listens on UDP 5006; point the Galaxy M36's streaming app to the Pi IP and that port. Raw packets help adapt the phone bridge.
2. **Phone bridge:** `ros2 run trixanth_demo phone_udp_bridge` listens on UDP 5005 for the specific JSON schema documented in `trixanth_demo/README.md`. It does not automatically support SensaGram payloads.
3. **Safe preflight:** `ros2 launch trixanth_demo preflight.launch.py` starts packet bridge, camera obstacle indicator, topic discovery and a **logging-only** motor subscriber.
4. **Experimental phone EKF:** `ros2 launch trixanth_demo phone_ekf.launch.py` only after phone message axes, mounting and orientation have been verified.

## Tomorrow's integration checklist

- Depth camera model, supported ROS 2 Jazzy driver, correct camera-to-base transform. The guard checks `/camera/depth/points` and publishes `/demo/obstacle_stop`. It starts in STOP and **does not connect to the motor gate**.
- FlySky transmitter + receiver exact models and protocol; add decoder only after checking signal levels and fail-safe behavior. There is no FlySky decoder in the original Trixanth archive.
- Cytron driver revision, motor count, motor stall current, suitable battery, Pi GPIO voltage compatibility, physical disconnect and watchdog.
- Teensy serial protocol can use the existing `trixanth_hardware` base bridge after firmware tests; avoid starting both Teensy and direct-Pi GPIO drivers simultaneously.
- EKF phone yaw/GPS is experimental; **GPS+IMU does not make valid wheel odometry or AMCL**. Depth-pointcloud obstacle avoidance can be developed separately.
- NEVER test powered motors without a physical disconnect and supervised low-speed bench checks.

## Notes

`trixanth_demo/launch/bench.launch.py` depends on original `trixanth_comms`, so it will NOT start until the separate Trixanth source is installed. Use `preflight.launch.py` first.
