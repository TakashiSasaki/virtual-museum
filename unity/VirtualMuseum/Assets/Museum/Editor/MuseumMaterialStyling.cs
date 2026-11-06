using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>Applies the V1 surface palette without changing models or gameplay.</summary>
public static class MuseumMaterialStyling
{
    const string Root = "Assets/Museum/";
    const string ScenePath = Root + "Scenes/MuseumV1.unity";
    const string MaterialsPath = Root + "Materials/Surfaces/";
    static readonly Dictionary<string, Material> Materials = new Dictionary<string, Material>();

    [MenuItem("Museum/Apply V1 Surface Materials")]
    public static void Apply()
    {
        var scene = SceneManager.GetActiveScene();
        if (EditorApplication.isPlayingOrWillChangePlaymode)
            throw new InvalidOperationException("Stop Play mode before applying materials.");
        if (scene.path != ScenePath || scene.isDirty)
            throw new InvalidOperationException("Open the saved MuseumV1 scene with no unsaved changes first.");
        var shader = Shader.Find("Museum/Triplanar Surface");
        if (!shader || !shader.isSupported)
            throw new InvalidOperationException("Museum surface shader is missing or unsupported.");
        Directory.CreateDirectory(MaterialsPath);
        Materials.Clear();
        // Photographs use their documented physical size, in repeats per metre.
        // Paint's broad plaster variation is reduced; its fine normal survives.
        Make("Wall paint", "WallPaint", 1.15f, 0f, .12f, .00015f, new Color(.94f,.94f,.92f),
            pbr:"WallPaint", pbrTiling:1f, normal:.12f, roughMin:.80f, roughMax:.96f, uniformity:.68f);
        Make("Walnut varnished", "Walnut", 1f, 0f, .39f, .00025f, Color.white,
            pbr:"Walnut", pbrTiling:1f/.6f, normal:.28f, roughMin:.30f, roughMax:.67f,
            local:true, rotation:90f, variation:.035f);
        Make("White laminate", "Laminate", 1.45f, 0f, .38f, .00012f, Color.white);
        Make("Powder coated steel", "PowderCoat", 1.7f, 0f, .30f, .00016f, Color.white);
        Make("Woven carpet", "CarpetWeave", 1.4f, 0f, .035f, .0007f, new Color(.82f,.80f,.75f),
            pbr:"Carpet", pbrTiling:1f/1.7f, normal:.50f, roughMin:.86f, roughMax:.99f, tileSize:.5f);
        Make("Vinyl floor", "VinylFloor", 1f, 0f, .28f, .00016f, Color.white);
        Make("Green rubber mat", "RubberMat", 2f, 0f, .16f, .00018f, Color.white);
        Make("Brushed metal trim", "PowderCoat", 2f, .78f, .48f, .00012f, new Color(.68f,.70f,.69f));

        int count = 0;
        foreach (var renderer in UnityEngine.Object.FindObjectsByType<Renderer>(FindObjectsInactive.Include))
        {
            if (renderer.gameObject.scene != scene || renderer is not MeshRenderer) continue;
            Material desired = Pick(renderer.transform);
            if (!desired || renderer.sharedMaterial == desired) continue;
            renderer.sharedMaterial = desired;
            EditorUtility.SetDirty(renderer);
            if (PrefabUtility.IsPartOfPrefabInstance(renderer))
                PrefabUtility.RecordPrefabInstancePropertyModifications(renderer);
            count++;
        }
        EditorSceneManager.MarkSceneDirty(scene);
        if (!EditorSceneManager.SaveScene(scene))
            throw new IOException("Could not save the material changes to MuseumV1.");
        AssetDatabase.SaveAssets();
        Debug.Log($"Museum V1: applied realistic surface materials to {count} renderers.");
    }

    static Texture2D ImportTexture(string texturePath, bool normal = false, bool color = true)
    {
        var importer = AssetImporter.GetAtPath(texturePath) as TextureImporter;
        if (importer == null) throw new FileNotFoundException("Missing texture", texturePath);
        var type = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
        // Color is sRGB; normal/roughness/height are linear data. Legacy PNG
        // alpha remains a height channel, not cutout or glass transparency.
        if (importer.alphaIsTransparency || importer.wrapMode != TextureWrapMode.Repeat ||
            importer.textureCompression != TextureImporterCompression.Uncompressed || !importer.mipmapEnabled ||
            importer.textureType != type || importer.sRGBTexture != (color && !normal) ||
            importer.anisoLevel != 8 || importer.filterMode != FilterMode.Trilinear)
        {
            importer.textureType = type;
            importer.sRGBTexture = color && !normal;
            importer.alphaIsTransparency = false;
            importer.wrapMode = TextureWrapMode.Repeat;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.mipmapEnabled = true;
            importer.anisoLevel = 8;
            importer.filterMode = FilterMode.Trilinear;
            importer.SaveAndReimport();
        }
        var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath);
        if (!texture) throw new FileNotFoundException("Could not import texture", texturePath);
        return texture;
    }

    static string FindPbr(string name, string map)
    {
        if (string.IsNullOrEmpty(name)) return null;
        foreach (string extension in new[] { ".jpg", ".png", ".jpeg" })
        {
            string path = Root + "Textures/PBR/" + name + "_" + map + extension;
            if (File.Exists(path)) return path;
        }
        return null;
    }

    static void SetMap(Material material, string property, string keyword, string path, bool normal = false)
    {
        material.SetTexture(property, path == null ? null : ImportTexture(path, normal, false));
        if (path == null) material.DisableKeyword(keyword);
        else material.EnableKeyword(keyword);
    }

    static void Make(string name, string image, float tiling, float metallic,
                     float smoothness, float relief, Color color, string pbr = null,
                     float pbrTiling = 1f, float normal = .3f, float roughMin = 0f,
                     float roughMax = 1f, bool local = false, float rotation = 0f,
                     float variation = 0f, float tileSize = 0f, float uniformity = 0f)
    {
        string photoPath = FindPbr(pbr, "BaseColor");
        bool photographic = photoPath != null;
        string texturePath = photoPath ?? Root + "Textures/" + image + ".png";
        var texture = ImportTexture(texturePath);
        string path = MaterialsPath + name + ".mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (!material)
        {
            material = new Material(Shader.Find("Museum/Triplanar Surface")) { name = name };
            AssetDatabase.CreateAsset(material, path);
        }
        material.shader = Shader.Find("Museum/Triplanar Surface");
        material.SetTexture("_MainTex", texture);
        material.SetColor("_Color", color);
        material.SetFloat("_ColorUniformity", photographic ? uniformity : 0);
        material.SetFloat("_Tiling", photographic ? pbrTiling : tiling);
        material.SetFloat("_ObjectCoordinates", local ? 1 : 0);
        material.SetFloat("_TextureRotation", photographic ? rotation : 0);
        material.SetFloat("_ObjectVariation", variation);
        material.SetFloat("_Metallic", metallic);
        material.SetFloat("_Smoothness", smoothness);
        material.SetFloat("_RoughnessMin", roughMin);
        material.SetFloat("_RoughnessMax", roughMax);
        material.SetFloat("_NormalStrength", normal);
        string normalPath = photographic ? FindPbr(pbr, "NormalGL") : null;
        string heightPath = photographic ? FindPbr(pbr, "Height") : null;
        material.SetFloat("_Relief", photographic && heightPath == null ? 0 : relief);
        SetMap(material, "_NormalMap", "_SURFACE_NORMAL", normalPath, true);
        SetMap(material, "_RoughnessMap", "_SURFACE_ROUGHNESS", photographic ? FindPbr(pbr, "Roughness") : null);
        SetMap(material, "_HeightMap", "_SURFACE_HEIGHT", heightPath);
        material.SetFloat("_TileSize", tileSize);
        material.SetFloat("_TileSeamWidth", .0008f);
        EditorUtility.SetDirty(material);
        Materials[name] = material;
    }

    static Material Pick(Transform obj)
    {
        string name = obj.name;
        if (name == "Back wall" || name == "Left wall" || name == "Right wall" ||
            name.StartsWith("Entrance wall ", StringComparison.Ordinal) || name == "Ceiling")
            return Materials["Wall paint"];
        if (name == "Walkable floor") return Materials["Woven carpet"];
        if (name == "Work area floor") return Materials["Vinyl floor"];
        if (name == "Metal floor strip") return Materials["Brushed metal trim"];
        if (name.StartsWith("Walnut tray ", StringComparison.Ordinal)) return Materials["Walnut varnished"];
        if (name.StartsWith("Exhibit plinth ", StringComparison.Ordinal)) return Materials["Powder coated steel"];

        bool inShelf = false, inBench = false;
        for (var parent = obj.parent; parent; parent = parent.parent)
        {
            if (parent.name == "SpecimenShelf") inShelf = true;
            if (parent.name == "ObservationBench") inBench = true;
        }
        if (inShelf)
        {
            if (name.StartsWith("Specimen drawer", StringComparison.Ordinal) ||
                name.StartsWith("Inclined display", StringComparison.Ordinal)) return Materials["Walnut varnished"];
            if (name.StartsWith("Shelf upright", StringComparison.Ordinal) || name == "Storage base" ||
                name == "Door" || name.StartsWith("Door.", StringComparison.Ordinal)) return Materials["Powder coated steel"];
            if (name.StartsWith("Tray lining", StringComparison.Ordinal)) return Materials["White laminate"];
        }
        if (inBench)
        {
            if (name == "Bench top") return Materials["White laminate"];
            if (name.StartsWith("Bench leg", StringComparison.Ordinal) ||
                name.StartsWith("Wall cabinet", StringComparison.Ordinal)) return Materials["Powder coated steel"];
            if (name == "Observation mat") return Materials["Green rubber mat"];
        }
        return null;
    }
}
