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
import pytest

from geofencing.common import mongo_polygon_from_polygon_filter, polygon_filter_from_mongo_polygon
from geofencing.filters import PointFilter

__author__ = "EUROCONTROL (SWIM)"


@pytest.mark.parametrize('polygon_filter, expected_mongo_polygon', [
    ([PointFilter(1, 2), PointFilter(3, 4), PointFilter(5, 6)],
     [[[1, 2], [3, 4], [5, 6]]])
])
def test_polygon_filter_to_mongo_polygon(polygon_filter, expected_mongo_polygon):
    assert expected_mongo_polygon == mongo_polygon_from_polygon_filter(polygon_filter)


@pytest.mark.parametrize('mongo_polygon, expected_polygon_filter', [
    ([[[1, 2], [3, 4], [5, 6]]],
     [PointFilter(1, 2), PointFilter(3, 4), PointFilter(5, 6)])
])
def test_polygon_filter_to_mongo_polygon(mongo_polygon, expected_polygon_filter):
    assert expected_polygon_filter == polygon_filter_from_mongo_polygon(mongo_polygon)
