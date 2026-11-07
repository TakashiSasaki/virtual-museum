using UnityEngine;

public partial class MuseumExperience
{
    bool guidePreparing, guideMenu;
    float guideTurnElapsed,guideStartYaw,guideStartPitch;
    Quaternion guideStartRotation;
    Texture2D guideTail;
    Vector2 guideBubbleScroll;
    Renderer guideFace;
    Vector3 GuideSpeechPoint()
    {
        if(!guideFace && guide)foreach(var renderer in guide.GetComponentsInChildren<Renderer>())if(renderer.name.StartsWith("Face")){guideFace=renderer;break;}
        return guideFace && (!(guideFace is SkinnedMeshRenderer skin) || skin.sharedMesh)?guideFace.bounds.center:InteractionPoint(guide.GetComponent<GuideMarker>());
    }

    void BeginGuideConversation()
    {
        if(!guide || guidePreparing || answer!="")return;
        PrioritizeRoom(guide);
        CancelArrivalTurn();CancelTouchGestures();walking=false;listOpen=helpOpen=compactMenuOpen=false;
        guidePreparing=true;guideMenu=true;guideTurnElapsed=0;guideBubbleScroll=Vector2.zero;
        guideStartRotation=guide.rotation;guideStartYaw=yaw;guideStartPitch=pitch;
    }
    void CloseGuideConversation()
    {
        guidePreparing=false;answer="";guideBubbleScroll=Vector2.zero;CancelTouchGestures();
    }
    void UpdateGuideConversation()
    {
        if(!guidePreparing)return;
        if(!guide || mode!="walk"){CloseGuideConversation();return;}
        if(externalOverlay || (touring && tourPaused))return;
        guideTurnElapsed+=Time.unscaledDeltaTime;
        float t=Mathf.SmoothStep(0,1,Mathf.Clamp01(guideTurnElapsed/.85f));
        var delta=visitorCamera.transform.position-guide.position;delta.y=0;
        if(delta.sqrMagnitude>.001f)guide.rotation=Quaternion.Slerp(guideStartRotation,Quaternion.LookRotation(delta),t);
        var marker=guide.GetComponent<GuideMarker>();
        if(marker && !ImmersionActive)
        {
            var view=GuideSpeechPoint()-visitorCamera.transform.position;
            float targetYaw=Mathf.Atan2(view.x,view.z)*Mathf.Rad2Deg;
            float targetPitch=Mathf.Clamp(-Mathf.Atan2(view.y,new Vector2(view.x,view.z).magnitude)*Mathf.Rad2Deg,-60,60);
            yaw=Mathf.LerpAngle(guideStartYaw,targetYaw,t);pitch=Mathf.LerpAngle(guideStartPitch,targetPitch,t);
            visitor.transform.rotation=Quaternion.Euler(0,yaw,0);visitorCamera.transform.localRotation=Quaternion.Euler(pitch,0,0);
        }
        if(t>=1){guidePreparing=false;answer="こんにちは！ アイモナイトです。何を知りたいですか？";RecordExperience(marker);}
    }
    void DrawGuideBubble()
    {
        SetupCompactStyles();
        bool wide=uiWidth>uiHeight*1.2f;
        float width=wide?Mathf.Min(420,uiWidth*.45f):Mathf.Min(420,uiWidth-24),top=CompactUI?64:108,bottom=CompactUI?CompactDockTop-8:uiHeight-108;
        float height=Mathf.Min(360,bottom-top);
        var marker=guide?guide.GetComponent<GuideMarker>():null;
        Vector3 screen=visitorCamera.WorldToScreenPoint(marker?GuideSpeechPoint():visitorCamera.transform.position+visitorCamera.transform.forward*2);
        Vector2 anchor=GuiPoint(screen);
        float x=wide?(anchor.x<uiWidth*.5f?uiWidth-width-12:12):Mathf.Clamp(anchor.x-width*.5f,12,uiWidth-width-12);
        if(!wide)height=Mathf.Min(height,Mathf.Max(200,anchor.y-top-28));
        float y=wide?Mathf.Clamp(anchor.y-height*.5f,top,Mathf.Max(top,bottom-height)):Mathf.Clamp(anchor.y-height-28,top,Mathf.Max(top,bottom-height));
        var rect=new Rect(x,y,width,height);
        if(!guideTail)
        {
            guideTail=new Texture2D(32,32,TextureFormat.RGBA32,false){name="Guide speech tail",hideFlags=HideFlags.HideAndDontSave};
            var pixels=new Color[1024];for(int yy=0;yy<32;yy++)for(int xx=0;xx<32;xx++)pixels[yy*32+xx]=new Color(1,1,1,Mathf.Clamp01((yy/31f-Mathf.Abs((xx+.5f)/16-1))*32));
            guideTail.SetPixels(pixels);guideTail.Apply(false,true);
        }
        var previous=GUI.color;
        Vector2 tailBase=new Vector2(Mathf.Clamp(anchor.x,rect.x+20,rect.xMax-20),Mathf.Clamp(anchor.y,rect.y+16,rect.yMax-16));
        if(anchor.y>rect.yMax)tailBase.y=rect.yMax-2;
        else if(anchor.y<rect.y)tailBase.y=rect.y+2;
        else tailBase.x=anchor.x>rect.center.x?rect.xMax-2:rect.x+2;
        var direction=anchor-tailBase;float length=Mathf.Min(60,direction.magnitude);
        var center=tailBase+direction.normalized*length*.5f;
        GUI.color=new Color(.96f,.97f,.91f,.98f);var matrix=GUI.matrix;
        GUIUtility.RotateAroundPivot(Mathf.Atan2(-direction.x,direction.y)*Mathf.Rad2Deg,center);
        GUI.DrawTexture(new Rect(center.x-14,center.y-length*.5f,28,length),guideTail);
        GUI.matrix=matrix;GUI.color=Color.white;
        GUI.DrawTexture(new Rect(x+2,y+4,width,height),Texture2D.whiteTexture,ScaleMode.StretchToFill,true,0,new Color(0,.08f,.09f,.22f),0,18);
        GUI.DrawTexture(rect,Texture2D.whiteTexture,ScaleMode.StretchToFill,true,0,new Color(.96f,.97f,.91f,.98f),0,18);
        GUI.Label(new Rect(x+16,y+10,width-100,32),"アイモナイト君",compactTitle);
        if(CompactButton(new Rect(rect.xMax-76,y+7,64,36),"閉じる")){CloseGuideConversation();GUI.color=previous;return;}
        var area=new Rect(x+14,y+52,width-28,height-66);
        float textHeight=compactBody.CalcHeight(new GUIContent(answer),area.width-20)+12;
        float contentHeight=textHeight+(guideMenu?184:54);
        BeginCompactScroll(area,contentHeight,ref guideBubbleScroll);
        GUI.Label(new Rect(0,0,area.width-20,textHeight),answer,compactBody);
        if(guideMenu)
        {
            string[] choices={"この展示の解説","本物の標本？","顕微鏡で何が見える？","操作を教えて"};
            for(int i=0;i<choices.Length;i++)if(CompactButton(new Rect(0,textHeight+i*46,area.width-20,40),choices[i],i==0))
            {if(i==0)answer=descriptions[selected];else Ask(i-1);guideMenu=false;guideBubbleScroll=Vector2.zero;}
        }
        else if(CompactButton(new Rect(0,textHeight,area.width-20,44),"ほかの質問を選ぶ",true))
        {guideMenu=true;answer="何を知りたいですか？";guideBubbleScroll=Vector2.zero;}
        EndCompactScroll(area,contentHeight,ref guideBubbleScroll);GUI.color=previous;
    }
}
