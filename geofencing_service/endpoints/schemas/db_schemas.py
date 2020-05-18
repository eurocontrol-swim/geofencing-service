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
from flask import current_app
from marshmallow import Schema, post_dump, pre_load, post_load, validate, ValidationError, EXCLUDE
from marshmallow.fields import String, Nested, Integer, Dict, AwareDateTime, List, Email, URL, \
    Boolean, Float

from geofencing_service.db.models import UASZone, UomDistance, UASZonesFilter, AirspaceVolume
from geofencing_service.endpoints.utils import time_str_from_datetime_str, \
    make_datetime_string_aware, datetime_str_from_time_str, is_valid_duration_format, \
    circumscribed_polygon_from_circle

__author__ = "EUROCONTROL (SWIM)"


FEET_METERS_RATIO = 0.3048


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


def validate_polygon_coordinates_linestring(linestring):

    if len(linestring) < 3:
        raise ValidationError('Linestring has less than 3 different vertices.')

    if linestring[0] != linestring[-1]:
        raise ValidationError('Linestring is not closed.')


class PolygonSchema(BaseSchema):

    type = String(required=True)
    coordinates = List(
        List(
            List(
                Float,
                validate=validate.Length(max=2, min=2)
            ),
            validate=validate_polygon_coordinates_linestring,
        ),
        required=True
    )


def validate_radius(value):
    if value < 0:
        raise ValidationError('Negative value not allowed.')


class CircleSchema(BaseSchema):
    type = String(required=True)
    center = List(Float, required=True)
    radius = Float(required=True, validate=validate_radius)


def validate_horizontal_projection(value):
    if 'type' not in value:
        raise ValidationError(
            message={'type': ['Missing data for required field.']}
        )

    if value['type'] == 'Circle':
        CircleSchema().load(value)
    elif value['type'] == 'Polygon':
        PolygonSchema().load(value)
    else:
        raise ValidationError(
            message={'type': ['Invalid geometry type. Expected one of [Circle, Polygon]']})

    return True


class AirspaceVolumeSchema(BaseSchema):
    horizontal_projection = Dict(data_key="horizontalProjection",
                                 validate=validate_horizontal_projection)
    lower_limit = Integer(data_key="lowerLimit", missing=None)
    lower_vertical_reference = String(data_key="lowerVerticalReference", missing=None)
    upper_limit = Integer(data_key="upperLimit", missing=None)
    upper_vertical_reference = String(data_key="upperVerticalReference", missing=None)
    uom_dimensions = String(data_key="uomDimensions")
    circle = Nested(CircleSchema)

    @post_load
    def handle_horizontal_projection_load(self, data, **kwargs):
        if data['horizontal_projection']['type'] == 'Circle':
            circle = data['horizontal_projection']

            radius_in_m = circle['radius']
            if data['uom_dimensions'] == UomDistance.METERS.value:
                radius_in_m = circle['radius'] * FEET_METERS_RATIO

            data['horizontal_projection'] = circumscribed_polygon_from_circle(
                lon=circle['center'][0],
                lat=circle['center'][1],
                radius_in_m=radius_in_m,
                n_edges=current_app.config['POLYGON_TO_CIRCLE_EDGES']
            )

            data['circle'] = circle

        return AirspaceVolume(**data)

    @post_dump
    def handle_horizontal_projection_dump(self, data, **kwargs):
        if data['circle']:
            data['horizontalProjection'] = data['circle']

        del data['circle']

        return data


class UASZonesFilterSchema(BaseSchema):
    airspace_volume = Nested(AirspaceVolumeSchema, data_key='airspaceVolume')
    start_date_time = AwareDateTime(data_key='startDateTime')
    end_date_time = AwareDateTime(data_key='endDateTime')
    regions = List(Integer)

    @post_load
    def load_filter(self, data, **kwargs):
        return UASZonesFilter(**data)

    @pre_load
    def handle_datetime_awareness_load(self, data, **kwargs):
        data["startDateTime"] = make_datetime_string_aware(data["startDateTime"])
        data["endDateTime"] = make_datetime_string_aware(data["endDateTime"])

        return data


class DailyPeriodSchema(BaseSchema):
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


class TimePeriodSchema(BaseSchema):
    permanent = String()
    start_date_time = AwareDateTime(data_key='startDateTime', required=True)
    end_date_time = AwareDateTime(data_key='endDateTime', required=True)
    schedule = Nested(DailyPeriodSchema, many=True, data_key='schedule')

    @post_dump
    def handle_datetime_awareness_dump(self, data, **kwargs):
        data["startDateTime"] = make_datetime_string_aware(data["startDateTime"])
        data["endDateTime"] = make_datetime_string_aware(data["endDateTime"])

        return data


def validate_duration(value: str) -> bool:
    """

    :param value:
    :return:
    """
    return is_valid_duration_format(value)


class AuthoritySchema(BaseSchema):
    name = String(required=True, validate=validate.Length(max=200))
    service = String(validate=validate.Length(max=200))
    email = Email()
    contact_name = String(data_key='contactName', validate=validate.Length(max=200))
    site_url = URL(data_key='siteURL')
    phone = String(validate=validate.Length(max=200))
    purpose = String(required=True)
    interval_before = String(data_key='intervalBefore', validate=validate_duration)


class UASZoneSchema(BaseSchema):
    identifier = String(required=True)
    country = String(required=True)
    name = String()
    type = String(required=True)
    restriction = String(required=True)
    restriction_conditions = List(String(), data_key='restrictionConditions')
    region = Integer()
    reason = List(String(), validate=validate.Length(max=9))
    other_reason_info = String(data_key='otherReasonInfo')
    regulation_exemption = String(data_key='regulationExemption')
    u_space_class = String(data_key='uSpaceClass')
    message = String()

    zone_authority = Nested(AuthoritySchema, data_key='zoneAuthority', required=True)
    applicability = Nested(TimePeriodSchema)
    geometry = Nested(AirspaceVolumeSchema, required=True, many=True)
    extended_properties = Dict(data_key='extendedProperties')

    @post_load
    def make_mongo_object(self, data, **kwargs):
        """
        A document schema will be eventually loaded in a mongoengine object for possible storing in
        DB
        :param data:
        :param kwargs:
        :return:
        """
        return UASZone(**data)

    @post_dump
    def handle_mongoengine_dict_field(self, data, **kwargs):
        """
        Apparently the dict field is not serialized properly to a dict object so it has to be done
        manually.
        :param data:
        :param kwargs:
        :return:
        """
        data['extendedProperties'] = dict(data['extendedProperties'])

        return data


class SubscriptionSchema(BaseSchema):
    active = Boolean(required=True)
