using System.Collections.Generic;
using UnityEngine;

// Web builds cannot access the visitor's operating-system fonts. The bundled
// Japanese font is shared by IMGUI, room lettering and interaction signs.
public partial class MuseumExperience
{
    readonly List<Material> roomFontMaterials = new();

    void SetupFonts()
    {
        if (!japaneseFont)
            japaneseFont = Resources.Load<Font>("MuseumFonts/NotoSansJP-Regular");
        if (!japaneseFont)
        {
            Debug.LogError("The bundled museum Japanese font is missing.", this);
            return;
        }

        Font.textureRebuilt += RefreshRoomFonts;
        var materials = new Dictionary<Material, Material>();
        foreach (var text in FindObjectsByType<TextMesh>(FindObjectsInactive.Include))
        {
            // Explicitly assigned alternative fonts retain their own atlas.
            if (text.font && text.font != japaneseFont) continue;
            var renderer = text.GetComponent<Renderer>();
            if (!renderer) continue;
            var source = renderer.sharedMaterial ? renderer.sharedMaterial : japaneseFont.material;
            if (!materials.TryGetValue(source, out var material))
            {
                material = new Material(source) { name = source.name + " (museum font runtime)" };
                materials.Add(source, material);
                roomFontMaterials.Add(material);
            }
            text.font = japaneseFont;
            renderer.sharedMaterial = material;
        }
        RefreshRoomFonts(japaneseFont);
    }

    void RefreshRoomFonts(Font rebuilt)
    {
        if (rebuilt != japaneseFont || !japaneseFont) return;
        foreach (var material in roomFontMaterials)
            if (material) material.mainTexture = japaneseFont.material.mainTexture;
    }

    void ReleaseFonts()
    {
        Font.textureRebuilt -= RefreshRoomFonts;
        foreach (var material in roomFontMaterials)
            if (material) Destroy(material);
        roomFontMaterials.Clear();
    }
}
