using UnityEngine;

public partial class MuseumExperience
{
    Texture2D navigationBase, navigationThumb, navigationDirection;
    GUIStyle navigationCaption;

    bool TouchNavigationContains(Vector2 point)
    {
        var pad=TouchNavigationRect;
        return (point-pad.center).sqrMagnitude<=pad.width*pad.width*.25f;
    }

    static float NavigationRamp(float low,float high,float value) => Mathf.SmoothStep(0,1,Mathf.InverseLerp(low,high,value));

    // Small cached RGBA textures: no opaque panel behind the controls.
    // Lighting is baked into the UI pixels, so it remains stable over the scene.
    Texture2D CreateNavigationDisc(bool thumb)
    {
        const int size=128;
        var texture=new Texture2D(size,size,TextureFormat.RGBA32,false){
            name=thumb?"Navigation glass thumb":"Navigation glass base",
            wrapMode=TextureWrapMode.Clamp,filterMode=FilterMode.Bilinear,
            hideFlags=HideFlags.HideAndDontSave};
        var pixels=new Color[size*size];
        for(int y=0;y<size;y++)for(int x=0;x<size;x++)
        {
            float u=(x+.5f)/size*2-1,v=(y+.5f)/size*2-1;
            float r=Mathf.Sqrt(u*u+v*v);
            float edge=1-NavigationRamp(.96f,1f,r);
            if(edge<=0)continue;
            float light=Mathf.Clamp01(.5f+(-u+v)*.32f);
            Color color;
            if(thumb)
            {
                float dome=Mathf.Sqrt(Mathf.Max(0,1-r*r));
                color=Color.Lerp(new Color(.035f,.20f,.21f),new Color(.57f,.86f,.80f),light*.68f+dome*.18f);
                float rim=NavigationRamp(.81f,.93f,r);
                color=Color.Lerp(color,Color.Lerp(new Color(.02f,.12f,.15f),new Color(.83f,.98f,.94f),light),rim*.75f);
                float shine=Mathf.Exp(-((u+.30f)*(u+.30f)+(v-.36f)*(v-.36f))*13f);
                color=Color.Lerp(color,Color.white,shine*.46f);
                color.a=(.48f+rim*.13f+shine*.10f)*edge;
            }
            else
            {
                float rim=Mathf.Exp(-Mathf.Pow((r-.91f)/.026f,2));
                float inner=Mathf.Exp(-Mathf.Pow((r-.69f)/.018f,2));
                color=Color.Lerp(new Color(.035f,.12f,.15f),new Color(.73f,.91f,.88f),rim*(.25f+light*.65f));
                color.a=(.16f+rim*.30f+inner*.09f)*edge;
                // Four inset direction marks, kept subtle against bright floors.
                bool mark=(Mathf.Abs(u)<.026f && Mathf.Abs(v)>.74f && Mathf.Abs(v)<.82f)||
                          (Mathf.Abs(v)<.026f && Mathf.Abs(u)>.74f && Mathf.Abs(u)<.82f);
                if(mark)color=new Color(.85f,.97f,.93f,.55f);
            }
            pixels[y*size+x]=color;
        }
        texture.SetPixels(pixels);texture.Apply(false,true);return texture;
    }

    Texture2D CreateNavigationDirection()
    {
        const int size=128;
        var texture=new Texture2D(size,size,TextureFormat.RGBA32,false){name="Navigation direction feedback",wrapMode=TextureWrapMode.Clamp,filterMode=FilterMode.Bilinear,hideFlags=HideFlags.HideAndDontSave};
        var pixels=new Color[size*size];
        for(int y=0;y<size;y++)for(int x=0;x<size;x++)
        {
            float u=(x+.5f)/size*2-1,v=(y+.5f)/size*2-1;
            float r=Mathf.Sqrt(u*u+v*v);
            float angle=Mathf.Abs(Mathf.Atan2(u,v)*Mathf.Rad2Deg);
            float sector=1-NavigationRamp(22,40,angle);
            float ring=Mathf.Exp(-Mathf.Pow((r-.90f)/.055f,2));
            float glow=Mathf.Exp(-Mathf.Pow((r-.82f)/.15f,2))*.20f;
            float alpha=(ring*.82f+glow)*sector*(1-NavigationRamp(.97f,1,r));
            pixels[y*size+x]=new Color(.24f,1f,.78f,alpha);
        }
        texture.SetPixels(pixels);texture.Apply(false,true);return texture;
    }

    void DrawTouchNavigation()
    {
        if(!navigationBase)navigationBase=CreateNavigationDisc(false);
        if(!navigationThumb)navigationThumb=CreateNavigationDisc(true);
        if(!navigationDirection)navigationDirection=CreateNavigationDirection();
        Rect pad=TouchNavigationRect;
        var old=GUI.color;GUI.color=Color.white;
        GUI.DrawTexture(pad,navigationBase);
        if(navigationDeflection.sqrMagnitude>0)
        {
            var matrix=GUI.matrix;
            GUIUtility.RotateAroundPivot(Mathf.Atan2(navigationDeflection.x,navigationDeflection.y)*Mathf.Rad2Deg,pad.center);
            GUI.color=navigationLooking?new Color(1,.65f,.35f,1):new Color(1,1,1,Mathf.Lerp(.65f,1,navigationDeflection.magnitude));
            GUI.DrawTexture(pad,navigationDirection);
            GUI.matrix=matrix;GUI.color=Color.white;
        }
        var center=pad.center+new Vector2(navigationDeflection.x,-navigationDeflection.y)*pad.width*.27f;
        float diameter=pad.width*.40f;
        GUI.color=new Color(0,.06f,.08f,.20f);
        GUI.DrawTexture(new Rect(center.x-diameter*.5f,center.y-diameter*.5f+3,diameter,diameter),navigationThumb);
        GUI.color=navigationLooking?new Color(1,.8f,.48f,1):Color.white;
        GUI.DrawTexture(new Rect(center.x-diameter*.5f,center.y-diameter*.5f,diameter,diameter),navigationThumb);
        string caption=navigationHoldProgress>0?"切替…":navigationLooking?"見回し":oneHandNavigation?"前後・旋回":"移動";
        if(navigationCaption==null)navigationCaption=new GUIStyle(compactLight){fontSize=11,alignment=TextAnchor.MiddleCenter};
        var label=new Rect(pad.center.x-42,pad.yMax-23,84,18);
        GUI.color=new Color(0,.06f,.08f,.65f);GUI.Label(new Rect(label.x,label.y+1,label.width,label.height),caption,navigationCaption);
        GUI.color=new Color(1,1,1,.85f);GUI.Label(label,caption,navigationCaption);
        if(oneHandNavigation && !CompactLandscape)
        {
            GUI.color=new Color(1,1,1,.85f);
            GUI.Label(new Rect(pad.x-4,pad.y-20,pad.width+8,18),navigationLooking?"中央で待つと歩行":"中央長押しで見回し",navigationCaption);
        }
        GUI.color=old;
    }

    void ReleaseTouchNavigation()
    {
        if(navigationBase)Destroy(navigationBase);
        if(navigationThumb)Destroy(navigationThumb);
        if(navigationDirection)Destroy(navigationDirection);
    }
}
