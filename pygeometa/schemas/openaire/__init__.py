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
        

        header_ = md.get('header')
        result_ = md.get('results', {}).get('record', {}).get('result')[0]  # in some case no 'record', check later

        # mcf: metadata
        metadata_ = result_.get('metadata', {}).get('oaf:entity', {}).get('oaf:result')

        pids_ = metadata_.get('pid')

        pids_value_ = [i.get('$') for i in pids_]
        children_instances_ = metadata_.get('children', {}).get('instance')
        main_id_, main_instance_ = process_id_and_instance(pids_, children_instances_)

        mcf['metadata']['identifier'] = main_id_
        mcf['metadata']['additional_identifiers'] = pids_value_
        mcf['metadata']['language'] = header_.get('locale', {}).get('$')

        ## relation
        
        resource_type_ = metadata_.get('resourcetype', {}).get('@classname')
        instance_type_ = main_instance_.get('instancetype', {}).get('@classname')
        if resource_type_ is not None and resource_type_ != 'UNKNOWN':
            mcf['metadata']['hierarchylevel'] = resource_type_
        elif instance_type_ is not None and instance_type_ != 'UNKNOWN':
            mcf['metadata']['hierarchylevel'] = instance_type_
        
        mcf['metadata']['datestamp'] = result_.get('header', {}).get('dri:dateOfCollection', {}).get('$')
        mcf['metadata']['dataseturi'] = main_instance_.get('webresource', {}).get('url', {}).get('$')

        # mcf: identification

        mcf['identification']['language'] = metadata_.get('language', {}).get('@classid')
        title_ = metadata_.get('title', {})
        if isinstance(title_, list):
            mcf['identification']['title'] = [t.get('$') for t in title_]
        elif isinstance(title_, dict):
            mcf['identification']['title'] = title_.get('$')
        description_ = metadata_.get('description', {}).get('$')
        mcf['identification']['abstract'] = description_
        ## edition/version
        ## topiccategory

        right_ = metadata_.get('bestaccessright', {}).get('@classname')
        instance_right_ = main_instance_.get('accessright', {}).get('@classname')
        if right_ is not None and right_ != 'unspecified':
            mcf['identification']['rights'] = right_
        elif instance_right_ is not None and instance_right_ != 'unspecified':
            mcf['identification']['rights'] = instance_right_
        else:
            mcf['identification']['rights'] = 'unspecified'
        
        license_ = main_instance_.get('license', {}).get('$')
        if license_:
            mcf['identification']['license'] = {'name': license_, 'url': ''}
        
        ## url
        dates_ = metadata_.get('relevantdate')
        dates_dict = {}
        if isinstance(dates_, list):
            for d in dates_:
                d_name_ = d.get('@classname')
                d_value = d.get('$')
                if d_name_ and d_value:
                    dates_dict[d_name_] = d_value
        elif isinstance(dates_, dict):
            d_name_ = dates_.get('@classname')
            d_value = dates_.get('$')
            if d_name_ and d_value:
                dates_dict[d_name_] = d_value
        if dates_dict: 
            mcf['identification']['dates'] = dates_dict
        ## keywords

        subjects_ = metadata_.get('subject')
        if isinstance(subjects_, dict):
            mcf['identification']['keywords'] = process_keywords([subjects_])
        elif isinstance(subjects_, list):
            mcf['identification']['keywords'] = process_keywords(subjects_)

        print(mcf)
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


def process_id_and_instance(ids: list, instances: list) -> tuple[str, object]:
    """
    Find one pair of children instance and pid with the same doi. 
    Use the instance as the entry of mcf attributes. Use the doi as the identifier.
    If can't find a match, use instance[0] and pid[0]
    """

    # get the first doi as main id
    if len(ids) == 0:
        LOGGER.info('identifier missed')
        return None, instances[0] if instances else None
    first_id = ids[0]
    main_id = first_id.get('$') if first_id else None
    if len(ids) > 1:
        for i in ids:
            if i.get('@classid') == "doi":
                main_id = i.get('$')
                break
    if len(instances) == 0:
        return main_id, None
    
    # get the instance matched with the main id
    main_instance = instances[0]
    for ins in instances:
        pid = ins.get('pid', {})
        if isinstance(pid, list): # instance has multiple pid
            pid_values = [i.get('$') for i in pid]
            if main_id in pid_values:
                main_instance = ins
                break
        elif isinstance(pid, dict): # instance has one pid
            if pid.get('$') == main_id:
                main_instance = ins
                break
        else:
            continue
    return main_id, main_instance
    
def process_keywords(subjects: list) -> dict:
    """
    convert openaire keywords to mcf keywords

    group keywords by classid
    
    """
    unique_kid = list(set([s.get('@classid') for s in subjects]))
    
    keyword_dict = {kid: {'keywords': [], 'keywords_type': ''} for kid in unique_kid} 
    for kid in unique_kid:
        for s in subjects:
            if s.get('@classid') == kid:
                keyword_dict[kid]['keywords'].append(s.get('$'))
 