#!/usr/bin/env python
# -*- coding: utf8 -*-

# ============================================================================
#  Copyright (c) 2013-2019 nexB Inc. http://www.nexb.com/ - All rights reserved.
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

import codecs
import collections
import datetime
import os

from posixpath import join

import jinja2

from attributecode import ERROR
from attributecode import Error
from attributecode.attrib_util import get_template
from attributecode.licenses import COMMON_LICENSES
from attributecode.model import parse_license_expression
from attributecode.util import add_unc


def generate(abouts, template_string=None, vartext_dict=None):
    """
    Generate and return attribution text from a list of About objects and a
    template string.
    The returned rendered text may contain template processing error messages.
    """
    syntax_error = check_template(template_string)
    if syntax_error:
        return 'Template validation error at line: %r: %r' % (syntax_error)
    template = get_template(template_string)

    try:
        captured_license = []
        license_key_and_context = {}
        sorted_license_key_and_context = {}
        license_file_name_and_key = {}
        license_key_to_license_name = {}
        license_name_to_license_key = {}
        # FIXME: This need to be simplified
        for about in abouts:
            # about.license_file.value is a OrderDict with license_text_name as
            # the key and the license text as the value
            if about.license_file:
                # We want to create a dictionary which have the license short name as
                # the key and license text as the value
                for license_text_name in about.license_file.value:
                    if not license_text_name in captured_license:
                        captured_license.append(license_text_name)
                        if license_text_name.endswith('.LICENSE'):
                            license_key = license_text_name.strip('.LICENSE')
                        else:
                            license_key = license_text_name
                        license_key_and_context[license_key] = about.license_file.value[license_text_name]
                        sorted_license_key_and_context = collections.OrderedDict(sorted(license_key_and_context.items()))
                        license_file_name_and_key[license_text_name] = license_key

            # Convert/map the key in license expression to license name
            if about.license_expression.value and about.license_name.value:
                special_char_in_expression, lic_list = parse_license_expression(about.license_expression.value)
                lic_name_list = about.license_name.value
                lic_name_expression_list = []

                # The order of the license_name and key should be the same
                # The length for both list should be the same
                assert len(lic_name_list) == len(lic_list)

                # Map the license key to license name
                index_for_license_name_list = 0
                for key in lic_list:
                    license_key_to_license_name[key] = lic_name_list[index_for_license_name_list]
                    license_name_to_license_key[lic_name_list[index_for_license_name_list]] = key
                    index_for_license_name_list = index_for_license_name_list + 1

                # Create a license expression with license name instead of key
                for segment in about.license_expression.value.split():
                    if segment in license_key_to_license_name:
                        lic_name_expression_list.append(license_key_to_license_name[segment])
                    else:
                        lic_name_expression_list.append(segment)

                # Join the license name expression into a single string
                lic_name_expression = ' '.join(lic_name_expression_list)

                # Add the license name expression string into the about object
                about.license_name_expression = lic_name_expression

        # Get the current UTC time
        utcnow = datetime.datetime.utcnow()
        rendered = template.render(abouts=abouts, common_licenses=COMMON_LICENSES,
                                   license_key_and_context=sorted_license_key_and_context,
                                   license_file_name_and_key=license_file_name_and_key,
                                   license_key_to_license_name=license_key_to_license_name,
                                   license_name_to_license_key=license_name_to_license_key,
                                   utcnow=utcnow, vartext_dict=vartext_dict)
    except Exception as e:
        line = getattr(e, 'lineno', None)
        ln_msg = ' at line: %r' % line if line else ''
        err = getattr(e, 'message', '')
        return 'Template processing error%(ln_msg)s: %(err)r' % locals()
    return rendered



def check_template(template_string):
    """
    Check the syntax of a template. Return an error tuple (line number,
    message) if the template is invalid or None if it is valid.
    """
    try:
        get_template(template_string)
    except (jinja2.TemplateSyntaxError, jinja2.TemplateAssertionError) as e:
        return e.lineno, e.message


# FIXME: the template dir should be outside the code tree
default_template = join(os.path.dirname(os.path.realpath(__file__)),
                                'templates', 'default_html.template')

def generate_from_file(abouts, template_loc=None, vartext_dict=None):
    """
    Generate and return attribution string from a list of About objects and a
    template location.
    """
    if not template_loc:
        template_loc = default_template
    template_loc = add_unc(template_loc)
    with codecs.open(template_loc, 'rb', encoding='utf-8') as tplf:
        tpls = tplf.read()
    return generate(abouts, template_string=tpls, vartext_dict=vartext_dict)


def generate_and_save(abouts, output_location, use_mapping=False, mapping_file=None,
                      template_loc=None, inventory_location=None, vartext=None):
    """
    Generate attribution file using the `abouts` list of About object
    at `output_location`.

    Optionally use the mapping.config file if `use_mapping` is True.

    Optionally use the custom mapping file if mapping_file is set.

    Use the optional `template_loc` custom temaplte or a default template.

    Optionally filter `abouts` object based on the inventory JSON or
    CSV at `inventory_location`.
    """
    updated_abouts = []
    lstrip_afp = []
    afp_list = []
    not_match_path = []
    errors = []
    vartext_dict = {}

    # Parse license_expression and save to the license list
    for about in abouts:
        if about.license_expression.value:
            special_char_in_expression, lic_list = parse_license_expression(about.license_expression.value)
            if special_char_in_expression:
                msg = (u"The following character(s) cannot be in the licesne_expression: " +
                       str(special_char_in_expression))
                errors.append(Error(ERROR, msg))
            else:
                about.license_key.value = lic_list

    # Parse the vartext and save to the vartext dictionary
    if vartext:
        for var in vartext:
            key = var.partition('=')[0]
            value = var.partition('=')[2]
            vartext_dict[key] = value
    
    rendered = generate_from_file(abouts, template_loc=template_loc, vartext_dict=vartext_dict)

    if rendered:
        output_location = add_unc(output_location)
        with codecs.open(output_location, 'wb', encoding='utf-8') as of:
            of.write(rendered)

    return errors

