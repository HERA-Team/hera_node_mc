from setuptools import setup
import socket
import glob

hostname = socket.gethostname()

scripts = []
if hostname in ['hera-node-head', 'hera-mobile']\
   or hostname.startswith('DAVID') or hostname.startswith('ral'):
    scripts = glob.glob('scripts/*')
elif hostname == 'hera-snap-head':
    scripts = ['scripts/hera_setup_new_node.py', 'scripts/hera_node_get_status.py']
else:
    scripts = ['scripts/hera_node_get_status.py']

setup(
    name='node_control',
    description='A node monitor and control interface',
    license='BSD',
    author='David DeBoer',
    author_email='ddeboer@berkeley.edu',
    url='https://github.com/hera_team/hera_node_mc.git',
    long_description=open('README.md').read(),
    package_dir={'node_control': 'node_control'},
    packages=['node_control'],
    scripts=scripts,
    use_scm_version=True,
    install_requires=['redis']
)
