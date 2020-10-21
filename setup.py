from setuptools import setup
import os

ver = '0.0.1'
try:
    import subprocess
    ver = (ver + '-' + subprocess.check_output(['git', 'describe', '--abbrev=8',
           '--always', '--dirty', '--tags']).strip().decode())
except:  # noqa
    print(('Couldn\'t get version from git. Defaulting to %s' % ver))

# Generate a __version__.py file with this version in it
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'monitor-control', 'nodeControl', '__version__.py'), 'w') as fh:
    fh.write('__version__ = "%s"' % ver)
with open(os.path.join(here, 'backend', 'udpSender', '__version__.py'), 'w') as fh:
    fh.write('__version__ = "%s"' % ver)

setup(
    name='monitor-control',
    version='0.1',
    description='A node monitor and control interface',
    license='BSD',
    author='Zuhra Abdurashidova',
    author_email='zabdurashidova@berkeley.edu',
    url='https://github.com/reeveress/monitor-control.git',
    long_description=open('README.md').read(),
    package_dir={'nodeControl': 'monitor-control/nodeControl', 'udpSender': 'backend/udpSender'},
    packages=['nodeControl', 'udpSender'],
    # scripts = [glob.glob('monitor-control/scripts/*'),glob.glob('backend/scripts/*')],
    scripts=[
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

if ver.endswith("dirty"):
    print("********************************************")
    print("* You are installing from a dirty git repo *")
    print("*      One day you will regret this.       *")
    print("*                                          *")
    print("*  Consider cleaning up and reinstalling.  *")
    print("********************************************")
