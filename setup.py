# Copyright (c) 1999-2017, Juniper Networks Inc.
# All rights reserved.
#
# Author: cklewar@juniper.net
#

from setuptools import setup, find_packages
import sys

# parse requirements
req_lines = [line.strip() for line in open(
    'requirements.txt').readlines()]
install_reqs = list(filter(None, req_lines))
if sys.version_info[:2] == (2, 6):
    install_reqs.append('importlib>=1.0.3')

setup(
    name='juniper-yapt',
    version='0.0.2',
    packages=find_packages(),
    url='https://git.juniper.net/cklewar/YAPT',
    license='The 3-Clause BSD License',
    author='cklewar',
    author_email='cklewar@juniper.net',
    maintainer = "Christian Klewar",
    description='Yet Another Provisioning Tool',
    keywords="networking automation",
    scripts = ["yapt.sh"],
    install_requires=install_reqs,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Framework :: CherryPy',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: BSD License',
        'Operating System:: POSIX:: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Networking',
    ],
)
