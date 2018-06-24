# copied from github.com/fragmuffin/cqparts car.py example file

import cadquery
import cqparts
from cqparts.params import *
from cqparts.display import render_props, display
from cqparts.constraint import Fixed, Coincident
from cqparts.constraint import Mate
from cqparts.utils.geometry import CoordSystem
import os
import sys
import tempfile

class Wheel(cqparts.Part):
    # Parameters
    width = PositiveFloat(10, doc="width of wheel")
    diameter = PositiveFloat(30, doc="wheel diameter")

    # default appearance
    _render = render_props(template='wood_dark')

    def make(self):
        wheel = cadquery.Workplane('XY') \
            .circle(self.diameter / 2).extrude(self.width).chamfer(1)
        hole = cadquery.Workplane('XY') \
            .circle(2).extrude(self.width/2).faces(">Z") \
            .circle(4).extrude(self.width/2)
        wheel = wheel.cut(hole)
        return wheel

    def get_cutout(self, clearance=0):
        # A cylinder with a equal clearance on every face
        return cadquery.Workplane('XY', origin=(0, 0, -clearance)) \
            .circle((self.diameter / 2) + clearance) \
            .extrude(self.width + (2 * clearance))

class Axle(cqparts.Part):
    # Parameters
    length = PositiveFloat(50, doc="axle length")
    diameter = PositiveFloat(10, doc="axle diameter")

    # default appearance
    _render = render_props(color=(50, 50, 50))  # dark grey

    def make(self):
        axle = cadquery.Workplane('ZX', origin=(0, -self.length/2, 0)) \
            .circle(self.diameter / 2).extrude(self.length)
        cutout = cadquery.Workplane('ZX', origin=(0, -self.length/2, 0)) \
            .circle(1.5).extrude(10)
        axle = axle.cut(cutout)
        cutout = cadquery.Workplane('XZ', origin=(0, self.length/2, 0)) \
            .circle(1.5).extrude(10)
        axle = axle.cut(cutout)
        return axle

    # wheel mates, assuming they rotate around z-axis
    @property
    def mate_left(self):
        return Mate(self, CoordSystem(
            origin=(0, -self.length / 2, 0),
            xDir=(1, 0, 0), normal=(0, -1, 0),
        ))

    @property
    def mate_right(self):
        return Mate(self, CoordSystem(
            origin=(0, self.length / 2, 0),
            xDir=(1, 0, 0), normal=(0, 1, 0),
        ))

    def get_cutout(self, clearance=0):
        return cadquery.Workplane('ZX', origin=(0, -self.length/2 - clearance, 0)) \
            .circle((self.diameter / 2) + clearance) \
            .extrude(self.length + (2 * clearance))

class Chassis(cqparts.Part):
    # Parameters
    width = PositiveFloat(50, doc="chassis width")

    _render = render_props(template='wood_light')

    def make(self):
        points = [  # chassis outline
            (-60,0),(-60,22),(-47,23),(-37,40),
            (5,40),(23,25),(60,22),(60,0),
        ]
        return cadquery.Workplane('XZ', origin=(0,self.width/2,0)) \
            .moveTo(*points[0]).polyline(points[1:]).close() \
            .extrude(self.width)

class WheeledAxle(cqparts.Assembly):
    left_width = PositiveFloat(7, doc="left wheel width")
    right_width = PositiveFloat(7, doc="right wheel width")
    left_diam = PositiveFloat(25, doc="left wheel diameter")
    right_diam = PositiveFloat(25, doc="right wheel diameter")
    axle_diam = PositiveFloat(8, doc="axel diameter")
    axle_track = PositiveFloat(50, doc="distance between wheel tread midlines")
    wheel_clearance = PositiveFloat(3, doc="distance between wheel and chassis")

    def make_components(self):
        axel_length = self.axle_track - (self.left_width + self.right_width) / 2
        return {
            'axle': Axle(length=axel_length, diameter=self.axle_diam),
            'left_wheel': Wheel(
                 width=self.left_width, diameter=self.left_diam,
            ),
            'right_wheel': Wheel(
                 width=self.right_width, diameter=self.right_diam,
            ),
        }

    def make_constraints(self):
        return [
            Fixed(self.components['axle'].mate_origin, CoordSystem()),
            Coincident(
                self.components['left_wheel'].mate_origin,
                self.components['axle'].mate_left
            ),
            Coincident(
                self.components['right_wheel'].mate_origin,
                self.components['axle'].mate_right
            ),
        ]

    def apply_cutout(self, part):
        # Cut wheel & axle from given part
        axle = self.components['axle']
        left_wheel = self.components['left_wheel']
        right_wheel = self.components['right_wheel']
        local_obj = part.local_obj
        local_obj = local_obj \
            .cut((axle.world_coords - part.world_coords) + axle.get_cutout()) \
            .cut((left_wheel.world_coords - part.world_coords) + left_wheel.get_cutout(self.wheel_clearance)) \
            .cut((right_wheel.world_coords - part.world_coords) + right_wheel.get_cutout(self.wheel_clearance))
        part.local_obj = local_obj

class Car(cqparts.Assembly):
    # Parameters
    wheelbase = PositiveFloat(70, "distance between front and rear axles")
    axle_track = PositiveFloat(60, "distance between tread midlines")
    # wheels
    wheel_width = PositiveFloat(10, doc="width of all wheels")
    front_wheel_diam = PositiveFloat(30, doc="front wheel diameter")
    rear_wheel_diam = PositiveFloat(30, doc="rear wheel diameter")
    axle_diam = PositiveFloat(10, doc="axle diameter")

    def make_components(self):
        return {
            'chassis': Chassis(width=self.axle_track),
            'front_axle': WheeledAxle(
                left_width=self.wheel_width,
                right_width=self.wheel_width,
                left_diam=self.front_wheel_diam,
                right_diam=self.front_wheel_diam,
                axle_diam=self.axle_diam,
                axle_track=self.axle_track,
            ),
            'rear_axle': WheeledAxle(
                left_width=self.wheel_width,
                right_width=self.wheel_width,
                left_diam=self.rear_wheel_diam,
                right_diam=self.rear_wheel_diam,
                axle_diam=self.axle_diam,
                axle_track=self.axle_track,
            ),
        }

    def make_constraints(self):
        return [
            Fixed(self.components['chassis'].mate_origin),
            Coincident(
                self.components['front_axle'].mate_origin,
                Mate(self.components['chassis'], CoordSystem((self.wheelbase/2,0,0))),
            ),
            Coincident(
                self.components['rear_axle'].mate_origin,
                Mate(self.components['chassis'], CoordSystem((-self.wheelbase/2,0,0))),
            ),
        ]

    def make_alterations(self):
        # cut out wheel wells
        chassis = self.components['chassis']
        self.components['front_axle'].apply_cutout(chassis)
        self.components['rear_axle'].apply_cutout(chassis)
        chassis.local_obj.chamfer(1)

car = Car()
car.axle_diam = 5
car.wheel_width = 9 
car.axle_track = 54

show_object(car)
