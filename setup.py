# Copyright 2018 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from io import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

# Package metadata.
name = "slo-generator"
description = "SLO Generator"
version = "1.5.0"
# Should be one of:
# 'Development Status :: 3 - Alpha'
# 'Development Status :: 4 - Beta'
# 'Development Status :: 5 - Production/Stable'
release_status = "Development Status :: 3 - Alpha"
dependencies = [
    'google-api-python-client < 2.0.0', 'oauth2client',
    'google-cloud-monitoring < 2.0.0', 'google-cloud-pubsub==1.7.0',
    'google-cloud-bigquery < 3.0.0', 'prometheus-http-client',
    'prometheus-client', 'pyyaml', 'opencensus', 'elasticsearch',
    'python-dateutil', 'datadog', 'retrying==1.3.3'
]
extras = {}

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name=name,
      version=version,
      description=description,
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='Google Inc.',
      author_email='ocervello@google.com',
      license='Apache 2.0',
      packages=find_packages(exclude=['contrib', 'docs', 'tests']),
      classifiers=[
          release_status,
          'Intended Audience :: Developers',
          'Topic :: Software Development :: Build Tools',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
      ],
      keywords='slo sli generator gcp',
      install_requires=dependencies,
      entry_points={
          'console_scripts': ['slo-generator=slo_generator.cli:main'],
      },
      python_requires='>=3.4')
