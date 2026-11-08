"""Shape an insect thorax and attach appendages in the generators' local axes.

Each section is (anterior Y, posterior Y, half-width, ventral Z, dorsal Z).
Sections meet at shallow sutures. Coxae are placed on the actual ventrolateral
surface of their own section, independently of dorsal shields or wing covers.
"""
import math

from mathutils import Vector


SEGMENTS = ('T1 prothorax', 'T2 mesothorax', 'T3 metathorax')


class Thorax:
    def __init__(self, mesh, ellipsoid, sections, material):
        self.ellipsoid = ellipsoid
        self.sections = tuple(sections)
        if len(self.sections) != len(SEGMENTS):
            raise ValueError('An insect thorax has three sections')
        front, rear = self.sections[0][:2]
        self.front_sign = 1 if front > rear else -1
        self.rings = []

        for index, (front, rear, width, bottom, top) in enumerate(self.sections):
            if self.front_sign * (front - rear) <= 0 or width <= 0 or top <= bottom:
                raise ValueError(f'Invalid profile for {SEGMENTS[index]}')
            if index and not math.isclose(front, self.sections[index - 1][1], abs_tol=1e-8):
                raise ValueError('Thoracic sections must meet along their boundary')
            middle = (width, bottom, top)
            leading = self._boundary(index - 1, index) if index else (width * .67, bottom, top)
            trailing = self._boundary(index, index + 1) if index < 2 else (width * .81, bottom, top)
            rings = [(0, leading), (.15, middle), (.5, middle), (.85, middle), (1, trailing)]
            self.rings.append(rings)
            vertices = [tuple(self.surface(index, fraction, step * math.tau / 16))
                        for fraction, _ in rings for step in range(16)]
            faces = []
            for row in range(len(rings) - 1):
                for step in range(16):
                    next_step = (step + 1) % 16
                    faces.append((row * 16 + step, row * 16 + next_step,
                                  (row + 1) * 16 + next_step, (row + 1) * 16 + step))
            faces.extend([tuple(reversed(range(16))), tuple(range(len(vertices) - 16, len(vertices)))])
            if self.front_sign < 0:
                faces = [face[::-1] for face in faces]
            section = mesh(SEGMENTS[index], vertices, faces, material)
            for polygon in section.data.polygons:
                polygon.use_smooth = len(polygon.vertices) == 4
            section['thoracic_segment'] = index + 1

    def _boundary(self, first, second):
        a, b = self.sections[first][2:], self.sections[second][2:]
        width, bottom, top = ((x + y) / 2 for x, y in zip(a, b))
        inset = (top - bottom) * .035
        return width * .91, bottom + inset, top - inset

    def surface(self, segment, fraction, angle, side=1):
        rings = self.rings[segment]
        if not 0 <= fraction <= 1:
            raise ValueError('Appendage falls outside its thoracic section')
        for (t0, a), (t1, b) in zip(rings, rings[1:]):
            if fraction <= t1:
                blend = (fraction - t0) / (t1 - t0)
                width, bottom, top = (x + (y - x) * blend for x, y in zip(a, b))
                break
        front, rear = self.sections[segment][:2]
        return Vector((side * width * math.cos(angle), front + (rear - front) * fraction,
                       (top + bottom + (top - bottom) * math.sin(angle)) / 2))

    def coxa(self, segment, side, radius, material, fraction=.5, angle=-.82):
        """Return the start of the distal leg, slightly outside the coxal joint."""
        center = self.surface(segment, fraction, angle, side)
        socket = self.ellipsoid(f'{SEGMENTS[segment]} coxa {side:+d}', center,
                                (radius * 1.25, radius * 1.1, radius * .9), material, 10, 6)
        socket['leg_segment'] = segment + 1
        socket['leg_side'] = side
        return center + Vector((side * radius * .62, 0, -radius * .31))
