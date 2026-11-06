using System.Collections.Generic;
using UnityEngine;

/// <summary>Compact, unlit meshes for the museum's in-world interaction signs.</summary>
public static class MuseumBeaconGeometry
{
    public static Mesh CreateFloor(Color accent, bool experienced = false)
    {
        var b = new Builder(true);
        // The centre remains almost clear so the floor material is still readable.
        b.Disc(Vector2.zero, .333f, Alpha(accent, .035f), 48);
        b.Arc(Vector2.zero, .332f, .004f, 0, 360, Alpha(accent, .33f));
        if (experienced)
        {
            // A closed, calmer outline marks a completed visit without removing the sign.
            b.GlowArc(Vector2.zero, .400f, .007f, 0, 360, Alpha(accent, .82f));
            b.Arc(Vector2.zero, .451f, .003f, 0, 360, Alpha(accent, .22f));
            var check = new[] { new Vector2(-.075f, -.005f), new Vector2(-.025f, -.055f), new Vector2(.075f, .075f) };
            b.Path(check, .043f, Alpha(accent, .17f));
            b.Path(check, .022f, new Color(.91f, 1f, .985f, .96f));
        }
        else
        {
            for (int i = 0; i < 4; i++)
            {
                float start = 13 + i * 90;
                b.GlowArc(Vector2.zero, .400f, .011f, start, start + 64, accent);
                b.Arc(Vector2.zero, .451f, .003f, start + 9, start + 55, Alpha(accent, .28f));
            }
        }
        for (int i = 0; i < 8; i++)
        {
            float angle = (i * 45) * Mathf.Deg2Rad;
            var direction = new Vector2(Mathf.Cos(angle), Mathf.Sin(angle));
            b.Line(direction * .421f, direction * .454f, .005f, Alpha(accent, .65f));
        }
        // A two-step arrow indicates the object, not an automatic activation zone.
        b.Path(new[] { new Vector2(-.092f, .509f), new Vector2(0, .564f), new Vector2(.092f, .509f) }, .012f, Alpha(accent, .83f));
        b.Path(new[] { new Vector2(-.067f, .610f), new Vector2(0, .651f), new Vector2(.067f, .610f) }, .009f, Alpha(accent, .46f));
        return b.Finish(experienced ? "Interaction floor / experienced closed halo" : "Interaction floor / segmented halo");
    }

    public static Mesh CreateBadge(int kind, Color accent, bool experienced = false)
    {
        var b = new Builder(false);
        Color ink = new Color(.022f, .055f, .068f, .94f);
        Color white = new Color(.91f, 1f, .985f, 1f);
        var centre = new Vector2(0, .16f);

        // A small cut-corner panel gives the two text lines contrast against white walls.
        var panel = new[] {
            new Vector2(-.452f, -.055f), new Vector2(.452f, -.055f),
            new Vector2(.490f, -.093f), new Vector2(.490f, -.282f),
            new Vector2(.452f, -.320f), new Vector2(-.452f, -.320f),
            new Vector2(-.490f, -.282f), new Vector2(-.490f, -.093f)
        };
        b.Polygon(panel, ink);
        b.ClosedPath(panel, .0035f, Alpha(accent, .38f));
        b.Line(new Vector2(-.420f, -.057f), new Vector2(-.240f, -.057f), .007f, accent);
        b.Line(new Vector2(.240f, -.318f), new Vector2(.420f, -.318f), .004f, Alpha(accent, .7f));

        var hex = RegularPolygon(centre, .184f, 6, 30);
        b.Polygon(hex, ink);
        b.ClosedPath(hex, .018f, Alpha(accent, .11f));
        b.ClosedPath(hex, .005f, Alpha(accent, .92f));
        b.Arc(centre, .206f, .003f, 24, 88, Alpha(accent, .38f));
        b.Arc(centre, .206f, .003f, 204, 268, Alpha(accent, .38f));
        b.Line(new Vector2(0, -.024f), new Vector2(0, -.052f), .004f, Alpha(accent, .48f));
        b.Line(new Vector2(0, -.332f), new Vector2(0, -.480f), .003f, Alpha(accent, .35f));
        b.Disc(new Vector2(0, -.495f), .007f, Alpha(accent, .8f), 12);

        if (kind == 1) Microscope(b, centre, white, accent);
        else if (kind == 2) Conversation(b, centre, white, accent);
        else Specimen(b, centre, white, accent);
        if (experienced)
        {
            // The seal stays inside the original icon's clickable circle and clear of labels.
            var seal = new Vector2(.110f, .085f);
            b.Arc(seal, .045f, .008f, 0, 360, Alpha(accent, .14f));
            b.Disc(seal, .043f, new Color(.022f, .055f, .068f, 1f), 24);
            b.Arc(seal, .044f, .003f, 0, 360, accent);
            b.Path(Offset(seal, new[] {
                new Vector2(-.023f, -.001f), new Vector2(-.007f, -.017f), new Vector2(.023f, .019f)
            }), .008f, white);
        }
        return b.Finish("Interaction badge / " + (kind == 1 ? "microscope" : kind == 2 ? "conversation" : "specimen") + (experienced ? " / experienced" : ""));
    }

    static void Microscope(Builder b, Vector2 c, Color white, Color accent)
    {
        // Sloping optical tube, arm, focus knob, sample stage and broad base.
        b.Path(Offset(c, new[] {
            new Vector2(-.085f, -.105f), new Vector2(.094f, -.105f),
            new Vector2(.076f, -.078f), new Vector2(-.069f, -.078f)
        }), .009f, white);
        b.Path(Offset(c, new[] {
            new Vector2(.040f, -.078f), new Vector2(.070f, -.028f),
            new Vector2(.070f, .023f), new Vector2(.033f, .064f)
        }), .010f, white);
        b.Line(c + new Vector2(-.081f, -.033f), c + new Vector2(.033f, -.033f), .009f, white);
        var tube = Offset(c, new[] {
            new Vector2(-.072f, .085f), new Vector2(-.044f, .108f),
            new Vector2(.019f, .028f), new Vector2(-.009f, .006f)
        });
        b.ClosedPath(tube, .008f, white);
        b.Line(c + new Vector2(-.082f, .090f), c + new Vector2(-.043f, .122f), .010f, accent);
        b.Line(c + new Vector2(-.002f, -.001f), c + new Vector2(.013f, -.021f), .010f, white);
        b.Disc(c + new Vector2(.066f, .031f), .017f, accent, 16);
        b.Disc(c + new Vector2(.066f, .031f), .006f, new Color(.022f, .055f, .068f, 1), 12);
        b.Line(c + new Vector2(-.057f, -.019f), c + new Vector2(-.025f, -.019f), .005f, accent);
    }

    static void Specimen(Builder b, Vector2 c, Color white, Color accent)
    {
        var top = c + new Vector2(0, .100f);
        var left = c + new Vector2(-.079f, .052f);
        var right = c + new Vector2(.079f, .052f);
        var middle = c + new Vector2(0, .004f);
        var bottom = c + new Vector2(0, -.090f);
        b.ClosedPath(new[] { top, right, c + new Vector2(.079f, -.041f), bottom,
            c + new Vector2(-.079f, -.041f), left }, .007f, white);
        b.Path(new[] { left, middle, right }, .006f, white);
        b.Line(middle, bottom, .006f, white);
        b.Arc(c, .126f, .005f, 192, 278, Alpha(accent, .9f));
        b.Arc(c, .126f, .005f, 12, 98, Alpha(accent, .9f));
        b.Path(Offset(c, new[] { new Vector2(.020f, .143f), new Vector2(-.018f, .125f), new Vector2(.012f, .105f) }), .006f, accent);
        b.Path(Offset(c, new[] { new Vector2(-.020f, -.143f), new Vector2(.018f, -.125f), new Vector2(-.012f, -.105f) }), .006f, accent);
    }

    static void Conversation(Builder b, Vector2 c, Color white, Color accent)
    {
        var outline = Offset(c, new[] {
            new Vector2(-.088f, .087f), new Vector2(.070f, .087f),
            new Vector2(.097f, .060f), new Vector2(.097f, -.028f),
            new Vector2(.070f, -.055f), new Vector2(-.013f, -.055f),
            new Vector2(-.058f, -.101f), new Vector2(-.058f, -.055f),
            new Vector2(-.088f, -.055f), new Vector2(-.108f, -.035f),
            new Vector2(-.108f, .067f)
        });
        b.ClosedPath(outline, .008f, white);
        for (int i = -1; i <= 1; i++) b.Disc(c + new Vector2(i * .044f - .005f, .018f), .011f, accent, 12);
    }

    static Color Alpha(Color color, float alpha) { color.a *= alpha; return color; }
    static Vector2[] Offset(Vector2 centre, Vector2[] points)
    {
        for (int i = 0; i < points.Length; i++) points[i] += centre;
        return points;
    }
    static Vector2[] RegularPolygon(Vector2 centre, float radius, int count, float degrees)
    {
        var points = new Vector2[count];
        for (int i = 0; i < count; i++)
        {
            float angle = (degrees + i * 360f / count) * Mathf.Deg2Rad;
            points[i] = centre + new Vector2(Mathf.Cos(angle), Mathf.Sin(angle)) * radius;
        }
        return points;
    }

    sealed class Builder
    {
        readonly bool floor;
        readonly List<Vector3> vertices = new List<Vector3>(1800);
        readonly List<Color> colors = new List<Color>(1800);
        readonly List<int> triangles = new List<int>(3600);
        public Builder(bool floor) { this.floor = floor; }
        int Vertex(Vector2 p, Color color)
        {
            vertices.Add(floor ? new Vector3(p.x, 0, p.y) : new Vector3(p.x, p.y, 0));
            colors.Add(color); return vertices.Count - 1;
        }
        void Triangle(int a, int b, int c)
        { triangles.Add(a); triangles.Add(c); triangles.Add(b); }
        void Quad(Vector2 a, Vector2 b, Vector2 c, Vector2 d, Color inner, Color outer)
        {
            int first = Vertex(a, inner); Vertex(b, inner); Vertex(c, outer); Vertex(d, outer);
            Triangle(first, first + 1, first + 2); Triangle(first, first + 2, first + 3);
        }
        public void Line(Vector2 a, Vector2 b, float width, Color color)
        {
            Vector2 direction = b - a;
            if (direction.sqrMagnitude < .0000001f) return;
            Vector2 normal = new Vector2(-direction.y, direction.x).normalized * (width * .5f);
            Quad(a - normal, b - normal, b + normal, a + normal, color, color);
        }
        public void Path(Vector2[] points, float width, Color color)
        {
            for (int i = 0; i < points.Length - 1; i++) Line(points[i], points[i + 1], width, color);
        }
        public void ClosedPath(Vector2[] points, float width, Color color)
        {
            Path(points, width, color);
            Line(points[points.Length - 1], points[0], width, color);
        }
        public void Polygon(Vector2[] points, Color color)
        {
            Vector2 centre = Vector2.zero;
            foreach (var point in points) centre += point;
            centre /= points.Length;
            int middle = Vertex(centre, color);
            int start = vertices.Count;
            foreach (var point in points) Vertex(point, color);
            for (int i = 0; i < points.Length; i++) Triangle(middle, start + i, start + (i + 1) % points.Length);
        }
        public void Disc(Vector2 centre, float radius, Color color, int segments)
        { Polygon(RegularPolygon(centre, radius, segments, 0), color); }
        public void Arc(Vector2 centre, float radius, float width, float from, float to, Color color)
        { Band(centre, radius - width * .5f, radius + width * .5f, from, to, color, color); }
        public void GlowArc(Vector2 centre, float radius, float width, float from, float to, Color color)
        {
            float glowWidth = width * 2.8f;
            Band(centre, radius - glowWidth, radius - width * .5f, from, to, Alpha(color, 0), Alpha(color, .27f));
            Band(centre, radius + width * .5f, radius + glowWidth, from, to, Alpha(color, .27f), Alpha(color, 0));
            Arc(centre, radius, width, from, to, color);
        }
        void Band(Vector2 centre, float innerRadius, float outerRadius, float from, float to, Color inner, Color outer)
        {
            int segments = Mathf.Max(1, Mathf.CeilToInt(Mathf.Abs(to - from) / 5f));
            for (int i = 0; i < segments; i++)
            {
                float a = Mathf.Lerp(from, to, i / (float)segments) * Mathf.Deg2Rad;
                float z = Mathf.Lerp(from, to, (i + 1) / (float)segments) * Mathf.Deg2Rad;
                var d0 = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                var d1 = new Vector2(Mathf.Cos(z), Mathf.Sin(z));
                Quad(centre + d0 * innerRadius, centre + d1 * innerRadius,
                    centre + d1 * outerRadius, centre + d0 * outerRadius, inner, outer);
            }
        }
        public Mesh Finish(string name)
        {
            var mesh = new Mesh { name = name };
            mesh.SetVertices(vertices); mesh.SetColors(colors); mesh.SetTriangles(triangles, 0);
            mesh.RecalculateNormals(); mesh.RecalculateBounds();
            return mesh;
        }
    }
}
