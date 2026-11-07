using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine.SceneManagement;
using Object=UnityEngine.Object;

public static class MuseumBackyardPreview
{
    public static Texture2D Generate(MuseumCollection.Entry[] entries,string path)
    {
        const int cell=128,columns=5;
        int rows=Mathf.CeilToInt(entries.Length/(float)columns);
        var atlas=new Texture2D(cell*columns,cell*rows,TextureFormat.RGB24,false);
        var scene=EditorSceneManager.NewPreviewScene();
        var cameraObject=new GameObject("Backyard thumbnail camera");SceneManager.MoveGameObjectToScene(cameraObject,scene);
        var camera=cameraObject.AddComponent<Camera>();camera.clearFlags=CameraClearFlags.SolidColor;
        camera.scene=scene;
        camera.backgroundColor=new Color(.85f,.88f,.84f);camera.orthographic=true;camera.nearClipPlane=.01f;camera.farClipPlane=100;
        var rt=new RenderTexture(cell,cell,24);camera.targetTexture=rt;
        var previous=RenderTexture.active;
        try
        {
            for(int i=0;i<2;i++)
            {
                var lightObject=new GameObject("Thumbnail light");SceneManager.MoveGameObjectToScene(lightObject,scene);
                var light=lightObject.AddComponent<Light>();light.type=LightType.Directional;light.intensity=i==0?1.25f:.7f;
                lightObject.transform.rotation=Quaternion.Euler(i==0?45:25,i==0?-35:145,0);
            }
            for(int i=0;i<entries.Length;i++)
            {
                var model=Object.Instantiate(entries[i].model);SceneManager.MoveGameObjectToScene(model,scene);
                try
                {
                    var rs=model.GetComponentsInChildren<Renderer>();var bounds=rs[0].bounds;foreach(var r in rs)bounds.Encapsulate(r.bounds);
                    float radius=Mathf.Max(.01f,bounds.extents.magnitude);
                    camera.transform.position=bounds.center+new Vector3(.35f,1.35f,-1.4f).normalized*radius*3.5f;
                    camera.transform.LookAt(bounds.center);camera.orthographicSize=radius*1.05f;
                    camera.Render();RenderTexture.active=rt;
                    atlas.ReadPixels(new Rect(0,0,cell,cell),(i%columns)*cell,(rows-1-i/columns)*cell);
                }
                finally {Object.DestroyImmediate(model);}
            }
            atlas.Apply();File.WriteAllBytes(path,atlas.EncodeToPNG());
        }
        finally {RenderTexture.active=previous;camera.targetTexture=null;Object.DestroyImmediate(rt);Object.DestroyImmediate(atlas);EditorSceneManager.ClosePreviewScene(scene);}
        AssetDatabase.ImportAsset(path);
        var importer=(TextureImporter)AssetImporter.GetAtPath(path);importer.mipmapEnabled=false;importer.npotScale=TextureImporterNPOTScale.None;
        importer.maxTextureSize=1024;importer.textureCompression=TextureImporterCompression.Uncompressed;importer.SaveAndReimport();
        return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
    }
}
