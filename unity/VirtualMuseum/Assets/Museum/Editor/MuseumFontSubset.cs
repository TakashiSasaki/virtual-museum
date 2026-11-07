using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Globalization;
using System.Security.Cryptography;
using System.Text.RegularExpressions;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

// Catch new display text before publishing a player with missing font glyphs.
public sealed class MuseumFontSubset : IPreprocessBuildWithReport
{
    const string Root = "Assets/Museum";
    [Serializable] sealed class Manifest
    {
        public int version;
        public string subsetSha256;
        public int[] codepoints;
        public int[] unsupported;
    }
    public int callbackOrder => 0;
    public void OnPreprocessBuild(BuildReport report) => Validate();

    public static void Validate()
    {
        const string instructions = "Regenerate the museum font: python work/prepare_web_font.py (see docs/web-optimization.md).";
        var manifestPath = Root + "/Editor/FontSubset.json";
        if (!File.Exists(manifestPath)) throw new BuildFailedException(instructions);
        var data = JsonUtility.FromJson<Manifest>(File.ReadAllText(manifestPath));
        if (data.version != 1 || data.codepoints == null || data.unsupported == null)
            throw new BuildFailedException("Invalid font manifest. " + instructions);
        using (var sha = SHA256.Create())
        {
            var bytes = File.ReadAllBytes(Root + "/Resources/MuseumFonts/NotoSansJP-Regular.otf");
            var hash = BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant();
            if (hash != data.subsetSha256) throw new BuildFailedException("Font fingerprint differs. " + instructions);
        }
        var covered = new HashSet<int>(data.codepoints.Concat(data.unsupported));
        var missing = new SortedSet<int>();
        foreach (var file in Directory.GetFiles(Root, "*", SearchOption.AllDirectories))
        {
            if (file.Replace('\\', '/').Contains("/GeneratedWeb/")) continue;
            var extension = Path.GetExtension(file);
            if (extension != ".cs" && extension != ".asset" && extension != ".unity") continue;
            var content = Regex.Replace(File.ReadAllText(file), @"\\u([0-9a-fA-F]{4})",
                m => ((char)int.Parse(m.Groups[1].Value, NumberStyles.HexNumber)).ToString());
            foreach (char c in content)
            {
                var category = char.GetUnicodeCategory(c);
                if (category == UnicodeCategory.Control || category == UnicodeCategory.Format ||
                    category == UnicodeCategory.Surrogate || category == UnicodeCategory.OtherNotAssigned) continue;
                if (!covered.Contains(c)) missing.Add(c);
            }
        }
        if (missing.Count > 0) throw new BuildFailedException("New font characters: " +
            string.Join(", ", missing.Take(16).Select(c => "U+" + c.ToString("X4"))) + ". " + instructions);
    }
}
