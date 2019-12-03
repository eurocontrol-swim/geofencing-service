"""
Copyright 2019 EUROCONTROL
==========================================

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
   disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
   disclaimer in the documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products
   derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

==========================================

Editorial note: this license is an instance of the BSD license template as provided by the Open Source Initiative:
http://opensource.org/licenses/BSD-3-Clause

Details on EUROCONTROL: http://www.eurocontrol.int
"""
from marshmallow import post_load, Schema, ValidationError
from marshmallow.fields import Nested, AwareDateTime, String, List, Integer

from geofencing.filters import UASZonesFilter

__author__ = "EUROCONTROL (SWIM)"


class PointFilterSchema(Schema):
    lat = String(data_key='LAT')
    lon = String(data_key='LON')

    @post_load
    def convert_to_float(self, data, **kwargs):
        data['lat'] = float(data['lat'])
        data['lon'] = float(data['lon'])

        return data


def validate_polygon(value):
    if len(value) < 3:
        raise ValidationError('Loop must have at least 3 different vertices')

    if value[0] != value[-1]:
        raise ValidationError('Loop is not closed')


class AirspaceVolumeFilterSchema(Schema):
    polygon = Nested(PointFilterSchema, many=True, validate=validate_polygon)
    lower_limit_in_m = Integer(data_key="lowerLimit", missing=None)
    lower_vertical_reference = String(data_key="lowerVerticalReference", missing=None)
    upper_limit_in_m = Integer(data_key="upperLimit", missing=None)
    upper_vertival_reference = String(data_key="upperVerticalReference", missing=None)


class UASZonesFilterSchema(Schema):
    airspace_volume = Nested(AirspaceVolumeFilterSchema, data_key='airspaceVolume')
    start_date_time = AwareDateTime(data_key='startDateTime')
    end_date_time = AwareDateTime(data_key='endDateTime')
    request_id = String(data_key='requestID')
    regions = List(Integer)
    updated_after_date_time = AwareDateTime(data_key='updatedAfterDateTime')

    @post_load
    def load_filter(self, item, **kwargs):
        return UASZonesFilter.from_dict(item)
