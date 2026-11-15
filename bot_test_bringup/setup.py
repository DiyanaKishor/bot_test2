import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'bot_test_bringup'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),

    data_files=[
        
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
            
        ('share/' + package_name, ['package.xml']),

        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),

        (os.path.join('share', package_name, 'config'),
            glob(os.path.join('config', '*.yaml'))),

        (os.path.join('share', package_name, 'web'),
                    glob(os.path.join('web', '*.html'))),
    ],

    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='diyana_kishor',
    maintainer_email='diyanakishor@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': ['cmd_vel_relay_node = bot_test_bringup.cmd_vel_relay_node:main'
        ],
    },
)
