from setuptools import setup
import os
import socket
import subprocess


ver = '0.3.0'
try:
    ver = (ver + '-' + subprocess.check_output(['git', 'describe', '--abbrev=8',
           '--always', '--dirty', '--tags']).strip().decode())
except:  # noqa
    print(("Couldn't get version from git. Defaulting to %s" % ver))

# Generate a __version__.py file with this version in it
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'monitor-control', 'node_control', '__version__.py'), 'w') as fh:
    fh.write('__version__ = "%s"' % ver)

hostname = socket.gethostname()

scripts = []
if hostname in ['hera-node-head', 'hera-mobile']:
    scripts = [
                'monitor-control/scripts/hera_node_data_dump.py',
                'monitor-control/scripts/hera_node_get_status.py',
                'monitor-control/scripts/hera_node_keep_alive.py',
                'monitor-control/scripts/hera_node_receiver.py',
                'monitor-control/scripts/hera_node_serial_dump.py',
                'monitor-control/scripts/hera_node_serial.py',
                'monitor-control/scripts/hera_node_power.py',
                'monitor-control/scripts/hera_service_status.py',
                'monitor-control/scripts/hera_setup_new_node.py'
              ]
elif hostname == 'hera-snap-head':
    scripts = ['monitor-control/scripts/hera_setup_new_node.py']
else:
    scripts = ['monitor-control/scripts/hera_node_get_status.py']

setup(
    name='node_control',
    version=ver,
    description='A node monitor and control interface',
    license='BSD',
    author='David DeBoer',
    author_email='ddeboer@berkeley.edu',
    url='https://github.com/hera_team/hera_node_mc.git',
    long_description=open('README.md').read(),
    package_dir={'node_control': 'monitor-control/node_control'},
    packages=['node_control'],
    # scripts = [glob.glob('monitor-control/scripts/*'),glob.glob('backend/scripts/*')],
    scripts=scripts
)

if ver.endswith("dirty"):
    print("********************************************")
    print("* You are installing from a dirty git repo *")
    print("*      One day you will regret this.       *")
    print("*                                          *")
    print("*  Consider cleaning up and reinstalling.  *")
    print("********************************************")
