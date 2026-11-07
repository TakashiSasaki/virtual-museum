using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;
using UnityEngine.Rendering;

/// <summary>Reproducible static Web build for the public GitHub Pages demo.</summary>
public static class MuseumWebBuild
{
    public const string ScenePath = "Assets/Museum/Scenes/MuseumV1.unity";
    public const string OutputPath = "Build/WebGL";

    [MenuItem("Museum/Web/Configure GitHub Pages")]
    public static void Configure()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
            throw new InvalidOperationException("Stop Play mode before configuring the Web build.");
        if (!BuildPipeline.IsBuildTargetSupported(BuildTargetGroup.WebGL, BuildTarget.WebGL))
            throw new InvalidOperationException("Install Web Build Support for this Unity Editor.");

        // Pages cannot supply custom Content-Encoding or cross-origin isolation headers.
        PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Brotli;
        PlayerSettings.WebGL.decompressionFallback = true;
        PlayerSettings.WebGL.threadsSupport = false;
        PlayerSettings.WebGL.nameFilesAsHashes = true;
        PlayerSettings.WebGL.dataCaching = true;
        PlayerSettings.WebGL.showDiagnostics = false;
        PlayerSettings.WebGL.initialMemorySize = 256;
        PlayerSettings.WebGL.maximumMemorySize = 2048;
        PlayerSettings.WebGL.template = "PROJECT:Museum";
        PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.WebGL, false);
        PlayerSettings.SetGraphicsAPIs(BuildTarget.WebGL, new[] { GraphicsDeviceType.OpenGLES3 });
        PlayerSettings.defaultWebScreenWidth = 1440;
        PlayerSettings.defaultWebScreenHeight = 900;
        EditorUserBuildSettings.development = false;
        EditorUserBuildSettings.allowDebugging = false;
        EditorUserBuildSettings.connectProfiler = false;
        UnityEditor.WebGL.UserBuildSettings.codeOptimization = UnityEditor.WebGL.WasmCodeOptimization.DiskSizeLTO;
        PlayerSettings.SetIl2CppCodeGeneration(UnityEditor.Build.NamedBuildTarget.WebGL, Il2CppCodeGeneration.OptimizeSize);
        PlayerSettings.SetManagedStrippingLevel(UnityEditor.Build.NamedBuildTarget.WebGL, ManagedStrippingLevel.High);
        PlayerSettings.stripEngineCode = true;
        PlayerSettings.stripUnusedMeshComponents = true;
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
        AssetDatabase.SaveAssets();
    }

    [MenuItem("Museum/Web/Build GitHub Pages")]
    public static void Build()
    {
        MuseumFontSubset.Validate();
        Configure();
        MuseumProgressiveBuild.Prepare();
        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
        {
            scenes = new[] { ScenePath },
            locationPathName = OutputPath,
            target = BuildTarget.WebGL,
            options = BuildOptions.DetailedBuildReport
        });
        if (report.summary.result != BuildResult.Succeeded)
            throw new InvalidOperationException("Web build failed: " + report.summary.result);

        FinalizeOutput();
        Debug.Log("Web build ready: " + OutputPath);
    }

    // Also callable after the Unity CLI's asynchronous build command succeeds.
    public static void FinalizeOutput()
    {
        if (!File.Exists(Path.Combine(OutputPath, "index.html")))
            throw new FileNotFoundException("Build the Web player before preparing its publication.");
        File.WriteAllText(Path.Combine(OutputPath, ".nojekyll"), "");
        var htmlPath=Path.Combine(OutputPath,"index.html");
        long startupBytes=0;
        foreach(var file in Directory.GetFiles(Path.Combine(OutputPath,"Build")))startupBytes+=new FileInfo(file).Length;
        startupBytes+=new FileInfo(htmlPath).Length+new FileInfo(Path.Combine(OutputPath,"museum.css")).Length;
        string megabytes=(Math.Ceiling(startupBytes/100000d)/10d).ToString("0.0",System.Globalization.CultureInfo.InvariantCulture);
        File.WriteAllText(htmlPath,File.ReadAllText(htmlPath).Replace("__MUSEUM_INITIAL_MB__",megabytes));
        var workerPath=Path.Combine(OutputPath,"museum-sw.js");
        using(var sha=System.Security.Cryptography.SHA256.Create())
        {
            string shell=File.ReadAllText(Path.Combine(OutputPath,"index.html"))+File.ReadAllText(Path.Combine(OutputPath,"museum.css"));
            string release=BitConverter.ToString(sha.ComputeHash(System.Text.Encoding.UTF8.GetBytes(shell))).Replace("-","").ToLowerInvariant().Substring(0,16);
            File.WriteAllText(workerPath,File.ReadAllText(workerPath).Replace("__MUSEUM_RELEASE__",release));
        }
        var notices = Path.Combine(Application.dataPath, "Museum/Resources/MuseumFonts/LICENSE.txt");
        if (!File.Exists(notices))
            throw new FileNotFoundException("The bundled font license must accompany the Web player.", notices);
        File.Copy(notices, Path.Combine(OutputPath, "FONT-LICENSE.txt"), true);
        File.WriteAllText(Path.Combine(OutputPath, "THIRD-PARTY-NOTICES.txt"),
            "Museum JP Subset (derived from Noto Sans JP): SIL Open Font License 1.1. See FONT-LICENSE.txt.\n" +
            "https://github.com/notofonts/noto-cjk\n\n" +
            "Surface photographs (CC0):\n" +
            "Fine Grained Wood / Rob Tuytel: https://polyhaven.com/a/fine_grained_wood\n" +
            "White Plaster 02: https://polyhaven.com/a/white_plaster_02\n" +
            "Carpet016: https://ambientcg.com/view?id=Carpet016\n");
    }
}
