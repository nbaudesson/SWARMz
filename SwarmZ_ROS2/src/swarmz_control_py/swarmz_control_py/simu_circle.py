# Import the subprocess and time modules
import rclpy
from rclpy.node import Node
import subprocess
import time
import sys
import argparse
import atexit
import os
import signal

class SimuNode(Node):

    def __init__(self) -> None:
        super().__init__("simu_node")

        self.declare_parameter("headless", 1)
        self.headless = self.get_parameter("headless").get_parameter_value().integer_value

        self.declare_parameter("dds", '../Micro-XRCE-DDS-Agent')
        self.dds = self.get_parameter("dds").get_parameter_value().string_value

        self.declare_parameter("px4", '../PX4-Autopilot')
        self.px4 = self.get_parameter("px4").get_parameter_value().string_value
        
        self.declare_parameter("lat", 43.13471)
        self.latitude = self.get_parameter("lat").get_parameter_value().double_value

        self.declare_parameter("lon", 6.01507)
        self.longitude = self.get_parameter("lon").get_parameter_value().double_value

        self.declare_parameter("alt", 6)
        self.altitude = self.get_parameter("alt").get_parameter_value().double_value

        if self.headless == 0:
            self.gui=""
        else:
            self.gui="HEADLESS=1"

# Function to terminate the external program
def terminate_external_program():
    global external_processes
    print(len(external_processes))
    # for external_process in external_processes:
    #     if external_process and external_process.poll() is None:
    #         external_process.kill()
    for external_process in external_processes:
        os.killpg(os.getpgid(external_process.pid), signal.SIGTERM) 

def kill_px4():
    # Kill px4 processes in the background
    try:
        subprocess.Popen("pkill -f 'px4'", shell=True)
    except subprocess.CalledProcessError as e:
        # Handle the error, or ignore it if it's due to no matching processes
        if e.returncode != 1:  # Check if the return code is not 1 (no processes matched)
            print(f"Error executing command: {e}")
        else:
            print("No processes matched the pattern.")

def kill_dds():
    # Kill px4 processes in the background
    try:
        subprocess.Popen("pkill -f 'MicroXRCEAgent'", shell=True)
    except subprocess.CalledProcessError as e:
        # Handle the error, or ignore it if it's due to no matching processes
        if e.returncode != 1:  # Check if the return code is not 1 (no processes matched)
            print(f"Error executing command: {e}")
        else:
            print("No processes matched the pattern.")

def kill_gazebo():
    # Kill old gazebo sim possibly running in the background
    try:
        subprocess.Popen("pkill -f 'gz sim'", shell=True)
    except subprocess.CalledProcessError as e:
        # Handle the error, or ignore it if it's due to no matching processes
        if e.returncode != 1:  # Check if the return code is not 1 (no processes matched)
            print(f"Error executing command: {e}")
        else:
            print("No processes matched the pattern.")

external_processes = []

def main():
    rclpy.init()
    node = SimuNode()

    # List of commands to run
    commands = (
        # Run the Micro XRCE-DDS Agent
        "cd "+node.dds+" && MicroXRCEAgent udp4 -p 8888",
    
        # Spawn drones in PX4 SITL simulation
        "cd "+node.px4+" && export PX4_HOME_LAT="+str(node.latitude)+" && export PX4_HOME_LON="+str(node.longitude)+" && export PX4_HOME_ALT="+str(node.altitude)+" && PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE='5,0' PX4_GZ_MODEL=x500 "+node.gui+" ./build/px4_sitl_default/bin/px4 -i 1",
        "cd "+node.px4+" && export PX4_HOME_LAT="+str(node.latitude)+" && export PX4_HOME_LON="+str(node.longitude)+" && export PX4_HOME_ALT="+str(node.altitude)+" && PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE='1.6,4.7' PX4_GZ_MODEL=x500 "+node.gui+" ./build/px4_sitl_default/bin/px4 -i 2",
        "cd "+node.px4+" && export PX4_HOME_LAT="+str(node.latitude)+" && export PX4_HOME_LON="+str(node.longitude)+" && export PX4_HOME_ALT="+str(node.altitude)+" && PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE='-4,3' PX4_GZ_MODEL=x500 "+node.gui+" ./build/px4_sitl_default/bin/px4 -i 3",
        "cd "+node.px4+" && export PX4_HOME_LAT="+str(node.latitude)+" && export PX4_HOME_LON="+str(node.longitude)+" && export PX4_HOME_ALT="+str(node.altitude)+" && PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE='-4,-3' PX4_GZ_MODEL=x500 "+node.gui+" ./build/px4_sitl_default/bin/px4 -i 4",
        "cd "+node.px4+" && export PX4_HOME_LAT="+str(node.latitude)+" && export PX4_HOME_LON="+str(node.longitude)+" && export PX4_HOME_ALT="+str(node.altitude)+" && PX4_SYS_AUTOSTART=4001 PX4_GZ_MODEL_POSE='1.6,-4.7' PX4_GZ_MODEL=x500 "+node.gui+" ./build/px4_sitl_default/bin/px4 -i 5",

        # Run QGroundControl
        # "cd ~/QGroundControl && ./QGroundControl.AppImage
    )

    kill_gazebo()
    time.sleep(2)

    # Loop through each command in the list
    for command in commands:
        if node.headless == 0:
            # Each command is run in a new tab of the gnome-terminal
            external_processes.append(subprocess.Popen(["gnome-terminal", "--tab", "--", "bash", "-c", command + "; exec bash"],shell=True))
            # pause between each command
            time.sleep(2.5)
        else:
            # In a diplayless machine, run the programs as regular subprocesses
            external_processes.append(subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid))
            # Pause between each command
            time.sleep(0.5)

    try:
        # Your ROS 2 node logic here
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Cleaning up...")
        kill_dds()
        kill_px4()
        kill_gazebo()
    finally:
        # Ensure proper shutdown of the ROS 2 node
        node.destroy_node()
        atexit.register(kill_gazebo)
        atexit.register(kill_px4)
        atexit.register(kill_dds)

if __name__ == '__main__':
    main()