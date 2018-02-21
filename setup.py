from setuptools import setup, find_packages
import glob

setup(
    name = 'monitor-control',
    version = '0.1',
    description = 'A node monitor and control interface',
    license = 'BSD',
    author = 'Zuhra Abdurashidova',
    author_email = 'zabdurashidova@berkeley.edu',
    url = 'https://github.com/reeveress/monitor-control.git',
    long_description = open('README.md').read(),
    package_dir = {'nodeControl':'monitor-control/nodeControl', 'udpSender':'backend/udpSender'},
    packages = ['nodeControl','udpSender'],
    #scripts = [glob.glob('monitor-control/scripts/*'),glob.glob('backend/scripts/*')],
    scripts = [
                'monitor-control/scripts/hera_node_data_dump.py',
                'monitor-control/scripts/hera_node_get_status.py',
                'monitor-control/scripts/hera_node_turn_off.py',
                'monitor-control/scripts/hera_node_turn_on.py',
                'backend/scripts/hera_node_cmd_check.py',
                'backend/scripts/hera_node_keep_alive.py',
                'backend/scripts/hera_node_receiver.py',
                'backend/scripts/hera_node_serial_dump.py',
                'backend/scripts/hera_node_serial.py',
                'backend/scripts/hera_node_turn_off_sender.py',
                'backend/scripts/hera_node_turn_on_sender.py',
                ]
    
)
