from setuptools import setup
from glob import glob
package_name='trixanth_demo'
setup(name=package_name,version='0.1.0',packages=[package_name],
 data_files=[('share/ament_index/resource_index/packages',['resource/'+package_name]),
 ('share/'+package_name,['package.xml']),('share/'+package_name+'/launch',glob('launch/*.launch.py'))],
 install_requires=['setuptools'],zip_safe=True,maintainer='Trixanth',maintainer_email='trixanth@example.com',
 description='Phone sensors + hardware-safe dry-run adapters',license='Apache-2.0',
 entry_points={'console_scripts':['phone_udp_bridge=trixanth_demo.phone_udp_bridge:main',
 'dry_run_motor=trixanth_demo.dry_run_motor:main']})
