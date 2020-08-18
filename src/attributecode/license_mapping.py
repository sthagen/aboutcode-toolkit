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


def mapping(location, output, convert_to):
    errors, abouts = load_inventory(
        location=location,
        base_dir=output
    )
