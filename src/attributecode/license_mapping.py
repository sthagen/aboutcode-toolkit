#!/usr/bin/env python
# -*- coding: utf8 -*-
# ============================================================================
#  Copyright (c) 2013-2020 nexB Inc. http://www.nexb.com/ - All rights reserved.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#      http://www.apache.org/licenses/LICENSE-2.0
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# ============================================================================

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from collections import Counter
from collections import OrderedDict
import io
import os
import json

import attr

from attributecode import CRITICAL
from attributecode import Error
from attributecode import saneyaml
from attributecode.gen import load_inventory
from attributecode.util import csv
from attributecode.util import load_csv
from attributecode.util import load_json
from attributecode.util import python2
from attributecode.util import replace_tab_with_spaces


def mapping(abouts, convert_to):
    errors = []
    map_file_location = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'spdx_mapping.json')
    with open(map_file_location, 'r') as f:
        map_file = json.loads(f.read())

    # The map_file is a dictionary list with spdx license as the key and djc as the value.
    # If 'convert_to == spdx', we need to create a new mapping file which the djc as the key and spdx as the value.
    if convert_to == 'djc':
        mapping_file = map_file.copy()
    else:
        mapping_file = {}
        for k, v in map_file.items():
            mapping_file[v] = k

    errors, abouts = process_mapping(abouts, mapping_file)
    

    return errors, abouts


def process_mapping(abouts, mapping_file):
    for about in abouts:
        print(about)

