#!/usr/bin/env python
# -*- coding: utf8 -*-
# ============================================================================
#  Copyright (c) 2013-2018 nexB Inc. http://www.nexb.com/ - All rights reserved.
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

"""
AboutCode toolkit is a tool to process ABOUT files. ABOUT files are
small text files that document the provenance (aka. the origin and
license) of software components as well as the essential obligation
such as attribution/credits and source code redistribution. See the
ABOUT spec at http://dejacode.org.

AboutCode toolkit reads and validates ABOUT files and collect software
components inventories.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from collections import OrderedDict
import io
import os
import re
import traceback

import click

from attributecode.util import python2

if python2:  # pragma: nocover
    from itertools import izip_longest as zip_longest  # NOQA
    from urlparse import urljoin, urlparse  # NOQA
    from urllib2 import urlopen, Request, HTTPError  # NOQA
    str = unicode  # NOQA
else:  # pragma: nocover
    from itertools import zip_longest  # NOQA
    from urllib.parse import urljoin, urlparse  # NOQA
    from urllib.request import urlopen, Request  # NOQA
    from urllib.error import HTTPError  # NOQA

import attr
from license_expression import Licensing

# from attributecode import api
from attributecode import CRITICAL
from attributecode import INFO
from attributecode import Error
from attributecode import saneyaml
from attributecode import util



@attr.attributes
class License(object):
    """
    A license object
    """
    # POSIX path relative to the ABOUT file location where the text file lives
    file = attr.attrib(default=None, repr=False)
    key = attr.attrib(default=None,)
    name = attr.attrib(default=None)
    url = attr.attrib(default=None, repr=False)
    text = attr.attrib(default=None, repr=False)

    def __attrs_post_init__(self, *args, **kwargs):
        if not self.file:
            self.file = self.default_file_name

    def to_dict(self):
        """
        Return an OrderedDict of license data (excluding texts).
        Fields with empty values are not included.
        """
        excluded = set(['text', ])

        def valid_fields(attr, value):
            return (value and attr.name not in excluded)

        return attr.asdict(self, filter=valid_fields, dict_factory=OrderedDict)

    def update(self, other_license):
        """
        Update self unset fields with data from another License.
        """
        assert isinstance(other_license, License)
        assert other_license.key == self.key
        self.name = self.name or other_license.name
        self.text = self.text or other_license.text
        self.file = self.file or other_license.file
        self.url = self.url or other_license.url

    @classmethod
    def load(cls, location):
        """
        Return a License object built from the YAML file at `location`.
        """
        with io.open(location, encoding='utf-8') as inp:
            data = saneyaml.load(inp.read(), allow_duplicate_keys=False)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data):
        """
        Return a License object built a `data` mapping.
        """
        return License(
            key=data['key'],
            name=data.get('name'),
            file=data.get('file'),
            url=data.get('url'),
        )

    @property
    def default_file_name(self):
        return self.key + '.LICENSE'

    def file_loc(self, base_dir):
        fn = self.file or self.default_file_name
        return os.path.join(base_dir, fn)

    def load_text(self, base_dir):
        """
        Load the license text found in `base_dir`.
        """
        file_loc = self.file_loc(base_dir)

        # text can be garbage and not valid UTF
        with io.open(file_loc, 'rb') as inp:
            text = inp.read()
        self.text = text.decode(encoding='utf-8', errors='replace')

    def dump(self, target_dir):
        """
        Write this license as a .yml data file and a .LICENSE text file in
        `target_dir`.
        """
        data_loc = os.path.join(target_dir, self.key + '.yml')
        with io.open(data_loc, 'w', encoding='utf-8') as out:
            out.write(saneyaml.dump(self.to_dict()))

        # always write a text file even if this is an empty one
        text = self.text or ''
        if not text:
            click.echo('WARNING: license text is empty for {}'.format(self.key))

        file_loc = self.file_loc(target_dir)
        with io.open(file_loc, 'w', encoding='utf-8') as out:
            out.write(text)


def load_license_references(reference_dir):
    """
    Return a mapping of notices as {notice_file: notice text} and a mapping of
    {license key: License} loaded from a `reference_dir`.
    In the `reference_dir`, all the files must be UTF-8 encoded text files:
     - license files must be named after their license key and can consist of:
      - a text file with .LICENSE extension
      - an optional companion .yml YAML data file with extra license data to load
        as a License obejct.

     - The notice files are any file that is not a license file pair.

    For instance, we can have the files foo.LICENSE and foo.yml where foo.yml contains:

        key: foo
        name: The Foo License
        url: http://zddfsdfsd.com/FOO
    """
    notices_by_name = {}
    licenses_by_key = {}
    ref_files = os.listdir(reference_dir)
    data_files = [f for f in ref_files if f.endswith('.yml')]
    text_files = set([f for f in ref_files if not f.endswith('.yml')])

    for data_file in data_files:
        loc = os.path.join(reference_dir, data_file)
        lic = License.load(loc)
        licenses_by_key[lic.key] = lic

        if lic.file not in text_files:
            click.echo(
                'ERROR: The license: {} does not have a '
                'corresponding text file: {}'.format(lic.key, lic.file))
        else:
            lic.load_text(reference_dir)
            text_files.remove(lic.file)

        assert lic.text is not None, 'Incorrect license with no text: {}'.format(lic.key)

    # whatever is left are "notice" files
    for notice_file in text_files:
        loc = os.path.join(reference_dir, notice_file)
        # text can be garbage and not valid UTF
        with io.open(loc, 'rb') as inp:
            text = inp.read()
        text = text.decode(encoding='utf-8', errors='replace')
        notices_by_name[notice_file] = text

    return notices_by_name, licenses_by_key


booleans = {
        'yes': True, 'y': True, 'true': True, 'x': True,
        'no': False, 'n': False, 'false': False,
}


def boolean_converter(value):
    if isinstance(value, str):
        vallo = value.lower()
        if vallo in booleans:
            return booleans[vallo]
    return value


def copyright_converter(value):
    if value:
        value = '\n'.join(v.strip() for v in value.splitlines(False))
    return value


def about_resource_converter(value):
    if value:
        value = util.to_posix(value).strip('/')
    return value


def license_expression_converter(value):
    if value:
        licensing = Licensing()
        expression = licensing.parse(value, simple=True)
        value = str(expression)
    return value


@attr.attributes
class About(object):
    """
    A package object
    """
    # the absolute location where this is stored
    location = attr.attrib(default=None, repr=False)

    # this is a path relative to the ABOUT file location
    about_resource = attr.attrib(
        default=None, converter=about_resource_converter)

    # everything else is optional

    name = attr.attrib(default=None)
    version = attr.attrib(default=None)
    description = attr.attrib(default=None, repr=False)
    homepage_url = attr.attrib(default=None, repr=False)
    download_url = attr.attrib(default=None, repr=False)
    notes = attr.attrib(default=None, repr=False)

    copyright = attr.attrib(
        default=None, repr=False, converter=copyright_converter)
    license_expression = attr.attrib(
        default=None, repr=False, converter=license_expression_converter)

    # boolean flags as yes/no
    attribute = attr.attrib(
        default=False, type=bool, converter=boolean_converter, repr=False)
    redistribute = attr.attrib(
        default=False, type=bool, converter=boolean_converter, repr=False)
    modified = attr.attrib(
        default=False, type=bool, converter=boolean_converter, repr=False)
    track_changes = attr.attrib(
        default=False, type=bool, converter=boolean_converter, repr=False)
    internal_use_only = attr.attrib(
        default=False, type=bool, converter=boolean_converter, repr=False)

    # a list of License objects
    licenses = attr.attrib(default=attr.Factory(list), repr=False)

    # path relative to the ABOUT file location
    notice_file = attr.attrib(default=None, repr=False)
    # the text loaded from notice_file
    notice_text = attr.attrib(default=None, repr=False)
    notice_url = attr.attrib(default=None, repr=False)

    # path relative to the ABOUT file location
    changelog_file = attr.attrib(default=None, repr=False)

    owner = attr.attrib(default=None, repr=False)
    owner_url = attr.attrib(default=None, repr=False)

    vcs_tool = attr.attrib(default=None, repr=False)
    vcs_repository = attr.attrib(default=None, repr=False)
    vcs_revision = attr.attrib(default=None, repr=False)

    checksum_md5 = attr.attrib(default=None, repr=False)
    checksum_sha1 = attr.attrib(default=None, repr=False)
    checksum_sha256 = attr.attrib(default=None, repr=False)
    spec_version = attr.attrib(default=None, repr=False)

    # custom files as name: value
    custom_fields = attr.attrib(default=attr.Factory(dict), repr=False)
    # list of Error object
    errors = attr.attrib(default=attr.Factory(list), repr=False)

    excluded_fields = set([
        'errors',
        'custom_fields',
        'notice_text',
        # this is the License text
        'text',
    ])

    def __attrs_post_init__(self, *args, **kwargs):
        # populate licenses from expression
        if self.license_expression and not self.licenses:
            keys = Licensing().license_keys(
                self.license_expression, unique=True, simple=True)
            licenses = [License(key=key) for key in keys]
            self.licenses = licenses

    def to_dict(self, with_licenses=True, with_location=False):
        """
        Return an OrderedDict of About data (excluding texts and file locations).
        Fields with empty values are not included.
        """
        excluded_fields = set(self.excluded_fields)

        if not with_licenses:
            excluded_fields.add('licenses')

        if not with_location:
            excluded_fields.add('location')

        def valid_fields(attr, value):
            return (value and attr.name not in excluded_fields)

        data = attr.asdict(self,
            recurse=True, filter=valid_fields, dict_factory=OrderedDict)

        # add custom fields
        for key, value in sorted(self.custom_fields.items()):
            if value:
                data[key] = value

        return data

    @classmethod
    def standard_fields(cls):
        """
        Return a list of standard field names available in this class.
        """
        return [f for f in attr.fields_dict(cls).keys()
                if f not in cls.excluded_fields]

    def fields(self):
        """
        Return a list of standard field names and a list of custom field names
        in use (with a value set) in this object.
        """

        def valid_fields(attribute, value):
            return (value and attribute.name not in self.excluded_fields)

        standard = attr.asdict(
            self, recurse=False, filter=valid_fields, dict_factory=OrderedDict)
        standard = list(standard.keys())

        custom = [key for key, value in self.custom_fields.items() if value]

        return standard, custom

    def dumps(self):
        """
        Return a YAML representation for this About.
        If `with_files` is True, also write any reference notice or license file.
        """
        return saneyaml.dump(self.to_dict(), indent=2)

    def dump(self, location, with_files=False):
        """
        Write this About object to the YAML file at `location`.
        If `with_files` is True, also write any reference notice or license file.
        """
        parent = os.path.dirname(location)
        if not os.path.exists(parent):
            os.makedirs(parent)

        with io.open(location, 'w', encoding='utf-8') as out:
            out.write(self.dumps())

        if with_files:
            base_dir = os.path.dirname(location)
            self.write_files(base_dir)

    def write_files(self, base_dir=None):
        """
        Write all referenced license and notice files.
        """
        base_dir = base_dir or os.path.dirname(self.location)

        def _write(text, target_loc):
            if target_loc:
                text = text or ''
                parent = os.path.dirname(target_loc)
                if not os.path.exists(parent):
                    os.makedirs(parent)

                with io.open(target_loc, 'w', encoding='utf-8') as out:
                    out.write(text)

        _write(self.notice_text, self.notice_file_loc(base_dir))

        for license in self.licenses:  # NOQA
            _write(license.text, license.file_loc(base_dir))

    @classmethod
    def load(cls, location):
        """
        Return an About object built from the YAML file at `location` or None.
        """
        # TODO: expand/resolve/abs/etc
        loc = util.to_posix(location)
        about = None
        try:
            with io.open(loc, encoding='utf-8') as inp:
                text = inp.read()
            about = cls.loads(text)
        except Exception as e:
            trace = traceback.format_exc()
            msg = 'Cannot load invalid ABOUT file from: %(location)r: %(e)r\n%(trace)s'
            about = About()
            about.errors.append(Error(CRITICAL, msg % locals()))

        if about:
            about.location = location
            return about

    @classmethod
    def loads(cls, text):
        """
        Return an About object built from a YAML `text` or None.
        """
        about = None
        try:
            data = saneyaml.load(text, allow_duplicate_keys=False)
            about = cls.from_dict(data)
        except Exception as e:
            trace = traceback.format_exc()
            msg = 'Cannot load invalid ABOUT file from: %(text)r: %(e)r\n%(trace)s'
            about = About()
            about.errors.append(Error(CRITICAL, msg % locals()))
        return about

    @classmethod
    def from_dict(cls, data):
        """
        Return an About object built a `data` mapping.
        """
        data = dict(data)

        standard_field_names = set(attr.fields_dict(cls).keys())

        keys = set(data.keys())
        keys_lower = set([k.lower() for k in keys])
        if len(keys) != len(keys_lower):
            raise Exception('Invalid data: lowercased keys must be unique.')

        if keys != keys_lower:
            raise Exception('Invalid data: all keys must be lowercase.')

        licenses = data.pop('licenses', []) or []
        licenses = [License.from_dict(l) for l in licenses]

        standard_fields = {}
        custom_fields = {}

        # strip strings nd skip empties
        for key, value in data.items():
            if isinstance(value, str):
                value = value.strip()

            if not value:
                continue

            if key in standard_field_names:
                standard_fields[key] = value
            else:
                custom_fields[key] = value

        about = About(licenses=licenses, custom_fields=custom_fields, **standard_fields)

        about.validate()
        return about

    def field_names(self):
        """
        Return a list of all field names in use in this object.
        """
        standard = list(attr.fields_dict(self.__class__).keys())
        custom = [k for k, v in self.custom_fields.items() if v]
        return standard + custom

    def validate(self):
        """
        Check self for errors. Reset, update and return self.errors.
        """
        is_valid_name = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$').match

        if not self.about_resource:
            msg = 'Field about_resource is required and empty or missing.'
            self.errors.append(Error(CRITICAL, msg))

        for name in self.custom_fields.keys():
            # Check if names aresafe to use as an attribute name.
            if not is_valid_name(name):
                msg = (
                    'Field name: %(name)r contains illegal characters. '
                    'Only these characters are allowed: '
                    'ASCII letters, digits and "_" underscore. '
                    'The first characters must be a letter')
                self.errors.append(Error(CRITICAL, msg % locals()))

            msg = 'Field %(name)s is a custom field.'
            self.errors.append(Error(INFO, msg % locals()))

        boolean_fields = (
                'redistribute',
                'attribute',
                'track_changes',
                'modified',
                'internal_use_only',
        )

        for name in boolean_fields:
            value = getattr(self, name, False)
            if value and value is not True:
                msg = (
                    'Field name: %(name)r has an invalid flag value: '
                    '%(value)r: should be one of yes or no or true or false.')
                self.errors.append(Error(CRITICAL, msg % locals()))

        # TODO: add check on license_expression!!! And it might be a required??

        return self.errors

    def about_resource_loc(self, base_dir=None):
        """
        Return the location to the about_resource.
        """
        base_dir = base_dir or os.path.dirname(self.location)
        return self.about_resource and os.path.join(base_dir, self.about_resource)

    def notice_file_loc(self, base_dir=None):
        """
        Return the location to the notice_file or None.
        """
        base_dir = base_dir or os.path.dirname(self.location)
        return self.notice_file and os.path.join(base_dir, self.notice_file)

    def changelog_file_loc(self, base_dir=None):
        """
        Return the location to the changelog_file or None.
        """
        base_dir = base_dir or os.path.dirname(self.location)
        return self.changelog_file and os.path.join(base_dir, self.changelog_file)

    def check_files(self, base_dir=None):
        """
        Check that referenced files exist. Update and return self.errors.
        """
        if self.location and not os.path.exists(self.location):
            msg = u'ABOUT file location: {} does not exists.'.format(self.location)
            self.errors.append(Error(CRITICAL, msg))

        base_dir = base_dir or os.path.dirname(self.location)

        if not os.path.exists(base_dir):
            msg = u'base_dir: {} does not exists: unable to check files existence.'.format(base_dir)
            self.errors.append(Error(CRITICAL, msg))
            return

        about_resource_loc = self.about_resource_loc(base_dir)
        if about_resource_loc and not os.path.exists(about_resource_loc):
            msg = u'File about_resource: "{}" does not exists'.format(self.about_resource)
            self.errors.append(Error(CRITICAL, msg))

        notice_file_loc = self.notice_file_loc(base_dir)
        if notice_file_loc and not os.path.exists(notice_file_loc):
            msg = u'File notice_file: "{}" does not exists'.format(self.notice_file)
            self.errors.append(Error(CRITICAL, msg))

        changelog_file_loc = self.changelog_file_loc(base_dir)
        if changelog_file_loc and not os.path.exists(changelog_file_loc):
            msg = u'File changelog_file: "{}" does not exists'.format(self.changelog_file)
            self.errors.append(Error(CRITICAL, msg))

        for license in self.licenses:  # NOQA
            license_file_loc = license.file_loc(base_dir)
            if not os.path.exists(license_file_loc):
                msg = u'License file: "{}" does not exists'.format(license.file)
                self.errors.append(Error(CRITICAL, msg))

        return self.errors

    def load_files(self, base_dir=None):
        """
        Load all referenced license and notice texts. Return a list of errors.
        """
        base_dir = base_dir or os.path.dirname(self.location)
        errors = []

        def _load_text(loc):
            if loc:
                text = None
                try:
                    # text can be garbage and not valid UTF
                    with io.open(loc, 'rb') as inp:
                        text = inp.read()
                    text = text.decode(encoding='utf-8', errors='replace')

                except Exception as e:
                    msg = 'Unable to read text file: {}\n'.format(loc) + str(e)
                    errors.append(Error(CRITICAL, msg))
                return text

        text = _load_text(self.notice_file_loc(base_dir))
        if text:
            self.notice_text = text

        for license in self.licenses:  # NOQA
            text = _load_text(license.file_loc(base_dir))
            if text:
                license.text = text

        return errors
