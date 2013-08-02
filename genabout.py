#!/usr/bin/env python
# -*- coding: utf8 -*-

# =============================================================================
#  Copyright (c) 2013 by nexB, Inc. http://www.nexb.com/ - All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#      http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# =============================================================================

"""
This is a tool to generate ABOUT files based on the input file.
The input file should be a csv format which contains information about the
file location, origin and license of the software components etc.
"""

from __future__ import print_function
from os import makedirs
from os.path import exists, dirname, join, abspath, isdir
import csv
import errno
import getopt
import os
import string
import sys

import about

# TODO: version number
__version__ = '0.8.1'


MANDATORY_FIELDS = ['about_resource', 'name', 'version']
SKIPPED_FIELDS = ['warnings', 'errors']

def _exists(file_path):
    """
    Return True if path exists.
    """
    if file_path:
        return exists(abspath(file_path))

def read_input(input_file, gen_location, action_num):
    """
    Read the input csv file, get the information and write the information 
    into the .ABOUT file.
    """
    csvfile = csv.DictReader(open(input_file, 'rb'))
    for line in csvfile:
        try:
            file_location = line['about_resource']
        except Exception, e:
            print(repr(e))
            print("The input file does not contain the key 'about_resource' which is required.")
            sys.exit(errno.EINVAL)
        if file_location.startswith('/'):
            file_location = file_location.partition('/')[2]
        location = join(gen_location, file_location)
        about_file_location =''
        if location.lower().endswith('.about'):
            about_file_location = location
        else:
            if location[-1] == '/':
                about_file_location = location.rpartition('/')[0] + '.ABOUT'
            else:
                about_file_location = location + '.ABOUT'
        dir = dirname(about_file_location)
        if not _exists(dir):
            makedirs(dir)
        # TODO: Create log to indicate which one have been ignored/changed.
        if _exists(about_file_location):
            if action_num == '0':
                print("ABOUT file already existed: %s" % about_file_location)
            # Overwrites the current ABOUT field value if existed
            elif action_num == '1':
                about_object = about.AboutFile(about_file_location)
                for field_name, value in about_object.parsed.items():
                    field_name = field_name.lower()
                    if not field_name in line.keys():
                        line[field_name] = value
                os.remove(about_file_location)
                gen_output(about_file_location, line)
            # Keep the current field value and only add the "new" field and field value
            elif action_num == '2':
                about_object = about.AboutFile(about_file_location)
                for field_name, value in about_object.parsed.items():
                    field_name = field_name.lower()
                    line[field_name] = value
                os.remove(about_file_location)
                gen_output(about_file_location, line)
            elif action_num == '3':
                os.remove(about_file_location)
                gen_output(about_file_location, line)
                print("This ABOUT file has been regenerated: %s" % about_file_location)
        else:
            gen_output(about_file_location, line)


def gen_output(about_file_location, line):
    with open(about_file_location, 'wb') as output_file:
        context = ''
        try:
            if line['name']:
                name = line['name']
        except:
            name = ''
        try:
            if line['version']:
                version = line['version']
        except:
            version = ''
        context = 'about_resource: ' + line['about_resource'] + '\n' \
                    + 'name: ' + name + '\n' \
                    + 'version: ' + version + '\n\n'
        for item in sorted(line.iterkeys()):
            if not item in MANDATORY_FIELDS:
                # The purpose of the replace('\n', '\n ') is used to
                # format the continuation strings
                value = line[item].replace('\n', '\n ')
                if (value or item in MANDATORY_FIELDS) and not item in SKIPPED_FIELDS:
                    context += item + ': ' + value + '\n'
        output_file.write(context)


def syntax():
    print("""
Syntax:
    genabout.py [Options] [Input File] [Generated Location]
    Input File         - The input CSV file
    Generated Location - the output location where the ABOUT files should be generated
""")

def version():
    print("""
ABOUT CODE: Version: %s
Copyright (c) 2013 nexB Inc. All rights reserved.
http://dejacode.org
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations
under the License.""" % __version__)


def option_usage():
    print("""
Options:
    -v,--version         Display current version, license notice, and copyright notice
    -h,--help            Display help
    --action  <arg>      Handle different behaviors if ABOUT files already existed
        <arg>
            0 - Do nothing if ABOUT file existed (default)
            1 - Overwrites the current ABOUT field value if existed
            2 - Keep the current field value and only add the "new" field and field value
            3 - Replace the ABOUT file with the current generation
""")

def main(args, opts):
    opt_arg_num = '0'
    for opt, opt_arg in opts:
        invalid_opt = True
        if opt in ('-h', '--help'):
            syntax()
            option_usage()
            sys.exit(0)

        if opt in ('-v', '--version'):
            version()
            sys.exit(0)

        if opt in ('--action'):
            invalid_opt = False
            valid_opt_args = ['0', '1', '2', '3']
            if not opt_arg or not opt_arg in valid_opt_args:
                print("Invalid option argument.")
                option_usage()
                sys.exit(errno.EINVAL)
            else:
                opt_arg_num = opt_arg

        if invalid_opt:
            assert False, 'Unsupported option.'

    if not len(args) == 2:
        print('Input file and generated location parameters are mandatory.')
        syntax()
        option_usage()
        sys.exit(errno.EINVAL)

    input_file = args[0]
    gen_location = args[1]

    if isdir(input_file):
        print(input_file, ": Input is not a CSV file.")
        sys.exit(errno.EIO)
    if not _exists(input_file):
        print(input_file, ': Input file does not exist.')
        sys.exit(errno.EIO)
    if not _exists(gen_location):
        print(gen_location, ': Generated location does not exist.')
        sys.exit(errno.EIO)

    read_input(input_file, gen_location, opt_arg_num)


if __name__ == "__main__":
    longopts = ['help', 'version', 'action=']
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hv', longopts)
    except Exception, e:
        print(repr(e))
        syntax()
        option_usage()
        sys.exit(errno.EINVAL)

    main(args, opts)
