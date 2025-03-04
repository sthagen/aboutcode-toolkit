.. _specification:

===============================
ABOUT File Specification v4.0.1
===============================

Purpose
=======

An ABOUT file provides a simple way to document the provenance (origin and license)
and other important or interesting information about a software component.
An ABOUT file is a small YAML formatted text file stored in the codebase side-by-side
with the software component file or archive that it documents. No modification
of the documented software is needed.

The ABOUT format is plain text with field name/value pairs separated by a colon.
It is easy to read and create by hand and is designed first for humans, rather than
machines. The format is well-defined and structured just enough to make it easy to process with
software as well. It contains enough information to fulfill key license requirements
such as creating credits or attribution notices, collecting redistributable source code,
or providing information about new versions of a software component.

Getting Started
===============

A simple and valid ABOUT file named httpd-2.4.3.tar.gz.ABOUT may look like this:

        ..  code-block:: none

                about_resource: httpd-2.4.3.tar.gz
                name: Apache HTTP Server
                version: 2.4.3
                homepage_url: http://httpd.apache.org
                download_url: http://archive.apache.org/dist/httpd/httpd-2.4.3.tar.gz
                license_expression: apache-2.0
                licenses:
                    -   key: apache-2.0
                        name: Apache 2.0
                        file: apache-2.0.LICENSE
                        url: https://scancode-licensedb.aboutcode.org/apache-2.0.LICENSE
                        spdx_license_key: Apache-2.0
                notice_file: httpd.NOTICE
                copyright: Copyright (c) 2012 The Apache Software Foundation.

The meaning of this ABOUT file is:

-   The file "httpd-2.4.3.tar.gz" is stored in the same directory and side-by-side with
    the ABOUT file "httpd-2.4.3.tar.gz.ABOUT" that documents it.
-   The name of this component is "Apache HTTP Server" with version "2.4.3".
-   The homepage URL for this component is http://httpd.apache.org
-   The file "httpd-2.4.3.tar.gz" was originally downloaded from http://archive.apache.org/dist/httpd/httpd-2.4.3.tar.gz
-   This component is licensed under "apache-2.0"
-   The licenses section contains the information of this "apache-2.0" license.
-   In the same directory, "apache-2.0.LICENSE" and "httpd.NOTICE" are files
    that contain respectively the license text and the notice text for this component.

Specification
=============

An ABOUT file is an YAML formatted text file.
The key for the licenses field and the license_expression are ScanCode license key.

ABOUT file name
---------------

An ABOUT file name can use a limited set of characters and is suffixed with a
".ABOUT" extension using any combination of uppercase and lowercase characters.

A file name can contain any characters and digits with the following exception and condition:

-   the following symbols are not accepted: ``", #, &, ', *, \, :, ;, <, >, =, ?, /, ^, `, |``
-   The case of a file name is not significant. On case-sensitive file systems
    (such as on Linux), a tool must report an error if two ABOUT files stored in the same
    directory have the same lowercase file name. This is to ensure that ABOUT files can be
    used across file systems. The convention is to use a lowercase file name and an uppercase
    ABOUT extension.

Lines of text
-------------

An ABOUT file contains lines of text. Lines contain field names/values pairs.
The standard line ending is the LF character. The line ending characters can be any LF,
CR or CR/LF and tools must normalize line endings to LF when processing an ABOUT file.
Empty lines and lines containing only white spaces that are not part of a field value
continuation are ignored. Empty lines are commonly used to improve the readability
of an ABOUT file.

Field name
----------

A field name can contain only these US-ASCII characters:

-   digits from 0 to 9
-   uppercase and lowercase letters from A to Z
-   the ``"_"`` underscore sign.
-   Field names are not case sensitive. For example, "HOMEPAGE_URL" and "HomePage_url"
    represent the same field name.
-   A field name must start at the beginning of a new line. No spaces is allowed in
    the field name. It can be followed by one or more spaces that must be ignored.
    These spaces are commonly used to improve the readability of an ABOUT file.

Field value
-----------

The field value is separated from the field name by a ":" colon. The ":" colon
can be followed by one or more spaces that must be ignored. This also applies
to trailing white spaces: they must be ignored.

The field value is composed of one or more lines of plain printable text.

When a field value is a long string, additional continuation lines must start with
at least one space. In this case, the first space of an additional continuation
line is ignored and should be removed from the field value by tools.

For instance:

        ..  code-block:: none

                description: This is a long description for a
                 software component that additional continuation line is used.

When a field value contains more than one line of text, a "literal block" (using ``|``) is need.

For instance:

        ..  code-block:: none

                description: |
                    This is a long description for a software component that spans
                    multiple lines with arbitrary line breaks.

                    This text contains multiple lines.

Fields are mandatory, optional or custom extension
--------------------------------------------------

A field can be mandatory, optional or custom extension. Tools must
report an error for missing mandatory fields.

Fields validation
-----------------

When processing an ABOUT file, tools must report a warning or error if a field
is invalid. A field can be invalid for several reasons, such as invalid field
name syntax or invalid content. Tools should report additional validation error
details. The validation process should check that each field name is syntactically
correct and that fields contain correct values according to its concise, common
sense definition in this specification. For certain fields, additional and specific
validations are relevant such as URL validation, path resolution and verification,
and so forth. Tools should report a warning for present fields that do not have any value.

Fields order and multiple occurrences
-------------------------------------

The field order does not matter. Multiple occurrences of a field name is
not supported.

The tool processing an ABOUT file or CSV/JSON/XLSX input will issue an error
when a field name occurs more than once in the input file.

Field referencing a file
------------------------

The actual value of some fields may be contained in another file. This is useful
for long texts or to reference a common text in multiple ABOUT files such as a
common license text. In this case the field name is suffixed with "_file" and
the field value must be a path pointing to the file that contains the actual
value of the field. If the field is referencing a license file, a "file" field
within the "licenses" group can be used. This path must be a POSIX path relative
to the path of the ABOUT file. The file content must be UTF-8-encoded text.

For example, this example shows the license file for the component is named
"linux.COPYING" and the notice file is "NOTICE":

        ..  code-block:: none

                license_file: linux.COPYING
                notice_file: NOTICE

Alternatvely, it can also write as the follow:

        ..  code-block:: none

                licenses:
                    -   file: linux.COPYING
                notice_file: NOTICE

In this example, the README file is stored in a doc directory, one directory
above the ABOUT file directory, using a relative POSIX path:

        ..  code-block:: none

                licenses:
                    -   file: ../docs/ruby.README

In addition, there may be cases that a license can have 2 or more referenced
license files. If this is the case, a comma ',' is used to identify multiple
files For instance:

        ..  code-block:: none

                license_expression: gpl-2.0-plus
                licenses:
                    -   key: gpl-2.0-plus
                        file: COPYING, COPYING.LESSER

Field referencing a URL
-----------------------

The value of a field may reference URLs such as a homepage or a download. In this
case the field name is suffixed with "_url" and the field value must be a valid
absolute URL starting with ftp://, http:// or https://. URLs are informational
and the content they may reference is ignored. For example, a download URL
is referenced this way:

        ..  code-block:: none

                download_url: http://www.kernel.org/pub/linux/kernel/v3.0/linux-3.4.20.tar.bz2

Flag fields
-----------

Flag fields have a "true" or "false" value. ``True``, ``T``, ``Yes``,
``Y`` or ``x`` must be interpreted as "true" in any case combination.
``False``, ``F``, ``No`` or ``N`` must be interpreted as "false"
in any case combination.

Referencing the file or directory documented by an ABOUT file
-------------------------------------------------------------

An ABOUT file documents one file or directory. The ``about_resource``
field reference the documented file or directory. The value of the ``about_resource``
field is the name or path of the referenced file or directory. There is also a
``ignored_resources`` field which can be used to ignore a set of subpaths inside the
directory which is being documented in the ABOUT file.

By convention, an ABOUT file is often stored in the same directory side-by-side
to the file or directory that it documents, but this is not mandatory.

For example, a file named django.ABOUT contains the following field to document
the django-1.2.3.tar.gz archive stored in the same directory:

        ..  code-block:: none

                about_resource: django-1.2.3.tar.gz

In this example, the ABOUT file documents a whole sub-directory:

        ..  code-block:: none

                about_resource: linux-kernel-2.6.23

In this example, the ABOUT file documents a whole sub-directory, with some
sub-paths under the directory ignored:

        ..  code-block:: none

                about_resource: linux-kernel-2.6.23
                ignored_resources: linux-kernel-2.6.23/Documentation

In this example, the ABOUT file documents the current directory, using a "." period to reference it:

        ..  code-block:: none

                about_resource: .

Mandatory fields
----------------------

When a tool processes an ABOUT file, it must issue an error if the
mandatory field is missing.

-   name: Component name.

Optional Information fields
---------------------------

-   about_resource: The resource this file referencing to.
-   ignored_resources: A list of paths under the ``about_resource`` path, which are
    not documented in the ABOUT file, and the information in the ABOUT file does not
    apply to these subpaths.
-   version: Component or package version. A component or package usually has a version,
    such as a revision number or hash from a version control system (for a snapshot checked
    out from VCS such as Subversion or Git). If not available, the version should be the date
    the component was provisioned, in an ISO date format such as 'YYYY-MM-DD'.
-   spec_version: The version of the ABOUT file format specification used for this file.
    This is provided as a hint to readers and tools in order to support future versions
    of this specification.
-   description: Component description, as a short text.
-   download_url: A direct URL to download the original file or archive documented
    by this ABOUT file.
-   homepage_url: URL to the homepage for this component.
-   changelog_file: Changelog file for the component.
-   package_url: Package URL for the package.
-   notes: Notes and comments about the component.

Optional Owner and Author fields
--------------------------------

-   owner: The name of the primary organization or person(s) that owns or
    provides the component.
-   owner_url: URL to the homepage for the owner.
-   contact: Contact information (such as an email address or physical address)
    for the component owner.
-   author: Name of the organization(s) or person(s) that authored the component.
-   author_file: Author file for the component.

Optional Licensing fields
-------------------------

-   copyright: Copyright statement for the component.
-   notice_file: Legal notice or credits for the component.
-   notice_url: URL to a legal notice for the component.
-   license_file: License file that applies to the component. For example, the
    name of a license file such as LICENSE or COPYING file extracted from a
    downloaded archive.
-   license_url: URL to the license text for the component.
-   license_expression: The ScanCode license expression that apply to
    the component. You can separate each identifier using " or " and " and " to
    document the relationship between multiple license identifiers, such as a choice
    among multiple licenses (No special characters are allowed).
-   license_name: The ScanCode license short name for the license
    (No special characters are allowed).
-   license_key: The ScanCode license key(s) for the component
    (No special characters are allowed).
-   spdx_license_key: The ScanCode LicenseDB spdx_license_key defined
    for the license at https://scancode-licensedb.aboutcode.org/index.html
-   spdx_license_expression: The license expression that use spdx_license_key

Notes
^^^^^
The license_* fields in the generated .ABOUT files are grouped under the "licenses" fields.
For instance,

        ..  code-block:: none

                licenses:
                    -   key: apache-2.0
                        name: Apache 2.0
                        file: apache-2.0.LICENSE
                        url: https://scancode-licensedb.aboutcode.org/apache-2.0.LICENSE
                        spdx_license_key: Apache-2.0

However, if user create .ABOUT file manually, it can also used the individual field name.


        ..  code-block:: none

                license_key: apache-2.0
                license_name: Apache 2.0
                license_file: apache-2.0.LICENSE
                license_url: https://scancode-licensedb.aboutcode.org/apache-2.0.LICENSE
                spdx_license_key: Apache-2.0

These groupping is only used in the generated .ABOUT files. The output from **gen**
will use the individual field name.

Optional Boolean flag fields
----------------------------

-   redistribute: Set this flag to yes if the component license requires source code
    redistribution. Defaults to no when absent.
-   track_changes: Set this flag to yes if the component license requires tracking changes made to
    a the component. Defaults to no when absent.
-   modified: Set this flag to yes if the component has been modified. Defaults to no when absent.
-   internal_use_only: Set this flag to yes if the component is used internal only.
    Defaults to no when absent.

Optional Boolean and Character fields
-------------------------------------

-   attribute: This field can be either in boolean value: ('yes', 'y', 'true',
    'x', 'no', 'n', 'false') or a character value field with no more than 2
    characters. Defaults to no when absent.

Optional Extension fields
-------------------------

You can create extension fields by prefixing them with a short prefix to
distinguish these from the standard fields (but this is not necessary).

Optional Extension fields to reference files stored in a version control system (VCS)
-------------------------------------------------------------------------------------
These fields provide a simple way to reference files stored in a version
control system. There are many VCS tools such as CVS, Subversion, Git,
ClearCase and GNU Arch. Accurate addressing of a file or directory revision
in each tool in a uniform way may not be possible. Some tools may require access
control via user/password or certificate and this information should not be
stored in an ABOUT file. This extension defines the 'vcs' field extension
prefix and a few common fields to handle the diversity of ways that VCS
tools reference files and directories under version control:

-   vcs_tool: VCS tool such as git, svn, cvs, etc.
-   vcs_repository: Typically a URL or some other identifier used by a
    VCS tool to point to a repository such as an SVN or Git repository URL.
-   vcs_path: Path used by a particular VCS tool to point to a file,
    directory or module inside a repository.
-   vcs_tag: tag name or path used by a particular VCS tool.
-   vcs_branch: branch name or path used by a particular VCS tool.
-   vcs_revision: revision identifier such as a revision hash or version number.

Some examples for using the vcs_* extension fields include:

        ..  code-block:: none

                vcs_tool: svn
                vcs_repository: http://svn.code.sf.net/p/inkscape/code/inkscape_project/
                vcs_path: trunk/inkscape_planet/
                vcs_revision: 22886

or:

        ..  code-block:: none

                vcs_tool: git
                vcs_repository: git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git
                vcs_path: tools/lib/traceevent
                vcs_revision: b59958d90b3e75a3b66cd311661535f94f5be4d1

Optional Extension fields for checksums
---------------------------------------
These fields support checksums (such as SHA1 and MD5)commonly provided with
downloaded archives to verify their integrity. A tool can optionally use these
to verify the integrity of a file documented by an ABOUT file.

-   checksum_md5: MD5 for the file documented by this ABOUT file in the "about_resource" field.
-   checksum_sha1: SHA1 for the file documented by this ABOUT file in the "about_resource" field.
-   checksum_sha256: SHA256 for the file documented by this ABOUT file in
    the "about_resource" field.

Some examples:

        ..  code-block:: none

                checksum_md5: f30b9c173b1f19cf42ffa44f78e4b96c

Fields Type
-----------

Following are the types for the supporting fields (All the custom fields
will be treated as **StringField**):

.. list-table::
    :widths: 10 10
    :header-rows: 1

    * - Type
      - Fields
    * - AboutResourceField
      - | about_resource
        | ignored_resources
    * - BooleanField
      - | redistribute
        | track_changes
        | modified
        | internal_use_only
    * - BooleanAndTwoCharactersField
      - attribute
    * - FileTextField
      - | license_file
        | notice_file
        | changelog_file
        | author_file
    * - ListField
      - | license_key
        | license_name
        | spdx_license_key
    * - PackageUrlField
      - package_url
    * - SingleLineField
      - | name
        | version
        | license_expression
        | spdx_license_expression
        | declared_license_expression
        | other_license_expression
        | vcs_tool
        | vcs_repository
        | vcs_path
        | vcs_tag
        | vcs_branch
        | vcs_revision
        | checksum_md5
        | checksum_sha1
        | checksum_sha256
        | spec_version
    * - StringField
      - | description
        | notes
        | copyright
        | owner
        | contact
        | author
    * - UrlField
      - | download_url
        | homepage_url
        | notice_url
        | owner_url
    * - UrlListField
      - license_url

Type description
----------------

-   **AboutResourceField**: Path or list of path to the about resource.
-   **BooleanField**: An flag field with a boolean value. Validated value is False,
    True or None.
-   **BooleanAndTwoCharactersField**: Field with either a boolean value or
    character(s) value (at most 2 characters). Validated value is False, True,
    None or character value.
-   **FileTextField**: A path field pointing to one or more text files such as
    license files. The validated value is an ordered dict of path->Text or None
    if no location or text could not be loaded.
-   **ListField**: A field containing a list of string values, one per line. The
    validated value is a list.
-   **PackageUrlField**: A Package URL field. The validated value is a purl
-   **SingleLineField**: A field containing a string value on a single line. The
    validated value is a string.
-   **StringField**: A field containing a string value possibly on multiple lines.
    The validated value is a string.
-   **UrlField**: A URL field. The validated value is a URL.
-   **UrlListField**: A URL field. The validated value is a list of URLs.
