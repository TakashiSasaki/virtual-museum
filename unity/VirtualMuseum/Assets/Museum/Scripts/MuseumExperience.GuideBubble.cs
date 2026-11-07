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
        float width=wide?Mathf.Min(420,uiWidth*.6f):Mathf.Min(420,uiWidth-24);
        float top=CompactUI?(wide?8:64):108;
        float bottom=CompactUI?CompactDockTop-8:uiHeight-108;
        const float menuHeight=210;
        if(CompactUI && bottom-top<menuHeight)bottom=uiHeight-8;
        float height=guideMenu?menuHeight:Mathf.Min(360,bottom-top);
        var marker=guide?guide.GetComponent<GuideMarker>():null;
        Vector3 screen=visitorCamera.WorldToScreenPoint(marker?GuideSpeechPoint():visitorCamera.transform.position+visitorCamera.transform.forward*2);
        Vector2 anchor=GuiPoint(screen);
        float x=wide?(anchor.x<uiWidth*.5f?uiWidth-width-12:12):Mathf.Clamp(anchor.x-width*.5f,12,uiWidth-width-12);
        float y=wide?Mathf.Clamp(anchor.y-height*.5f,top,Mathf.Max(top,bottom-height)):Mathf.Clamp(anchor.y-height-28,top,Mathf.Max(top,bottom-height));
        var rect=new Rect(x,y,width,height);
        if(!guideTail)
        {
            guideTail=new Texture2D(32,32,TextureFormat.RGBA32,false){name="Guide speech tail",hideFlags=HideFlags.HideAndDontSave};
            var pixels=new Color[1024];for(int yy=0;yy<32;yy++)for(int xx=0;xx<32;xx++)pixels[yy*32+xx]=new Color(1,1,1,Mathf.Clamp01((yy/31f-Mathf.Abs((xx+.5f)/16-1))*32));
            guideTail.SetPixels(pixels);guideTail.Apply(false,true);
        }
        var previous=GUI.color;
        var previousBackground=GUI.backgroundColor;
        GUI.backgroundColor=new Color(1,1,1,.55f);
        Vector2 tailBase=new Vector2(Mathf.Clamp(anchor.x,rect.x+20,rect.xMax-20),Mathf.Clamp(anchor.y,rect.y+16,rect.yMax-16));
        if(anchor.y>rect.yMax)tailBase.y=rect.yMax-2;
        else if(anchor.y<rect.y)tailBase.y=rect.y+2;
        else tailBase.x=anchor.x>rect.center.x?rect.xMax-2:rect.x+2;
        var direction=anchor-tailBase;float length=Mathf.Min(60,direction.magnitude);
        var center=tailBase+direction.normalized*length*.5f;
        GUI.color=new Color(.96f,.97f,.91f,.84f);var matrix=GUI.matrix;
        GUIUtility.RotateAroundPivot(Mathf.Atan2(-direction.x,direction.y)*Mathf.Rad2Deg,center);
        GUI.DrawTexture(new Rect(center.x-14,center.y-length*.5f,28,length),guideTail);
        GUI.matrix=matrix;GUI.color=Color.white;
        GUI.DrawTexture(new Rect(x+2,y+4,width,height),Texture2D.whiteTexture,ScaleMode.StretchToFill,true,0,new Color(0,.08f,.09f,.12f),0,18);
        GUI.DrawTexture(rect,Texture2D.whiteTexture,ScaleMode.StretchToFill,true,0,new Color(.96f,.97f,.91f,.84f),0,18);
        GUI.Label(new Rect(x+16,y+10,width-100,32),"アイモナイト君",compactTitle);
        if(CompactButton(new Rect(rect.xMax-76,y+7,64,36),"閉じる")){CloseGuideConversation();GUI.color=previous;GUI.backgroundColor=previousBackground;return;}
        var area=new Rect(x+14,y+52,width-28,height-66);
        if(guideMenu)
        {
            GUI.Label(new Rect(area.x,area.y,area.width,28),"何を知りたいですか？",compactBody);
            string[] choices={"この展示の解説","本物の標本？","顕微鏡の解説","操作を教えて"};
            float buttonWidth=(area.width-8)/2;
            for(int i=0;i<choices.Length;i++)if(CompactButton(new Rect(area.x+(i%2)*(buttonWidth+8),area.y+34+(i/2)*54,buttonWidth,48),choices[i]))
            {if(i==0)answer=descriptions[selected];else Ask(i-1);guideMenu=false;guideBubbleScroll=Vector2.zero;}
        }
        else
        {
            var textArea=new Rect(area.x,area.y,area.width,area.height-52);
            float textHeight=compactBody.CalcHeight(new GUIContent(answer),textArea.width-20)+12;
            BeginCompactScroll(textArea,textHeight,ref guideBubbleScroll);
            GUI.Label(new Rect(0,0,textArea.width-20,textHeight),answer,compactBody);
            EndCompactScroll(textArea,textHeight,ref guideBubbleScroll);
            if(CompactButton(new Rect(area.x,area.yMax-44,area.width,44),"ほかの質問を選ぶ",true))
            {guideMenu=true;answer="何を知りたいですか？";guideBubbleScroll=Vector2.zero;}
        }
        GUI.color=previous;
        GUI.backgroundColor=previousBackground;
    }
}
