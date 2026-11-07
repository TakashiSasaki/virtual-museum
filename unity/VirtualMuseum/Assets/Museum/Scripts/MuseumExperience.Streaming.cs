using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

public partial class MuseumExperience
{
    sealed class DetailModel {public AssetBundle bundle;public Mesh mesh;public int used;}
    readonly Dictionary<int,DetailModel> detailModels=new();
    sealed class DisplayDetail
    {
        public MeshFilter filter;
        public Mesh preview;
        public Mesh detail;
    }
    readonly Dictionary<int,DisplayDetail> displayDetails=new();
    UnityWebRequest detailRequest;
    Coroutine detailRoutine;
    int detailGeneration,detailUseCounter;
    bool detailFailed,detailLoading;
    float detailProgress;
    const int DetailMemoryLimit=3;

    bool HasRemoteDetail(int index) => collection && index>=0 && index<collection.entries.Length &&
        !string.IsNullOrEmpty(collection.entries[index].detailBundle);

    void RequestDetail(int index)
    {
        CancelDetailRequest();
        if(!HasRemoteDetail(index))return;
        if(displayDetails.TryGetValue(index,out var display))
        {
            ApplyDetailMesh(display.detail);
            return;
        }
        if(detailModels.TryGetValue(index,out var cached))
        {cached.used=++detailUseCounter;ApplyDetailMesh(cached.mesh);return;}
        detailLoading=true;detailProgress=0;
        detailRoutine=StartCoroutine(LoadDetail(index,detailGeneration));
    }

    IEnumerator LoadDetail(int index,int generation)
    {
        // Hashed URLs are cached by the scoped service worker. Do not also
        // persist the same bundle in Unity's IndexedDB cache.
        var entry=collection.entries[index];
        string baseUrl=Application.absoluteURL;
        if(string.IsNullOrEmpty(baseUrl)) {detailLoading=false;detailFailed=true;yield break;}
        string url=new Uri(new Uri(baseUrl),"Content/"+entry.detailBundle).AbsoluteUri;
        var request=UnityWebRequestAssetBundle.GetAssetBundle(url);
        request.timeout=90;detailRequest=request;
        var operation=request.SendWebRequest();
        while(!operation.isDone)
        {
            detailProgress=entry.detailBytes>0?Mathf.Clamp01((float)request.downloadedBytes/entry.detailBytes):request.downloadProgress;
            yield return null;
        }
        if(generation!=detailGeneration){request.Dispose();yield break;}
        bool succeeded=request.result==UnityWebRequest.Result.Success;
        AssetBundle bundle=succeeded?DownloadHandlerAssetBundle.GetContent(request):null;
        request.Dispose();detailRequest=null;
        Mesh mesh=bundle?bundle.LoadAsset<Mesh>("mesh"):null;
        detailLoading=false;detailRoutine=null;
        if(!mesh)
        {
            if(bundle)bundle.Unload(true);
            detailFailed=true;yield break;
        }
        CacheDetail(index,bundle,mesh);
        if(held && selected==index && mode!="walk")ApplyDetailMesh(mesh);
        while(detailModels.Count>DetailMemoryLimit)
        {
            int oldest=-1;int use=int.MaxValue;
            foreach(var pair in detailModels)if(pair.Key!=index && pair.Value.used<use){use=pair.Value.used;oldest=pair.Key;}
            if(oldest<0)break;
            detailModels[oldest].bundle.Unload(true);detailModels.Remove(oldest);
        }
    }

    void CacheDetail(int index,AssetBundle bundle,Mesh mesh)
    {
        var exhibit=FindExhibit(index);
        var filter=exhibit?exhibit.GetComponentInChildren<MeshFilter>():null;
        if(filter)
        {
            displayDetails[index]=new DisplayDetail {filter=filter,preview=filter.sharedMesh,detail=mesh};
            filter.sharedMesh=mesh;
            // Keep the shared mesh for this visit. The container can be released.
            bundle.Unload(false);
            return;
        }
        detailModels[index]=new DetailModel {bundle=bundle,mesh=mesh,used=++detailUseCounter};
    }

    void ApplyDetailMesh(Mesh mesh)
    {
        if(!held)return;
        // Same coordinates/material slots as the preview: preserve the user's
        // rotation, zoom, lens and current camera transition while replacing it.
        var filter=held.GetComponentInChildren<MeshFilter>();
        if(filter)filter.sharedMesh=mesh;
    }

    void CancelDetailRequest()
    {
        detailGeneration++;
        if(detailRoutine!=null){StopCoroutine(detailRoutine);detailRoutine=null;}
        if(detailRequest!=null){detailRequest.Abort();detailRequest.Dispose();detailRequest=null;}
        detailLoading=false;detailFailed=false;
    }

    void ReleaseDetailModels()
    {
        CancelDetailRequest();
        foreach(var model in detailModels.Values)if(model.bundle)model.bundle.Unload(true);
        detailModels.Clear();
        foreach(var display in displayDetails.Values)
        {
            if(display.filter && display.filter.sharedMesh==display.detail)display.filter.sharedMesh=display.preview;
            if(display.detail)Destroy(display.detail);
        }
        displayDetails.Clear();
    }

    Rect DetailStatusRect => CompactUI?new Rect(12,CompactHeaderHeight+34,uiWidth-24,44):new Rect(28,146,620,44);

    void DrawDetailStatus()
    {
        DrawRoomStatus();
        if(mode=="walk" || !HasRemoteDetail(selected) || (!detailLoading && !detailFailed))return;
        var rect=DetailStatusRect;
        if(detailFailed)
        {
            bool retry=CompactUI?CompactButton(rect,"簡易模型を表示中 · 詳細を再取得"):Button(rect.x,rect.y,rect.width,"簡易模型を表示中 · 詳細を再取得",false,44);
            if(retry)RequestDetail(selected);
        }
        else
        {
            GUI.DrawTexture(rect,dark);
            string text=$"詳細を読み込み中 {Mathf.RoundToInt(detailProgress*100)}% · 回転できます";
            GUI.Label(rect,text,CompactUI?compactLight:darkTextStyle);
            GUI.DrawTexture(new Rect(rect.x,rect.yMax-2,rect.width*detailProgress,2),accent);
        }
    }
}
