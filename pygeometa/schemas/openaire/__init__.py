# =================================================================
#
# Terms and Conditions of Use
#
# Unless otherwise noted, computer program source code of this
# distribution # is covered under Crown Copyright, Government of
# Canada, and is distributed under the MIT License.
#
# The Canada wordmark and related graphics associated with this
# distribution are protected under trademark law and copyright law.
# No permission is granted to use them outside the parameters of
# the Government of Canada's corporate identity program. For
# more information, see
# http://www.tbs-sct.gc.ca/fip-pcim/index-eng.asp
#
# Copyright title to all 3rd party software distributed with this
# software is held by the respective copyright holders as noted in
# those files. Users are asked to read the 3rd Party Licenses
# referenced with those assets.
#
# Copyright (c) 2025 Tom Kralidis, Jiarong Li, Paul van Genuchten
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

from datetime import date, datetime
import logging
import os
import json
from typing import Union

from pygeometa import __version__
from pygeometa.core import get_charstring
from pygeometa.helpers import json_dumps
from pygeometa.schemas.base import BaseOutputSchema

THISDIR = os.path.dirname(os.path.realpath(__file__))

LOGGER = logging.getLogger(__name__)


class OpenAireOutputSchema(BaseOutputSchema):
    """OpenAire: record schema"""

    def __init__(self):
        """
        Initialize object

        :returns: pygeometa.schemas.base.BaseOutputSchema
        """

        description = 'OpenAire'

        super().__init__('openaire', description, 'json', THISDIR)

    def import_(self, metadata: str) -> dict:
        """
        Import metadata into MCF

        :param metadata: string of metadata content

        :returns: `dict` of MCF content
        """

        # Initialized mcf
        mcf = {
            'mcf': {
                'version': '1.0',
            },
            'spatial': {},
            'metadata': {},
            'identification': {
                'extents': {
                    'spatial': []
                }
            },
            'contact': {},
            'distribution': {},
            'tag': 'test'
        }

        # Process metadata (convert XML to JSON if needed)
        metadata = xml_to_json(metadata)
        md = json.loads(metadata).get('response')
        if md is None:
            LOGGER.info('invalid openaire metadata')
            return mcf
        

        header = md.get('header')
        result = md.get('results', {}).get('record', {}).get('result')[0]  # in some case no 'record', check later

        # mcf: metadata
        metadata_ = result.get('metadata', {}).get('oaf:entity', {}).get('oaf:result')
        
        ids_ = []

        for i in metadata_.get('originalId'):
            ids_.append(i.get('$'))

        for i in metadata_.get('pid'):
            ids_.append(i.get('$'))

        adids_, id_ = process_id(ids_)
        mcf['metadata']['identifier'] = id_
        mcf['metadata']['additional_identifiers'] = adids_
        mcf['metadata']['language'] = header.get('locale', {}).get('$')

        print(mcf)



        # id_ = md.get('identifier', md.get('@id',''))
        # mcf['metadata']['identifier'] = id_
        
        return mcf

    def write(self, mcf: dict, stringify: str = True) -> Union[dict, str]:
        """
        Write outputschema to JSON string buffer

        :param mcf: dict of MCF content model
        :param stringify: whether to return a string representation (default)
                          else native (dict, etree)

        :returns: `dict` or `str` of MCF as Schema.org
        """

        # no write implementation for now

        return 'test'
      
        # return None

def xml_to_json(content: str) -> str:
    """
    Convert XML to JSON if content is detected as XML
    
    Write it later
    """
    return content


def process_id(ids: list) -> tuple[list, str]:

    """
    Get the identifier and additional_identifier from the list of originalIds and pids
    
    """
    
    if len(ids) < 1:
        return [], None
    else:
        unique_ids = list(set(ids))
        main_id = unique_ids[0]
        for i in unique_ids:
            if i.startswith('10.'): # use doi is main id if exists
                main_id = i
                break
        return unique_ids, main_id
