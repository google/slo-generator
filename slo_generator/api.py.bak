# Copyright 2021 Google Inc.
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
"""
`api.py`
Simple Flask API for `slo-generator`.
"""
import argparse
import sys
from os.path import abspath
from flask import jsonify, Flask, request
from .compute import compute
from .utils import parse_config

app = Flask(__name__)
app.config['DEBUG'] = True

CONFIG_PATH = 'config.yaml'


@app.route('/', methods=['POST'])
def run():
    """Run slo-generator on requested data."""
    data = request.data.decode('utf-8')
    slo_config = parse_config(content=data)
    config = parse_config(path=app.config['CONFIG_PATH'])
    reports = compute(slo_config, config)
    return jsonify(reports)


def main():
    """Run Flask application."""
    args = vars(parse_args(sys.argv[1:]))
    app.config['CONFIG_PATH'] = abspath(args.pop('config'))
    app.run(**args)


def parse_args(args):
    """Parse CLI arguments.

    Args:
        args (list): List of args passed from CLI.

    Returns:
        obj: Args parsed by ArgumentParser.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',
                        '-c',
                        type=str,
                        required=False,
                        default='config.yaml',
                        help='Error budget policy file (JSON / YAML)')
    parser.add_argument('--host',
                        type=str,
                        required=False,
                        default='0.0.0.0',
                        help='API host (default: 0.0.0.0)')
    parser.add_argument('--port',
                        type=str,
                        required=False,
                        default='5000',
                        help='API port (default: 5000)')
    return parser.parse_args(args)


if __name__ == '__main__':
    main()
