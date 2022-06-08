from setuptools import setup
import socket
import glob

hostname = socket.gethostname().lower()

if hostname == 'hera-snap-head':
    scripts = ['scripts/hera_setup_new_node.py', 'scripts/hera_node_get_status.py',
               'scripts/hera_upload_meta_to_redis.py']
elif hostname == 'hera-corr-head':
    scripts = ['scripts/hera_node_get_status.py', 'scripts/hera_upload_meta_to_redis.py']
else:
    scripts = glob.glob('scripts/*')

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
