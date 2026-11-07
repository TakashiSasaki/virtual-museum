using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

// Added to the build copy only. The editable scene keeps the original assets.
public sealed class MuseumRoomStreaming : MonoBehaviour
{
    [Serializable] public sealed class MeshTarget
    {
        public MeshFilter filter;
        public SkinnedMeshRenderer skin;
        public int index;
        public Transform Anchor => filter ? filter.transform : skin ? skin.transform : null;
    }
    [Serializable] public sealed class TextureTarget
    {
        public Material material;
        public string property;
        public int index;
    }
    [Serializable] public sealed class Chunk
    {
        public string file, label;
        public long bytes;
        public MeshTarget[] meshes = Array.Empty<MeshTarget>();
        public TextureTarget[] textures = Array.Empty<TextureTarget>();
        public GameObject[] placeholders = Array.Empty<GameObject>();
        [NonSerialized] public bool loaded, failed;
    }
    public Chunk[] chunks = Array.Empty<Chunk>();
    public MuseumExperience experience;
    readonly List<AssetBundle> bundles = new();
    UnityWebRequest request;
    Chunk active, preferred;
    public int Completed { get; private set; }
    public int Failed { get { int n=0;foreach(var c in chunks)if(c.failed)n++;return n; } }
    public bool Pending => Completed < chunks.Length;
    public string Status => Failed>0 ? "一部の展示を再取得" :
        $"展示室を準備中 {Completed}/{chunks.Length} · 移動できます";

    IEnumerator Start()
    {
        // Allow the first interactive frame before background traffic starts.
        yield return new WaitForSecondsRealtime(1);
        while (true)
        {
            if (experience && experience.DetailDownloadInProgress) {yield return null;continue;}
            active=NextChunk();
            if(active==null){yield return new WaitForSecondsRealtime(.3f);continue;}
            yield return Load(active);
            active=null;
            yield return null;
        }
    }

    Chunk NextChunk()
    {
        if(preferred!=null && !preferred.loaded && !preferred.failed)return preferred;
        Chunk next=null;float best=float.MaxValue;
        var camera=experience ? experience.visitorCamera : Camera.main;
        foreach(var chunk in chunks)
        {
            if(chunk.loaded || chunk.failed)continue;
            float score=chunk.textures.Length>0 ? 50 : 20;
            foreach(var target in chunk.meshes)
            {
                if(!target.Anchor || !camera)continue;
                var delta=target.Anchor.position-camera.transform.position;
                score=Mathf.Min(score,delta.magnitude+(Vector3.Dot(camera.transform.forward,delta.normalized)<0?8:0));
            }
            if(chunk.label=="アイモナイト君")score-=15;
            if(score<best){best=score;next=chunk;}
        }
        return next;
    }

    public void Prioritize(Component target)
    {
        if(!target)return;
        foreach(var chunk in chunks)foreach(var mesh in chunk.meshes)
            if(mesh.Anchor && (mesh.Anchor==target.transform || mesh.Anchor.IsChildOf(target.transform)))
            {preferred=chunk;chunk.failed=false;return;}
    }
    public void RetryFailed() {foreach(var chunk in chunks)chunk.failed=false;}

    IEnumerator Load(Chunk chunk)
    {
        if(string.IsNullOrEmpty(Application.absoluteURL)){chunk.failed=true;yield break;}
        string url=new Uri(new Uri(Application.absoluteURL),"Content/"+chunk.file).AbsoluteUri;
        request=UnityWebRequestAssetBundle.GetAssetBundle(url);request.timeout=60;
        yield return request.SendWebRequest();
        AssetBundle bundle=request.result==UnityWebRequest.Result.Success?DownloadHandlerAssetBundle.GetContent(request):null;
        request.Dispose();request=null;
        if(!bundle){chunk.failed=true;yield break;}
        var operation=bundle.LoadAssetAsync<MuseumRoomPayload>("payload");
        yield return operation;
        var payload=operation.asset as MuseumRoomPayload;
        bool valid=payload;
        if(valid)foreach(var target in chunk.meshes)
            if(target.index<0 || target.index>=payload.meshes.Length || !payload.meshes[target.index])valid=false;
        if(valid)foreach(var target in chunk.textures)
            if(target.index<0 || target.index>=payload.textures.Length || !payload.textures[target.index])valid=false;
        if(!valid){bundle.Unload(true);chunk.failed=true;yield break;}
        // Binding to existing renderers retains bones, interaction targets and all poses.
        foreach(var target in chunk.meshes)
        {
            if(target.filter)target.filter.sharedMesh=payload.meshes[target.index];
            if(target.skin)target.skin.sharedMesh=payload.meshes[target.index];
        }
        foreach(var target in chunk.textures)if(target.material)
            target.material.SetTexture(target.property,payload.textures[target.index]);
        foreach(var placeholder in chunk.placeholders)if(placeholder)Destroy(placeholder);
        bundles.Add(bundle);chunk.loaded=true;Completed++;
    }

    void OnDestroy()
    {
        if(request!=null){request.Abort();request.Dispose();request=null;}
        foreach(var bundle in bundles)if(bundle)bundle.Unload(true);
        bundles.Clear();
    }
}
