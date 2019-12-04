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
from marshmallow import Schema, pre_dump, post_dump, pre_load, post_load
from marshmallow.fields import String, Nested, Integer, Dict, Float, AwareDateTime, List, Email, URL, Boolean

from geofencing_server.common import point_list_from_geojson_polygon_coordinates, geojson_polygon_coordinates_from_point_list,\
    Point
from geofencing_server.db.models import UASZone, AuthorityEntity
from geofencing_server.endpoints.schemas.filters_schemas import validate_polygon
from geofencing_server.endpoints.utils import time_str_from_datetime_str, make_datetime_string_aware, \
    datetime_str_from_time_str

__author__ = "EUROCONTROL (SWIM)"


class PointSchema(Schema):
    lat = String(data_key='LAT')
    lon = String(data_key='LON')


class AirspaceVolumeSchema(Schema):
    polygon = Nested(PointSchema, many=True, validate=validate_polygon)
    lower_limit_in_m = Integer(data_key="lowerLimit", missing=None)
    lower_vertical_reference = String(data_key="lowerVerticalReference", missing=None)
    upper_limit_in_m = Integer(data_key="upperLimit", missing=None)
    upper_vertical_reference = String(data_key="upperVerticalReference", missing=None)

    @pre_dump
    def handle_geojson_polygon_dump(self, item, **kwargs):
        """
        Converts a GeoJSON polygon (as it is found in a mongo polygon field) to a list of Point i.e.:

        this GeoJSON polygon:
        {
            'type': 'Polygon',
            'coordinates': [
                [[50.863648, 4.329385],
                 [50.865348, 4.328055],
                 [50.86847, 4.317369],
                 [50.863648, 4.329385]]
            ]
        }
        will be converted to:
        [
             Point(lat=50.863648, lon=4.329385),
             Point(lat=50.865348, lon=4.328055),
             Point(lat=50.86847, lon=4.317369),
             Point(lat=50.863648, lon=4.329385)
        ]
        :param item:
        :param many:
        :param kwargs:
        :return:
        """
        coordinates = item['polygon']['coordinates'] if 'coordinates' in item['polygon'] else item['polygon']

        item['polygon']: List[Point] = point_list_from_geojson_polygon_coordinates(coordinates)

        return item

    @post_load
    def handle_geojson_polygon_load(self, item, **kwargs):
        """
        Converts a list of point coordinates to GeoJSON polygon coordinates:

        Example:
        this list of points:
        [
             {"lat": 50.863648, "lon": 4.329385},
             {"lat": 50.865348, "lon": 4.328055},
             {"lat": 50.86847, "lon": 4.317369},
             {"lat": 50.863648, "lon": 4.329385}
        ]
        will be converted to:
        [
            [[50.863648, 4.329385],
             [50.865348, 4.328055],
             [50.86847, 4.317369],
             [50.863648, 4.329385]]
        ]
        :param item:
        :param kwargs:
        :return:
        """
        point_list = [Point.from_dict(coords) for coords in item['polygon']]

        item['polygon'] = geojson_polygon_coordinates_from_point_list(point_list)

        return item


class DailyScheduleSchema(Schema):
    day = String()
    start_time = AwareDateTime(data_key='startTime', required=True)
    end_time = AwareDateTime(data_key='endTime', required=True)

    @pre_load
    def convert_time_to_datetime(self, data, **kwargs):
        data['startTime'] = datetime_str_from_time_str(data['startTime'])
        data['endTime'] = datetime_str_from_time_str(data['endTime'])

        return data

    @post_dump
    def handle_time_format(self, data, **kwargs):
        """
        Makes the dumped datetimes timezone aware as it seems that this info is not kept in mongodb
        TODO: to be checked

        :param data:
        :param many:
        :param kwargs:
        :return:
        """

        data['startTime'] = time_str_from_datetime_str(make_datetime_string_aware(data['startTime']))
        data['endTime'] = time_str_from_datetime_str(make_datetime_string_aware(data['endTime']))

        return data


class ApplicableTimePeriodSchema(Schema):
    permanent = String()
    start_date_time = AwareDateTime(data_key='startDateTime', required=True)
    end_date_time = AwareDateTime(data_key='endDateTime', required=True)
    daily_schedule = Nested(DailyScheduleSchema, many=True, data_key='dailySchedule')

    @post_dump
    def handle_datetime_awareness(self, data, **kwargs):
        data["startDateTime"] = make_datetime_string_aware(data["startDateTime"])
        data["endDateTime"] = make_datetime_string_aware(data["endDateTime"])

        return data


class AuthorityEntitySchema(Schema):
    authority_id = String(primary_key=True)
    name = String(required=True)
    contact_name = String(data_key='contactName')
    service = String()
    email = Email()
    site_url = URL(data_key='siteURL')
    phone = String()

    @post_load
    def make_mongo_object(self, data, **kwargs):
        """
        A document schema will be eventually loaded in a mongoengine object for possible storing in DB
        :param data:
        :param kwargs:
        :return:
        """
        return AuthorityEntity(**data)


class NotificationRequirementSchema(Schema):
    authority = Nested(AuthorityEntitySchema, required=True)
    interval_before = String(data_key='intervalBefore', required=True)


class AuthorizationRequirementSchema(Schema):
    authority = Nested(AuthorityEntitySchema, required=True)


class AuthoritySchema(Schema):
    requires_notification_to = Nested(NotificationRequirementSchema, data_key="requiresNotificationTo")
    requires_authorization_from = Nested(AuthorizationRequirementSchema, data_key="requiresAuthorisationFrom")


class DataSourceSchema(Schema):
    author = String(required=True)
    creation_date_time = AwareDateTime(data_key='creationDateTime', required=True)
    update_date_time = AwareDateTime(data_key='updateDateTime')

    @post_dump
    def handle_datetime_awareness(self, data, **kwargs):
        data["creationDateTime"] = make_datetime_string_aware(data["creationDateTime"])
        data["updateDateTime"] = make_datetime_string_aware(data["updateDateTime"])

        return data


class UASZoneSchema(Schema):
    identifier = String(required=True)
    name = String(required=True)
    type = String()
    restriction = String()
    restriction_conditions = List(String(), data_key='restrictionConditions')
    region = Integer()
    data_capture_prohibition = String(data_key='dataCaptureProhibition')
    u_space_class = String(data_key='uSpaceClass')
    message = String()
    reason = List(String())
    country = String()

    airspace_volume = Nested(AirspaceVolumeSchema, data_key='airspaceVolume', required=True)
    applicable_time_period = Nested(ApplicableTimePeriodSchema, data_key='applicableTimePeriod')
    authority = Nested(AuthoritySchema)
    data_source = Nested(DataSourceSchema, data_key='dataSource')
    extended_properties = Dict(data_key='extendedProperties')

    @post_load
    def make_mongo_object(self, data, **kwargs):
        """
        A document schema will be eventually loaded in a mongoengine object for possible storing in DB
        :param data:
        :param kwargs:
        :return:
        """
        return UASZone(**data)


class SubscriptionSchema(Schema):
    active = Boolean()
