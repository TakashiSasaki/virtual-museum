using System;
using UnityEngine;

public partial class MuseumExperience
{
    public MuseumCollection collection;
    int collectionPage;
    bool selectionPinned;
    int SpecimenCount => specimenModels.Length;
    int DestinationForSpecimen(int index) => index<3?index:index+2;
    int SpecimenForDestination(int index) => index<3?index:index>=5?index-2:-1;
    int ListDestination(int slot) => slot<SpecimenCount?DestinationForSpecimen(slot):slot==SpecimenCount?3:4;
    string ListDestinationLabel(int slot) => slot<SpecimenCount?(slot+1).ToString("00")+"  "+names[slot]:slot==SpecimenCount?"観察台・顕微鏡":"入口・全体を見渡す";
    string ScopeCaption => collection && selected<collection.entries.Length?collection.entries[selected].microscopeCaption:"拡大資料";

    void FaceSelectedSpecimen()
    {
        var target=FindExhibit(selected);if(!target)return;
        var delta=InteractionPoint(target)-visitorCamera.transform.position;
        yaw=Mathf.Atan2(delta.x,delta.z)*Mathf.Rad2Deg;
        pitch=Mathf.Clamp(-Mathf.Atan2(delta.y,new Vector2(delta.x,delta.z).magnitude)*Mathf.Rad2Deg,-60,60);
        visitor.transform.rotation=Quaternion.Euler(0,yaw,0);visitorCamera.transform.localRotation=Quaternion.Euler(pitch,0,0);
    }

    void LoadCollection()
    {
        if(!collection || collection.entries==null || collection.entries.Length==0) return;
        names=Array.ConvertAll(collection.entries,e=>e.title);
        english=Array.ConvertAll(collection.entries,e=>e.english);
        descriptions=Array.ConvertAll(collection.entries,e=>e.description);
        specimenModels=Array.ConvertAll(collection.entries,e=>e.model);
        selected=Mathf.Clamp(selected,0,SpecimenCount-1);
    }

    Texture2D ScopeImage(int index)
    {
        if(scopeTextures[index]) return scopeTextures[index];
        int kind=collection?collection.entries[index].microscopePattern:index;
        scopeTextures[index]=MakeScope(kind);
        return scopeTextures[index];
    }

    void DrawCollectionDestinations()
    {
        const int pageSize=5;
        int pages=Mathf.CeilToInt((SpecimenCount+2)/(float)pageSize);
        collectionPage=Mathf.Clamp(collectionPage,0,pages-1);
        GUI.DrawTexture(new Rect(20,110,360,470),panel);
        Label(40,126,320,45,"展示一覧・移動",bodyStyle);
        for(int row=0;row<pageSize;row++)
        {
            int slot=collectionPage*pageSize+row;
            if(slot>=SpecimenCount+2) break;
            if(Button(36,180+row*61,328,ListDestinationLabel(slot)))Jump(ListDestination(slot));
        }
        if(Button(36,500,92,"前へ"))collectionPage=Mathf.Max(0,collectionPage-1);
        Label(138,510,120,35,(collectionPage+1)+" / "+pages,bodyStyle);
        if(Button(272,500,92,"次へ"))collectionPage=Mathf.Min(pages-1,collectionPage+1);
    }

    static Bounds ModelBounds(GameObject root)
    {
        var renderers=root.GetComponentsInChildren<Renderer>();
        Bounds bounds=renderers.Length>0?renderers[0].bounds:new Bounds(root.transform.position,Vector3.one);
        foreach(var renderer in renderers)bounds.Encapsulate(renderer.bounds);
        return bounds;
    }

    static Color MicroscopePattern(int kind,int x,int y)
    {
        float u=(x-256)/256f,v=(y-256)/256f;
        float grain=Mathf.PerlinNoise(x*.12f,y*.12f);
        if(kind==3 || kind==4)
        {
            float bands=.5f+.5f*Mathf.Cos(y*.06f+Mathf.Sin(x*.025f));
            float hairs=Mathf.Pow(Mathf.Max(0,Mathf.Sin(x*.24f+y*.035f)),20);
            return Color.Lerp(new Color(.11f,.16f,.10f),new Color(.64f,.70f,.34f),bands*.6f+grain*.25f+hairs*.15f);
        }
        if(kind>=5 && kind<=7)
        {
            float radius=kind==5?Mathf.Sqrt(u*u*2.2f+v*v*.75f):kind==6?Mathf.Sqrt(u*u*5+v*v*.8f):Mathf.Abs(u)*1.6f+Mathf.Abs(v)*.75f;
            Color water=new Color(.08f,.18f,.22f);
            if(radius>1) return Color.Lerp(water,new Color(.22f,.38f,.41f),grain*.3f);
            float membrane=Mathf.SmoothStep(.84f,1,radius);
            float detail=kind==7?Mathf.Pow(Mathf.Abs(Mathf.Sin(y*.21f)),5):Mathf.PerlinNoise(x*.035f,y*.035f);
            Color cell=kind==6?new Color(.25f,.64f,.24f):kind==7?new Color(.77f,.62f,.31f):new Color(.63f,.73f,.64f);
            return Color.Lerp(Color.Lerp(water,cell,.45f+detail*.5f),Color.white,membrane*.55f);
        }
        if(kind==8 || kind==9)
        {
            float face=Mathf.Abs(Mathf.Sin(x*.024f+y*.014f)*Mathf.Cos(y*.026f));
            float lines=Mathf.Pow(Mathf.Abs(Mathf.Sin((kind==8?x+y:x)*.19f)),20);
            return Color.Lerp(kind==8?new Color(.22f,.29f,.36f):new Color(.22f,.18f,.07f),kind==8?new Color(.85f,.9f,.95f):new Color(.83f,.66f,.27f),face*.7f+lines*.2f);
        }
        float filament=kind==10?Mathf.Abs(Mathf.Sin((y-Mathf.Abs(x-256)*.6f)*.15f)):kind==11?Mathf.Abs(Mathf.Sin(x*.18f+Mathf.Sin(y*.02f))):Mathf.Abs(Mathf.Sin(x*.06f)*Mathf.Sin(y*.08f));
        return Color.Lerp(kind==10?new Color(.025f,.17f,.25f):new Color(.17f,.11f,.05f),kind==10?new Color(.20f,.65f,.73f):kind==11?new Color(.72f,.46f,.25f):new Color(.42f,.65f,.25f),filament*.8f+grain*.2f);
    }
}
