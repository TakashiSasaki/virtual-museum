using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

/// <summary>Depth-tested signs that share the experience's actual interaction state.</summary>
[DefaultExecutionOrder(100)]
public sealed class MuseumWayfinding : MonoBehaviour
{
    public enum Kind { Specimen, Microscope, Guide }

    [Serializable]
    public sealed class Landmark
    {
        public Transform anchor;
        public Component target;
        public Kind kind;
        public string title;
        public float badgeHeight = 1.8f;
    }

    public MuseumExperience experience;
    public Material beaconMaterial;
    public Shader letteringShader;
    public Landmark[] landmarks = Array.Empty<Landmark>();
    [Range(4, 16)] public float badgeViewDistance = 10;

    sealed class View
    {
        public Landmark landmark;
        public GameObject root;
        public Transform badge;
        public MeshRenderer floorRenderer, badgeRenderer;
        public TextMesh title, action;
        public Color accent;
        public float focus;
        public bool ready, experienced, touch;
    }

    static readonly int Tint = Shader.PropertyToID("_Color");
    static readonly int Opacity = Shader.PropertyToID("_Opacity");
    readonly List<View> views = new();
    readonly Dictionary<Kind, Mesh> floors = new(), badges = new();
    readonly Dictionary<Kind, Mesh> experiencedFloors = new(), experiencedBadges = new();
    MaterialPropertyBlock properties;
    Material textMaterial;
    Font font;
    bool visible;

    public static Color Accent(Kind kind) => kind switch
    {
        Kind.Microscope => new Color(.24f, .95f, .88f),
        Kind.Guide => new Color(.75f, .65f, 1f),
        _ => new Color(1f, .74f, .35f)
    };

    void Start()
    {
        if (!experience || !beaconMaterial || !letteringShader) { enabled = false; return; }
        properties = new MaterialPropertyBlock();
        font = experience.japaneseFont;
        if (!font) { enabled = false; return; }
        textMaterial = new Material(letteringShader) { name = "Wayfinding lettering (runtime)", mainTexture = font.material.mainTexture };
        Font.textureRebuilt += RefreshFont;
        foreach (var landmark in landmarks)
        {
            if (landmark == null || !landmark.anchor || !landmark.target) continue;
            var accent = Accent(landmark.kind);
            if (!floors.ContainsKey(landmark.kind))
            {
                floors.Add(landmark.kind, MuseumBeaconGeometry.CreateFloor(accent));
                badges.Add(landmark.kind, MuseumBeaconGeometry.CreateBadge((int)landmark.kind, accent));
            }
            var root = new GameObject("Signal (runtime)") { layer = 2 };
            root.transform.SetParent(landmark.anchor, false);
            var floor = MeshObject("Approach halo", root.transform, floors[landmark.kind]);
            var badge = MeshObject("Interaction sign", root.transform, badges[landmark.kind]);
            Vector3 toward = landmark.target.transform.position - landmark.anchor.position;
            toward.y = 0;
            if (toward.sqrMagnitude > .001f && landmark.kind != Kind.Guide)
            {
                floor.transform.localRotation = Quaternion.LookRotation(toward.normalized);
                badge.transform.localPosition = toward.normalized * .18f;
            }
            badge.transform.localPosition += Vector3.up * landmark.badgeHeight;
            var title = Text("Title", badge.transform, landmark.title, -.13f, 64, landmark.kind == Kind.Guide ? .0175f : .022f);
            var action = Text("Action", badge.transform, IdleAction(landmark.kind), -.255f, 44, .0195f);
            action.color = accent;
            views.Add(new View { landmark = landmark, root = root, badge = badge.transform, floorRenderer = floor,
                badgeRenderer = badge, title = title, action = action, accent = accent });
        }
        RefreshFont(font);
    }

    MeshRenderer MeshObject(string label, Transform parent, Mesh mesh)
    {
        var go = new GameObject(label) { layer = 2 };
        go.transform.SetParent(parent, false);
        go.AddComponent<MeshFilter>().sharedMesh = mesh;
        var renderer = go.AddComponent<MeshRenderer>();
        renderer.sharedMaterial = beaconMaterial;
        renderer.shadowCastingMode = ShadowCastingMode.Off;
        renderer.receiveShadows = false;
        renderer.lightProbeUsage = LightProbeUsage.Off;
        renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
        return renderer;
    }

    TextMesh Text(string label, Transform parent, string value, float y, int size, float characterSize)
    {
        var go = new GameObject(label) { layer = 2 };
        go.transform.SetParent(parent, false);
        go.transform.localPosition = new Vector3(0, y, -.018f);
        var text = go.AddComponent<TextMesh>();
        text.font = font;
        text.text = value;
        text.fontSize = size;
        text.characterSize = characterSize;
        text.anchor = TextAnchor.MiddleCenter;
        text.alignment = TextAlignment.Center;
        text.color = new Color(.95f, 1f, .99f);
        var renderer = go.GetComponent<MeshRenderer>();
        renderer.sharedMaterial = textMaterial;
        renderer.shadowCastingMode = ShadowCastingMode.Off;
        renderer.receiveShadows = false;
        renderer.lightProbeUsage = LightProbeUsage.Off;
        renderer.reflectionProbeUsage = ReflectionProbeUsage.Off;
        return text;
    }

    static string IdleAction(Kind kind) => kind switch
    {
        Kind.Microscope => "クリックでのぞく",
        Kind.Guide => "クリックで解説",
        _ => "クリックで手に取る"
    };

    void UpdateExperienceVisual(View view, bool experienced)
    {
        var kind = view.landmark.kind;
        if (experienced && !experiencedFloors.ContainsKey(kind))
        {
            experiencedFloors.Add(kind, MuseumBeaconGeometry.CreateFloor(view.accent, true));
            experiencedBadges.Add(kind, MuseumBeaconGeometry.CreateBadge((int)kind, view.accent, true));
        }
        view.floorRenderer.GetComponent<MeshFilter>().sharedMesh = experienced ? experiencedFloors[kind] : floors[kind];
        view.badgeRenderer.GetComponent<MeshFilter>().sharedMesh = experienced ? experiencedBadges[kind] : badges[kind];
        view.experienced = experienced;
    }

    void LateUpdate()
    {
        visible = experience && experience.WayfindingVisible;
        if (!experience || !experience.visitorCamera) return;
        var camera = experience.visitorCamera.transform;
        Component ready = experience.ReadyInteraction;
        float time = Time.unscaledTime;
        foreach (var view in views)
        {
            if (!view.root) continue;
            if (!view.landmark.target || !view.landmark.anchor) { view.root.SetActive(false); continue; }
            if (view.root.activeSelf != visible) view.root.SetActive(visible);
            if (!visible) continue;
            if (view.landmark.kind == Kind.Guide)
            {
                Vector3 position = view.landmark.target.transform.position;
                position.y = .045f;
                view.landmark.anchor.position = position;
            }
            bool focused = ready == view.landmark.target;
            bool experienced = experience.HasExperienced(view.landmark.target);
            bool experienceChanged = view.experienced != experienced;
            if (experienceChanged) UpdateExperienceVisual(view, experienced);
            bool touch = experience.UsesTouchControls;
            if (view.ready != focused || experienceChanged || view.touch != touch)
            {
                view.ready = focused;view.touch = touch;
                view.action.text = touch ? (experienced ? "体験済み・もう一度" : IdleAction(view.landmark.kind).Replace("クリック", "タップ")) :
                    experienced ? (focused ? "体験済み・Eで観察" : "体験済み・もう一度") :
                    focused ? (view.landmark.kind == Kind.Microscope ? "E でのぞく" : "E で手に取る") : IdleAction(view.landmark.kind);
            }
            view.focus = Mathf.MoveTowards(view.focus, focused ? 1 : 0, Time.unscaledDeltaTime * 5);
            float pulse = .5f + .5f * Mathf.Sin(time * 1.5f);
            properties.Clear();
            properties.SetColor(Tint, Color.Lerp(Color.white, new Color(1.18f, 1.18f, 1.18f), view.focus));
            properties.SetFloat(Opacity, experienced ? .67f + .30f * view.focus : .58f + .09f * pulse + .30f * view.focus);
            view.floorRenderer.SetPropertyBlock(properties);
            properties.SetColor(Tint, Color.white);
            properties.SetFloat(Opacity, .87f + .13f * view.focus);
            view.badgeRenderer.SetPropertyBlock(properties);
            view.action.color = Color.Lerp(view.accent, Color.white, view.focus);

            Vector3 direction = view.badge.position - camera.position;
            float horizontalDistance = new Vector2(direction.x, direction.z).magnitude;
            bool inRange = direction.sqrMagnitude <= badgeViewDistance * badgeViewDistance && horizontalDistance > .27f;
            if (view.badge.gameObject.activeSelf != inRange) view.badge.gameObject.SetActive(inRange);
            // Cap its apparent size near an approach point: the sign must not
            // cover the specimen when the visitor uses a movement shortcut.
            view.badge.localScale = Vector3.one * Mathf.Min(1, horizontalDistance / 2.4f);
            // Upright signs remain readable while walking; no spinning or large bobbing.
            direction.y = 0;
            if (direction.sqrMagnitude > .0001f) view.badge.rotation = Quaternion.LookRotation(direction, Vector3.up);
        }
    }

    // Decorative geometry has no colliders. A sign can still be clicked by
    // intersecting its visible plane, without blocking floor or object raycasts.
    public bool TryActivate(Ray ray)
    {
        if (!visible || !experience || !experience.WayfindingVisible) return false;
        View candidate = null;
        float closest = float.PositiveInfinity;
        foreach (var view in views)
        {
            if (!view.badge || !view.badge.gameObject.activeInHierarchy || !view.landmark.target) continue;
            var plane = new Plane(-view.badge.forward, view.badge.position);
            if (!plane.Raycast(ray, out float distance) || distance <= 0 || distance >= closest) continue;
            Vector3 point = view.badge.InverseTransformPoint(ray.GetPoint(distance));
            bool onPanel = Mathf.Abs(point.x) <= .49f && point.y >= -.32f && point.y <= -.055f;
            bool onIcon = new Vector2(point.x, point.y - .16f).sqrMagnitude <= .19f * .19f;
            if (!onPanel && !onIcon) continue;
            if (Physics.Raycast(ray, out var hit, distance, ~0, QueryTriggerInteraction.Ignore) &&
                !hit.collider.transform.IsChildOf(view.landmark.target.transform)) continue;
            closest = distance; candidate = view;
        }
        if (candidate == null) return false;
        if (candidate.landmark.target is MuseumExhibit exhibit) experience.Observe(exhibit.index);
        else if (candidate.landmark.target is MicroscopeStation station) experience.Microscope(station);
        else if (candidate.landmark.target is GuideMarker) experience.Talk();
        else return false;
        return true;
    }

    void RefreshFont(Font rebuilt)
    {
        if (rebuilt == font && textMaterial) textMaterial.mainTexture = font.material.mainTexture;
    }

    void OnDisable()
    {
        visible = false;
        foreach (var view in views) if (view.root) view.root.SetActive(false);
    }

    void OnDestroy()
    {
        Font.textureRebuilt -= RefreshFont;
        foreach (var view in views) if (view.root) Destroy(view.root);
        foreach (var mesh in floors.Values) if (mesh) Destroy(mesh);
        foreach (var mesh in badges.Values) if (mesh) Destroy(mesh);
        foreach (var mesh in experiencedFloors.Values) if (mesh) Destroy(mesh);
        foreach (var mesh in experiencedBadges.Values) if (mesh) Destroy(mesh);
        if (textMaterial) Destroy(textMaterial);
    }
}
