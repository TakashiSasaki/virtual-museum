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
        // Tiling is specified in repeats per metre. Colors live in the texture;
        // the neutral tint avoids multiplying the photographed palette twice.
        Make("Wall paint", "WallPaint", 1.15f, 0f, .13f, .00035f, Color.white);
        Make("Walnut varnished", "Walnut", 1.0f, 0f, .30f, .0015f, Color.white);
        Make("White laminate", "Laminate", 1.45f, 0f, .34f, .0008f, Color.white);
        Make("Powder coated steel", "PowderCoat", 1.7f, 0f, .33f, .0008f, Color.white);
        Make("Woven carpet", "CarpetWeave", 1.4f, 0f, .06f, .0018f, Color.white);
        Make("Vinyl floor", "VinylFloor", 1.2f, 0f, .24f, .0008f, Color.white);
        Make("Green rubber mat", "RubberMat", 2f, 0f, .16f, .0008f, Color.white);
        Make("Brushed metal trim", "PowderCoat", 2f, .72f, .46f, .0005f, new Color(.68f,.70f,.69f));

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

    static void Make(string name, string image, float tiling, float metallic,
                     float smoothness, float relief, Color color)
    {
        string texturePath = Root + "Textures/" + image + ".png";
        var importer = AssetImporter.GetAtPath(texturePath) as TextureImporter;
        if (importer == null) throw new FileNotFoundException("Missing texture", texturePath);
        // Alpha is a height map, not transparency. Preserve it unchanged.
        if (importer.alphaIsTransparency || importer.wrapMode != TextureWrapMode.Repeat ||
            importer.textureCompression != TextureImporterCompression.Uncompressed || !importer.mipmapEnabled)
        {
            importer.alphaIsTransparency = false;
            importer.wrapMode = TextureWrapMode.Repeat;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.mipmapEnabled = true;
            importer.SaveAndReimport();
        }
        var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(texturePath);
        if (!texture) throw new FileNotFoundException("Could not import texture", texturePath);
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
        material.SetFloat("_Tiling", tiling);
        material.SetFloat("_Metallic", metallic);
        material.SetFloat("_Smoothness", smoothness);
        material.SetFloat("_Relief", relief);
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
