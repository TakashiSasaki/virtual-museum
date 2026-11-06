using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class MuseumWayfindingSetup
{
    [MenuItem("Museum/Add Interaction Wayfinding")]
    public static void Add()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop Play mode before adding wayfinding.");
        var scene = SceneManager.GetActiveScene();
        var experience = UnityEngine.Object.FindAnyObjectByType<MuseumExperience>();
        if (!experience || experience.gameObject.scene != scene) throw new InvalidOperationException("Open the museum scene first.");
        if (UnityEngine.Object.FindAnyObjectByType<MuseumWayfinding>()) throw new InvalidOperationException("Wayfinding already exists; edit its anchors in the scene.");
        var shader = Shader.Find("Museum/Wayfinding");
        var textShader = Shader.Find("Museum/WorldText");
        if (!shader || !textShader) throw new InvalidOperationException("Import the wayfinding shaders first.");
        const string directory = "Assets/Museum/Materials/Wayfinding";
        if (!AssetDatabase.IsValidFolder(directory)) AssetDatabase.CreateFolder("Assets/Museum/Materials", "Wayfinding");
        const string materialPath = directory + "/Interaction light.mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
        if (!material)
        {
            material = new Material(shader) { name = "Interaction light" };
            AssetDatabase.CreateAsset(material, materialPath);
        }
        var root = new GameObject("Interaction wayfinding");
        Undo.RegisterCreatedObjectUndo(root, "Add interaction wayfinding");
        var system = root.AddComponent<MuseumWayfinding>();
        system.experience = experience;
        system.beaconMaterial = material;
        system.letteringShader = textShader;
        var landmarks = new List<MuseumWayfinding.Landmark>();
        foreach (var exhibit in UnityEngine.Object.FindObjectsByType<MuseumExhibit>().OrderBy(e => e.index))
        {
            if (exhibit.gameObject.scene != scene) continue;
            Vector3 point = exhibit.transform.position;
            point.x -= 1.35f; point.y = .045f;
            landmarks.Add(Anchor(root.transform, exhibit, MuseumWayfinding.Kind.Specimen, "標本 " + (exhibit.index + 1).ToString("00"), point, 1.77f));
        }
        int number = 0;
        foreach (var station in UnityEngine.Object.FindObjectsByType<MicroscopeStation>().OrderBy(s => s.transform.position.z))
        {
            if (station.gameObject.scene != scene) continue;
            Vector3 point = station.transform.position;
            point.x += 1.33f; point.y = .045f;
            landmarks.Add(Anchor(root.transform, station, MuseumWayfinding.Kind.Microscope, "顕微鏡 " + (++number).ToString("00"), point, 1.86f));
        }
        if (experience.guide && experience.guide.TryGetComponent<GuideMarker>(out var guide))
        {
            Vector3 point = guide.transform.position; point.y = .045f;
            landmarks.Add(Anchor(root.transform, guide, MuseumWayfinding.Kind.Guide, "アイモナイト君", point, 2.55f));
        }
        system.landmarks = landmarks.ToArray();
        EditorUtility.SetDirty(system);
        EditorSceneManager.MarkSceneDirty(scene);
        AssetDatabase.SaveAssets();
        if (!EditorSceneManager.SaveScene(scene)) throw new InvalidOperationException("Wayfinding was added, but the scene could not be saved.");
        Selection.activeGameObject = root;
        Debug.Log("Added " + landmarks.Count + " interaction signs without colliders or additional lights.");
    }

    static MuseumWayfinding.Landmark Anchor(Transform root, Component target, MuseumWayfinding.Kind kind, string title, Vector3 position, float height)
    {
        var anchor = new GameObject(title + " / approach").transform;
        anchor.SetParent(root, false); anchor.position = position;
        return new MuseumWayfinding.Landmark { anchor = anchor, target = target, kind = kind, title = title, badgeHeight = height };
    }
}
