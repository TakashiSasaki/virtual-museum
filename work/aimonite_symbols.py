"""Colored emblems for the front of Aimonite's shell.

Use from a Blender model-building script after creating the shell::

    from aimonite_symbols import add_symbols
    add_symbols(patch, stroke, colors)

``patch(name, cx, cz, sx, sz, polygon, material)`` must project a polygon
onto the shell and draw its outline. ``stroke(name, points)`` must project
a polyline and render a thin dark line. ``colors`` follows the 12-material
order in refine_aimonite.py. Coordinates are in the character's X/Z front
plane, whose baseline shell centre is (.06, 1.46). ``center`` and ``scale``
map them to a resized or repositioned shell. This file does not alter the
scene or export files on import.
"""
import math


def add_symbols(patch, stroke, colors, center=(.06, 1.46), scale=1.0):
    if len(colors) < 12:
        raise ValueError('Expected the 12 Aimonite emblem materials')

    def tr(point):
        x, z = point
        return (center[0] + (x-.06)*scale, center[1] + (z-1.46)*scale)

    def shape(name, x, z, rx, rz, vertices, color):
        x, z = tr((x, z))
        patch(name, x, z, rx*scale, rz*scale, vertices, colors[color])

    def line(name, points):
        # Short segments follow the surface curvature instead of cutting
        # straight across the front of the rounded spiral.
        result = []
        for a, b in zip(points, points[1:]):
            count = max(1, math.ceil(math.dist(a, b) / .012))
            for i in range(count):
                t=i/count
                result.append(tr((a[0]*(1-t)+b[0]*t, a[1]*(1-t)+b[1]*t)))
        result.append(tr(points[-1]))
        stroke(name, result)

    def ellipse(cx, cz, rx, rz, start=0, end=2*math.pi, count=48):
        return [(cx+rx*math.cos(start+(end-start)*i/count),
                 cz+rz*math.sin(start+(end-start)*i/count)) for i in range(count+1)]

    disk=[(math.cos(math.tau*i/40),math.sin(math.tau*i/40)) for i in range(40)]
    # The colors and profiles follow the provided four-view illustration;
    # they are symbolic artwork, rather than scientific specimen diagrams.
    artifact=[(-.78,.72),(-.56,1),(.39,1),(.76,.82),(.68,.48),(.28,.42),
              (.10,.14),(.13,-.08),(.34,-.28),(.75,-.42),(.63,-.95),
              (-.53,-1),(-.8,-.78),(-.67,-.40),(-.42,-.18),(-.40,.12),(-.75,.25)]
    plant=[(-.12,-1),(-.01,-.63),(.10,-.35),(.21,.08),(.42,.74),(.48,.40),
           (.70,.93),(.65,.52),(.92,1),(.76,.49),(.90,.67),(.68,.10),
           (.44,-.25),(.17,-.65),(.07,-1)]
    fossil=[(-.87,-.73),(-.88,-.30),(-.62,-.10),(-.75,.14),(-.60,.30),
            (-.42,.28),(-.48,.60),(-.31,.80),(-.08,.71),(.10,.53),
            (.20,.78),(.37,.78),(.39,.51),(.60,.58),(.71,.36),(.57,.15),
            (.88,.22),(.93,-.02),(.68,-.22),(.93,-.40),(.85,-.68),
            (.54,-.55),(.41,-.90),(.15,-.77),(-.15,-.87),(-.46,-.73)]
    map_shape=[(-.45,-1),(-.19,-.45),(-.54,-.18),(-.45,.17),(-.61,.46),
               (-.51,.93),(-.25,.82),(-.05,.63),(.13,.82),(.52,1),
               (.66,.90),(.33,.50),(.13,.37),(.23,.12),(.00,-.08),
               (.16,-.40),(.28,-.67),(.13,-.87),(-.08,-.58)]
    wave=[(-1,-.24),(-.85,-.10),(-.68,.04),(-.55,.39),(-.33,.74),(-.05,.89),
          (.19,.83),(.34,.60),(.24,.50),(.04,.68),(-.12,.50),(-.18,.22),
          (-.08,.02),(.14,-.03),(.36,.08),(.46,.23),(.59,.23),(.57,-.01),
          (.72,-.10),(1,.03),(.84,-.39),(.64,-.50),(.34,-.51),(.04,-.43),
          (-.25,-.55),(-.63,-.51),(-.92,-.48)]
    person=[(-.25,.40),(-.36,.57),(-.32,.82),(-.13,.98),(.12,.98),(.33,.82),
            (.36,.58),(.25,.40),(.40,.18),(.73,-.12),(.66,-.28),(.37,-.14),
            (.28,-.06),(.33,-.53),(.23,-.94),(.07,-.96),(0,-.49),
            (-.10,-.94),(-.26,-.94),(-.34,-.51),(-.29,-.03),(-.56,-.32),
            (-.72,-.25),(-.47,.17)]
    stone=[(-.82,-.62),(-.94,-.18),(-.72,.19),(-.76,.63),(-.48,.84),
           (-.02,.72),(.38,.82),(.55,.55),(.88,.48),(.78,.12),
           (.94,-.19),(.77,-.52),(.48,-.55),(.32,-.90),(-.01,-.82),(-.42,-.89)]
    fossil_brown=[(-.86,-.58),(-.56,-.35),(-.65,-.08),(-.70,.27),(-.47,.67),
                  (-.13,.91),(.26,.86),(.59,.61),(.73,.23),(.66,-.17),
                  (.38,-.60),(.05,-.83),(-.27,-.88),(-.54,-.77)]

    shape('Insect emblem',-.18,1.99,.125,.13,disk,0)
    shape('Artifact emblem',.23,2.01,.12,.14,artifact,1)
    shape('Plant emblem',.49,1.84,.10,.19,plant,2)
    shape('Fossil emblem',.62,1.52,.13,.12,fossil,3)
    shape('Pink people',.41,1.19,.084,.14,person,4)
    shape('Blue people',.57,1.23,.084,.14,person,5)
    shape('Joined hands',.49,1.205,.025,.018,[(-1,0),(0,.6),(1,0),(0,-.6)],4)
    shape('Stone emblem',.25,.99,.13,.12,stone,6)
    shape('Brown fossil',.04,1.13,.13,.12,fossil_brown,7)
    shape('Red mineral',.32,1.52,.115,.115,disk,8)
    shape('Planet',-.14,1.58,.13,.13,disk,9)
    shape('Wave',-.38,1.30,.18,.12,wave,10)
    shape('Map',-.50,1.72,.12,.20,map_shape,11)

    # Fine drawing within the green insect and red specimen disks.
    line('Insect transverse marking',[(-.296,2.025),(-.19,2.035),(-.070,2.06)])
    line('Insect central vein',[(-.19,2.035),(-.17,2.005),(-.15,1.88)])
    for name,points in [
        ('Insect antenna L',[(-.294,2.03),(-.32,2.038)]),
        ('Insect antenna R',[(-.058,2.07),(-.035,2.08)]),
        ('Insect leg L1',[(-.28,1.98),(-.31,1.96)]),
        ('Insect leg L2',[(-.27,1.94),(-.29,1.91)]),
        ('Insect leg R1',[(-.06,1.99),(-.04,1.98)]),
        ('Insect leg R2',[(-.07,1.95),(-.05,1.93)])]: line(name,points)

    line('Mineral outer cut',[(.255,1.47),(.267,1.52),(.29,1.56),(.34,1.60),
                              (.38,1.53),(.38,1.46),(.33,1.45),(.255,1.47)])
    line('Mineral inner cut',[(.277,1.47),(.29,1.51),(.32,1.54),(.35,1.52),
                              (.36,1.47),(.33,1.46),(.277,1.47)])
    line('Mineral facet',[(.34,1.60),(.32,1.54)])

    # Saturn's thin ring and little satellite. Subdivide so that a line
    # remains close to the shell instead of becoming a hovering chord.
    line('Planet ring',ellipse(-.14,1.58,.18,.075,-.8,2.34,48))
    line('Planet ring',ellipse(-.14,1.58,.18,.075,2.40,5.44,48))
    shape('Planet moon',.012,1.66,.028,.028,disk,9)

    # Three shallow water lines below the wave.
    line('Water line 1',[(-.55,1.20),(-.48,1.18),(-.41,1.18),(-.34,1.20),(-.27,1.18),(-.21,1.18)])
    line('Water line 2',[(-.50,1.15),(-.43,1.13),(-.36,1.14),(-.30,1.15),(-.25,1.13)])
    line('Water line 3',[(-.43,1.10),(-.38,1.11),(-.33,1.10)])
