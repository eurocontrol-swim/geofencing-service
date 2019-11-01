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
from dataclasses import dataclass

from marshmallow import Schema, pre_dump, ValidationError
from marshmallow.fields import String, Nested, Integer, DateTime, Dict, List, Float

__author__ = "EUROCONTROL (SWIM)"


@dataclass
class Point:
    lat: float
    lon: float


class PointSchema(Schema):
    lat = Float(data_key='LAT')
    lon = Float(data_key='LON')


class AirspaceVolumeSchema(Schema):
    polygon = Nested(PointSchema, many=True)
    lower_limit_in_m = Integer(data_key="lowerLimit", missing=None)
    lower_vertical_reference = String(data_key="lowerVerticalReference")
    upper_limit_in_m = Integer(data_key="upperLimit", missing=None)
    upper_vertival_reference = String(data_key="upperVerticalReference")

    @pre_dump
    def handle_polygon(self, item, many, **kwargs):
        if isinstance(item['polygon'], list):
            coords = item['polygon'][0]
        elif isinstance(item['polygon'], dict):
            coords = item['polygon']['coordinates'][0]
        else:
            raise ValidationError("invalid polygon type")

        item['polygon'] = [Point(lat, lon) for lat, lon in coords]

        return item


class DailyScheduleSchema(Schema):
    day = String()
    start_time = DateTime(data_key='startTime', required=True)
    end_time = DateTime(data_key='endTime', required=True)


class ApplicableTimePeriodSchema(Schema):
    permanent = String()
    start_date_time = DateTime(data_key='startDateTime', required=True)
    end_date_time = DateTime(data_key='endDateTime', required=True)
    daily_schedule = Nested(DailyScheduleSchema, many=True, data_key='dailySchedule')


class AuthorityEntitySchema(Schema):
    authority_id = String(primary_key=True)
    name = String(required=True)
    contact_name = String(data_key='contactName')
    service = String()
    email = String()
    site_url = String(data_key='siteUrl')
    phone = String()


class NotificationRequirementSchema(Schema):
    authority = Nested(AuthorityEntitySchema, required=True)
    interval_before = String(data_key='intervalBefore', required=True)


class AuthorizationRequirementSchema(Schema):
    authority = Nested(AuthorityEntitySchema, required=True)


class AuthoritySchema(Schema):
    requires_notification_to = Nested(NotificationRequirementSchema, data_key="requiresNotificationTo")
    requires_authorization_from = Nested(AuthorizationRequirementSchema, data_key="requiresAuthorisationFrom")


class DataSourceSchema(Schema):
    # author = ReferenceField(AuthorityEntity, required=True)
    creation_date_time = DateTime(data_key='creationDateTime', required=True)
    update_date_time = DateTime(data_key='endDateTime')


class UASZoneSchema(Schema):
    identifier = String(required=True)
    name = String(required=True)
    type = String()
    restriction = String()
    region = Integer()
    data_capture_prohibition = String(data_key='dataCaptureProhibition')
    u_space_class = String(data_key='uSpaceClass')
    message = String()
    reason = String(many=True)
    country = String()

    airspace_volume = Nested(AirspaceVolumeSchema, data_key='airspaceVolume', required=True)
    applicable_time_period = Nested(ApplicableTimePeriodSchema, data_key='applicableTimePeriod')
    authority = Nested(AuthoritySchema)
    data_source = Nested(DataSourceSchema, data_key='dataSource')
    extended_properties = Dict(data_key='extendedProperties')
