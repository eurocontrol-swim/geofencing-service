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
from typing import List, Any, Union, Dict

__author__ = "EUROCONTROL (SWIM)"

GeoJSONPolygonCoordinates = List[List[List[Union[float, int]]]]


class CompareMixin:
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and other.__dict__ == self.__dict__

    def __ne__(self, other: Any) -> bool:
        return not other == self


class Polygon(CompareMixin):
    def __init__(self, type: str, coordinates: List[List[List[float]]]) -> None:
        self.type = type
        self.coordinates = coordinates

    @classmethod
    def from_dic(cls, object_dict: Dict[str, Any]):
        """

        :return: Polygon
        """
        return cls(
            type=object_dict['type'],
            coordinates=object_dict['coordinates']
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'coordinates': self.coordinates
        }


class Circle(CompareMixin):
    def __init__(self, type: str, coordinates: List[List[List[float]]], radius: float) -> None:
        self.type = type
        self.radius = radius
        self.coordinates = coordinates

    @classmethod
    def from_dic(cls, object_dict: Dict[str, Any]):
        """

        :return: Polygon
        """
        return cls(
            type=object_dict['type'],
            radius=object_dict['radius'],
            coordinates=object_dict['coordinates']
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type,
            'radius': self.radius,
            'coordinates': self.coordinates
        }

