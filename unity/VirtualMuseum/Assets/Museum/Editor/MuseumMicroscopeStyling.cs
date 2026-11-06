using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

/// <summary>Applies the Blender microscope palette only to saved scene microscopes.</summary>
public static class MuseumMicroscopeStyling
{
    const string ScenePath = "Assets/Museum/Scenes/MuseumV1.unity";
    const string MaterialFolder = "Assets/Museum/Materials/Microscope";

    readonly struct Finish
    {
        public readonly string Label;
        public readonly Color Color;
        public readonly float Roughness;
        public readonly float Metallic;
        public Finish(string label, float r, float g, float b, float roughness, float metallic = 0f)
        {
            Label = label;
            Color = new Color(r, g, b, 1f);
            Roughness = roughness;
            Metallic = metallic;
        }
    }

    // Keep these values in step with work/refine_microscope.py.
    static readonly Finish[] Finishes =
    {
        new Finish("Warm white enamel", .81f, .83f, .80f, .29f),
        new Finish("Optical housing", .67f, .71f, .69f, .35f),
        new Finish("Eyecup rubber", .018f, .021f, .023f, .71f),
        new Finish("Black anodized aluminium", .027f, .035f, .040f, .30f, .65f),
        new Finish("Brushed steel", .43f, .48f, .50f, .26f, .82f),
        new Finish("Stage ceramic", .91f, .92f, .88f, .23f),
        new Finish("Coated optical glass", .018f, .055f, .065f, .12f, .52f),
        new Finish("LED diffuser", .80f, .88f, .88f, .20f),
        new Finish("Scale markings", .64f, .69f, .68f, .49f),
        new Finish("Camera status light", .045f, .38f, .13f, .28f)
    };

    [MenuItem("Museum/Apply Microscope Materials")]
    public static void Apply()
    {
        var scene = SceneManager.GetActiveScene();
        if (EditorApplication.isPlayingOrWillChangePlaymode)
            throw new InvalidOperationException("Stop Play mode before applying microscope materials.");
        if (scene.path != ScenePath || scene.isDirty)
            throw new InvalidOperationException("Open the saved MuseumV1 scene with no unsaved changes first.");
        var shader = Shader.Find("Standard");
        if (!shader || !shader.isSupported)
            throw new InvalidOperationException("The Standard shader is missing or unsupported.");

        // Resolve the entire assignment first, before creating assets or editing
        // renderers. Unknown slots indicate an old or unexpectedly changed model.
        var assignments = new Dictionary<Renderer, int[]>();
        int stationCount = 0;
        foreach (var root in scene.GetRootGameObjects())
        foreach (var station in root.GetComponentsInChildren<MicroscopeStation>(true))
        {
            stationCount++;
            foreach (var renderer in station.GetComponentsInChildren<MeshRenderer>(true))
            {
                var slots = renderer.sharedMaterials;
                if (slots.Length == 0)
                    throw new InvalidOperationException("Microscope renderer has no material: " + renderer.name);
                var indices = new int[slots.Length];
                for (int i = 0; i < slots.Length; i++)
                {
                    indices[i] = FindFinish(slots[i] ? slots[i].name : "");
                    // FBX importers may sanitize material names. The combined
                    // mesh also carries its single material's descriptive name.
                    if (indices[i] < 0 && slots.Length == 1)
                        indices[i] = FindFinish(renderer.name);
                    if (indices[i] < 0)
                        throw new InvalidOperationException("Unrecognized microscope material on " +
                            renderer.name + " slot " + i + ". Import the refined Microscope.fbx first.");
                }
                assignments[renderer] = indices;
            }
        }
        if (stationCount == 0 || assignments.Count == 0)
            throw new InvalidOperationException("No microscope stations with renderers found in MuseumV1.");

        EnsureFolder(MaterialFolder);
        var palette = new Material[Finishes.Length];
        for (int i = 0; i < Finishes.Length; i++)
            palette[i] = Make(Finishes[i], shader);
        int changed = 0;
        foreach (var assignment in assignments)
        {
            var renderer = assignment.Key;
            var before = renderer.sharedMaterials;
            var after = new Material[assignment.Value.Length];
            bool different = false;
            for (int i = 0; i < after.Length; i++)
            {
                after[i] = palette[assignment.Value[i]];
                different |= before[i] != after[i];
            }
            if (!different) continue;
            Undo.RecordObject(renderer, "Apply microscope materials");
            renderer.sharedMaterials = after;
            EditorUtility.SetDirty(renderer);
            if (PrefabUtility.IsPartOfPrefabInstance(renderer))
                PrefabUtility.RecordPrefabInstancePropertyModifications(renderer);
            changed++;
        }
        AssetDatabase.SaveAssets();
        EditorSceneManager.MarkSceneDirty(scene);
        if (!EditorSceneManager.SaveScene(scene))
            throw new IOException("Could not save the microscope material changes to MuseumV1.");
        Debug.Log($"Museum microscopes: {stationCount} stations, {assignments.Count} renderers, " +
                  $"{palette.Length} shared materials, {changed} assignments updated.");
    }

    static string Normalize(string value)
    {
        var result = new StringBuilder();
        foreach (char c in value)
            if (char.IsLetterOrDigit(c)) result.Append(char.ToLowerInvariant(c));
        return result.ToString();
    }

    static int FindFinish(string name)
    {
        string key = Normalize(name);
        for (int i = 0; i < Finishes.Length; i++)
            if (key.Contains(Normalize(Finishes[i].Label))) return i;
        return -1;
    }

    static void EnsureFolder(string path)
    {
        if (AssetDatabase.IsValidFolder(path)) return;
        string parent = Path.GetDirectoryName(path).Replace('\\', '/');
        EnsureFolder(parent);
        AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
    }

    static Material Make(Finish finish, Shader shader)
    {
        string path = MaterialFolder + "/" + finish.Label + ".mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (!material)
        {
            material = new Material(shader);
            AssetDatabase.CreateAsset(material, path);
        }
        // Update the existing asset in place, preserving its .meta GUID.
        material.name = finish.Label;
        material.shader = shader;
        material.SetColor("_Color", finish.Color);
        material.SetFloat("_Metallic", finish.Metallic);
        material.SetFloat("_Glossiness", 1f - finish.Roughness);
        material.SetFloat("_GlossMapScale", 1f - finish.Roughness);
        material.SetFloat("_SmoothnessTextureChannel", 0f);
        material.SetFloat("_Mode", 0f);
        material.SetInt("_SrcBlend", (int)BlendMode.One);
        material.SetInt("_DstBlend", (int)BlendMode.Zero);
        material.SetInt("_ZWrite", 1);
        material.SetOverrideTag("RenderType", "Opaque");
        material.renderQueue = -1;
        material.SetFloat("_SpecularHighlights", 1f);
        material.SetFloat("_GlossyReflections", 1f);
        foreach (string property in new[] { "_MainTex", "_MetallicGlossMap", "_BumpMap", "_EmissionMap" })
            material.SetTexture(property, null);
        foreach (string keyword in new[] { "_ALPHATEST_ON", "_ALPHABLEND_ON", "_ALPHAPREMULTIPLY_ON",
            "_METALLICGLOSSMAP", "_NORMALMAP", "_EMISSION", "_SMOOTHNESS_TEXTURE_ALBEDO_CHANNEL_A",
            "_SPECULARHIGHLIGHTS_OFF", "_GLOSSYREFLECTIONS_OFF" })
            material.DisableKeyword(keyword);
        material.SetColor("_EmissionColor", Color.black);
        EditorUtility.SetDirty(material);
        return material;
    }
}
