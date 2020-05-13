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
__author__ = "EUROCONTROL (SWIM)"

import json
import re
from datetime import datetime, timezone

import dateutil.parser

import geog
import numpy as np
import shapely.geometry


_ISO_8601_CHECK_PATTERN = r'^P(?!$)((?P<years>\d+)Y)?((?P<months>\d+)M)?(\d+W)?(\d+D)?(T(?=\d)(\d+H)?(\d+M)?(\d+S)?)?$'
_iso_8601_check_regex = re.compile(_ISO_8601_CHECK_PATTERN)


def time_str_from_datetime_str(date_string: str) -> str:
    """
    Extracts the time parts of a datetime.

    Example:
        2019-12-03T09:00:00.12345 will be converted to:
        09:00:00.12345

    :param date_string:
    :return:
    """
    return date_string.split('T')[1]


def datetime_str_from_time_str(time_str: str) -> str:
    """
    Applies a dummy date on a time string for further storage as datetime

    :param time_str:
    :return:
    """
    return f"2000-01-01T{time_str}"


def make_datetime_string_aware(dt: str) -> str:
    """
    Applies UTC timezone on a datetime string,

    :param dt:
    :return:
    """
    return make_datetime_aware(dateutil.parser.parse(dt)).isoformat()


def make_datetime_aware(dt: datetime) -> datetime:
    """
    Applies UTC timezone of a datetime

    :param dt:
    :return:
    """
    return dt.replace(tzinfo=timezone.utc)


def is_valid_duration_format(iso_duration: str) -> bool:
    """
    Validates ISO 8601 duration strings as described at https://en.wikipedia.org/wiki/ISO_8601#Durations
    :param iso_duration:
    :return:
    """
    return _iso_8601_check_regex.match(iso_duration) is not None


def inscribed_polygon_from_circle(lon: float, lat: float, radius_in_m: float, n_edges: int):
    """
    :param lon:
    :param lat:
    :param radius_in_m:
    :param n_edges: how many edges should the polygon have
    :return:
    """
    center_point = shapely.geometry.Point([lon, lat])

    # linspace accepts number of points so we add 1 to have the desired number of edges
    angles = np.linspace(0, 360, n_edges + 1)

    polygon = geog.propagate(center_point, angles, radius_in_m)

    result = shapely.geometry.mapping(shapely.geometry.Polygon(polygon))

    return json.loads(json.dumps(result))


def circumscribed_polygon_from_circle(lon: float, lat: float, radius_in_m: float, n_edges: int):
    """
    By increasing the radius 5% we get an approximation of the circumscribed polygon
    :param lon:
    :param lat:
    :param radius_in_m:
    :param n_edges:
    :return:
    """

    return inscribed_polygon_from_circle(lon, lat, radius_in_m * 1.05, n_edges)
