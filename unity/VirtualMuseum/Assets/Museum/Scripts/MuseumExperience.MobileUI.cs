using UnityEngine;

// The compact interface uses the canvas' CSS dimensions, not its high-DPI
// backing buffer. All actions remain reachable without a hardware keyboard.
public partial class MuseumExperience
{
    bool compactMenuOpen;
    Vector2 compactListScroll, compactGuideScroll, compactHelpScroll, compactMenuScroll;
    bool compactScrollActive;
    Rect compactScrollViewport;
    Vector2 compactScrollOffset;
    GUIStyle compactTitle, compactBody, compactSmall, compactLight, compactButton, compactPrimary;
    const float CompactHeaderHeight=56;

    bool CompactUI => TouchControlsVisible || Screen.width/Mathf.Max(.1f,WebViewportScale)<900 ||
        Screen.width/(float)Mathf.Max(1,Screen.height)<1.1f;
    float UiScale => CompactUI ? Mathf.Max(.1f,WebViewportScale) : Mathf.Min(Screen.width/1440f,Screen.height/810f);
    float CompactWidth => Screen.width/UiScale;
    float CompactHeight => Screen.height/UiScale;
    bool CompactLandscape => CompactWidth>CompactHeight*1.2f;
    float CompactDockHeight => touring?(CompactLandscape?60:132):mode=="walk"?100:(CompactLandscape?60:112);
    float CompactDockTop => CompactHeight-CompactDockHeight;
    bool TouchWorldInputBlocked => backyardOpen || guidePreparing || listOpen || helpOpen || answer!="" || compactMenuOpen;
    bool CompactNavigationVisible => TouchControlsVisible && !TouchWorldInputBlocked && !touring &&
        mode=="walk" && !ImmersionTransitioning;
    Rect TouchNavigationRect
    {
        get {float size=CompactLandscape?Mathf.Clamp(CompactDockTop-CompactHeaderHeight-16,64,112):112;
            return new Rect(navigationOnRight?CompactWidth-size-12:12,CompactDockTop-size-8,size,size);}
    }
    Rect CompactReadyRect
    {
        get {bool pad=CompactLandscape && TouchControlsVisible;
            float left=pad && !navigationOnRight?TouchNavigationRect.xMax+12:12;
            float right=BackyardButtonVisible?180:pad && navigationOnRight?TouchNavigationRect.width+24:12;
            return new Rect(left,CompactHeaderHeight+8,CompactWidth-left-right,48);}
    }
    Rect CompactObservationRect
    {
        get
        {
            float available=Mathf.Max(32,CompactDockTop-CompactHeaderHeight-36);
            float size=Mathf.Min(CompactWidth-24,available);
            return new Rect((CompactWidth-size)/2,CompactHeaderHeight+30+(available-size)/2,size,size);
        }
    }

    Vector2 GuiPoint(Vector2 screen)
    {
        float scale=UiScale;
        float offset=CompactUI?0:(Screen.width-1440*scale)/2;
        return new Vector2((screen.x-offset)/scale,(Screen.height-screen.y)/scale);
    }

    bool CompactOverUI(Vector2 screen)
    {
        if(TouchWorldInputBlocked) return true;
        Vector2 point=GuiPoint(screen);
        if(BackyardButtonVisible && BackyardButtonRect.Contains(point))return true;
        if(point.y<CompactHeaderHeight || point.y>=CompactDockTop) return true;
        if(RoomStatusVisible && RoomStatusRect.Contains(point))return true;
        if(mode!="walk" && (detailLoading || detailFailed) && DetailStatusRect.Contains(point))return true;
        if(CompactNavigationVisible && TouchNavigationContains(point)) return true;
        return mode=="walk" && !touring && !ImmersionActive && ReadyInteraction && CompactReadyRect.Contains(point);
    }

    void SetupCompactStyles()
    {
        if(compactTitle!=null) return;
        compactTitle=new GUIStyle(titleStyle){fontSize=18,alignment=TextAnchor.MiddleLeft};
        compactBody=new GUIStyle(bodyStyle){fontSize=16};
        compactSmall=new GUIStyle(smallStyle){fontSize=13};
        compactLight=new GUIStyle(compactBody);compactLight.normal.textColor=new Color(.95f,.96f,.91f);
        compactButton=new GUIStyle(buttonStyle){fontSize=15,alignment=TextAnchor.MiddleCenter,padding=new RectOffset(7,7,5,5)};
        compactPrimary=new GUIStyle(compactButton);compactPrimary.normal.background=accent;compactPrimary.normal.textColor=Color.white;
    }

    bool CompactButton(Rect rect,string text,bool primary=false)
    {
        bool clicked=GUI.Button(rect,text,primary?compactPrimary:compactButton);
        if(!GUI.enabled) return false;
        if(!IgnoreGameplayMouse) return clicked;
        if(compactScrollActive)
        {
            rect.position+=compactScrollViewport.position-compactScrollOffset;
            rect=Rect.MinMaxRect(Mathf.Max(rect.xMin,compactScrollViewport.xMin),Mathf.Max(rect.yMin,compactScrollViewport.yMin),
                Mathf.Min(rect.xMax,compactScrollViewport.xMax),Mathf.Min(rect.yMax,compactScrollViewport.yMax));
            if(rect.width<=0 || rect.height<=0) return false;
        }
        return TouchButton(rect);
    }

    void DrawCompactUI()
    {
        SetupCompactStyles();uiWidth=CompactWidth;uiHeight=CompactHeight;
        Matrix4x4 previousMatrix=GUI.matrix;
        GUI.matrix=Matrix4x4.Scale(new Vector3(UiScale,UiScale,1));
        DrawCompactObservation();
        bool baseEnabled=GUI.enabled;
        // IMGUI draws back-to-front but handles input in call order. Disable the
        // covered controls so a tap on a sheet cannot activate a hidden button.
        GUI.enabled=baseEnabled && !TouchWorldInputBlocked;
        DrawDetailStatus();
        GUI.DrawTexture(new Rect(0,0,uiWidth,CompactHeaderHeight),dark);
        bool observation=mode!="walk";
        if(observation && !touring)
        {
            if(CompactButton(new Rect(8,6,70,44),"戻る")) {CloseObservation();compactMenuOpen=false;}
            GUI.Label(new Rect(88,8,Mathf.Max(80,uiWidth-174),40),mode=="scope"?"顕微鏡で観察":names[selected],compactLight);
        }
        else GUI.Label(new Rect(12,6,uiWidth-92,44),touring && CompactLandscape?
            (tourStep+1)+" / 6  "+tourTitles[tourStep]:"収蔵庫を、探検しよう。",compactLight);
        if(CompactButton(new Rect(uiWidth-78,6,70,44),"使い方"))
        {helpOpen=!helpOpen;compactMenuOpen=false;listOpen=false;walking=false;}

        if(!touring && mode=="walk" && !ImmersionActive && !TouchWorldInputBlocked && ReadyInteraction)
        {
            if(CompactButton(CompactReadyRect,nearbyMicroscope?"この顕微鏡をのぞく":names[nearbyExhibit.index]+" を観察",true))
            {if(nearbyMicroscope) Microscope(nearbyMicroscope);else if(nearbyExhibit) Observe(nearbyExhibit.index);}
        }
        if(CompactNavigationVisible) DrawTouchNavigation();
        if(touring) {GUI.enabled=baseEnabled;DrawCompactTourDock();}
        else if(mode=="walk") DrawCompactWalkDock();
        else DrawCompactObservationDock();
        GUI.enabled=baseEnabled;

        // A single sheet can cover the scene, while the tour's transport remains
        // below it. The same modal state also excludes world input.
        if(helpOpen) DrawCompactHelp();
        else if(listOpen && !touring) DrawCompactDestinations();
        else if(compactMenuOpen && !touring) DrawCompactMenu();
        else if(answer!="") DrawCompactGuide();
        DrawBackyard();
        GUI.matrix=previousMatrix;
    }

    void DrawCompactWalkDock()
    {
        float top=CompactDockTop;
        GUI.DrawTexture(new Rect(0,top,uiWidth,CompactDockHeight),dark);
        GUI.Label(new Rect(12,top+5,uiWidth-24,31),(selected+1).ToString("00")+"  "+names[selected],compactLight);
        float width=(uiWidth-32)/3;
        bool enabled=GUI.enabled;GUI.enabled=enabled && !ImmersionTransitioning;
        if(CompactButton(new Rect(8,top+40,width,48),"標本を見る",true))
        {compactMenuOpen=false;helpOpen=false;Observe(selected);}
        GUI.enabled=enabled;
        if(CompactButton(new Rect(16+width,top+40,width,48),listOpen?"一覧を閉じる":"移動"))
        {listOpen=!listOpen;compactMenuOpen=false;helpOpen=false;answer="";walking=false;compactListScroll=Vector2.zero;}
        if(CompactButton(new Rect(24+width*2,top+40,width,48),compactMenuOpen?"閉じる":"メニュー"))
        {compactMenuOpen=!compactMenuOpen;listOpen=false;helpOpen=false;answer="";walking=false;compactMenuScroll=Vector2.zero;}
    }

    void DrawCompactObservationDock()
    {
        float top=CompactDockTop,half=(uiWidth-24)/2;
        GUI.DrawTexture(new Rect(0,top,uiWidth,CompactDockHeight),dark);
        bool enabled=GUI.enabled;GUI.enabled=enabled && !ImmersionTransitioning;
        if(CompactLandscape)
        {
            float usable=uiWidth-48,x=8,switchWidth=usable*.31f,resetWidth=usable*.20f,zoomWidth=usable*.16f;
            if(CompactButton(new Rect(x,top+8,switchWidth,44),mode=="scope"?"標本に戻る":"顕微鏡で見る",true))
            {if(mode=="scope")mode="observe";else Microscope();}
            x+=switchWidth+8;
            if(CompactButton(new Rect(x,top+8,resetWidth,44),"リセット"))ResetView();
            x+=resetWidth+8;
            if(CompactButton(new Rect(x,top+8,zoomWidth,44),"−"))
            {if(mode=="scope")scopeZoom=Mathf.Max(1,scopeZoom-.5f);else zoom=Mathf.Max(.55f,zoom-.15f);}
            x+=zoomWidth+8;
            GUI.Label(new Rect(x,top+14,usable*.17f,32),(mode=="scope"?scopeZoom:zoom).ToString("0.0")+" ×",compactLight);
            x+=usable*.17f+8;
            if(CompactButton(new Rect(x,top+8,zoomWidth,44),"＋"))
            {if(mode=="scope")scopeZoom=Mathf.Min(8,scopeZoom+.5f);else zoom=Mathf.Min(2.5f,zoom+.15f);}
            if(held)held.transform.localScale=Vector3.one*zoom;
            GUI.enabled=enabled;return;
        }
        if(CompactButton(new Rect(8,top+8,half,44),mode=="scope"?"標本に戻る":"顕微鏡で見る",true))
        {if(mode=="scope") mode="observe";else Microscope();}
        if(CompactButton(new Rect(16+half,top+8,half,44),"リセット")) ResetView();
        float centre=(uiWidth-16)/3;
        if(CompactButton(new Rect(8,top+60,centre-4,44),"− 縮小"))
        {if(mode=="scope")scopeZoom=Mathf.Max(1,scopeZoom-.5f);else zoom=Mathf.Max(.55f,zoom-.15f);}
        GUI.Label(new Rect(8+centre,top+66,centre,32),(mode=="scope"?scopeZoom:zoom).ToString("0.0")+" ×",compactLight);
        if(CompactButton(new Rect(12+centre*2,top+60,centre-4,44),"＋ 拡大"))
        {if(mode=="scope")scopeZoom=Mathf.Min(8,scopeZoom+.5f);else zoom=Mathf.Min(2.5f,zoom+.15f);}
        if(held)held.transform.localScale=Vector3.one*zoom;
        GUI.enabled=enabled;
    }

    void DrawCompactTourDock()
    {
        float top=CompactDockTop;
        GUI.DrawTexture(new Rect(0,top,uiWidth,CompactDockHeight),dark);
        if(!CompactLandscape)GUI.Label(new Rect(12,top+3,uiWidth-24,28),(tourStep+1)+" / 6  "+tourTitles[tourStep],compactLight);
        float width=CompactLandscape?(uiWidth-40)/4:(uiWidth-32)/3;
        float row=top+(CompactLandscape?8:34);
        if(CompactButton(new Rect(8,row,width,44),tourPaused?"再開":"一時停止",true))tourPaused=!tourPaused;
        if(CompactButton(new Rect(16+width,row,width,44),"次へ"))AdvanceTour();
        if(CompactButton(new Rect(24+width*2,row,width,44),"見学を終了"))StopTour();
        Rect loopRect=CompactLandscape?new Rect(32+width*3,row,width,44):new Rect(8,top+84,uiWidth-16,44);
        if(CompactButton(loopRect,tourLoop?"繰り返し：ON":"繰り返し：OFF"))tourLoop=!tourLoop;
        GUI.DrawTexture(new Rect(0,top,uiWidth*Mathf.Clamp01(tourElapsed/tourDurations[tourStep]),3),accent);
    }

    void DrawCompactObservation()
    {
        if(!immersionActive) return;
        Color previous=GUI.color;
        float blend=Mathf.SmoothStep(0,1,Mathf.InverseLerp(.16f,1,immersionProgress));
        GUI.color=new Color(previous.r,previous.g,previous.b,previous.a*blend);
        GUI.DrawTexture(new Rect(0,CompactHeaderHeight,uiWidth,CompactDockTop-CompactHeaderHeight),dark);
        Rect full=CompactObservationRect;
        Vector2 origin=new Vector2(focusViewport.x*uiWidth,(1-focusViewport.y)*uiHeight);
        Rect view=new Rect(Mathf.Lerp(origin.x-40,full.x,blend),Mathf.Lerp(origin.y-40,full.y,blend),
            Mathf.Lerp(80,full.width,blend),Mathf.Lerp(80,full.height,blend));
        GUI.DrawTexture(view,specimenView,ScaleMode.ScaleToFit,true);
        float lens=Mathf.SmoothStep(0,1,microscopeBlend);
        if(lens>0)
        {
            ClampPan();float extent=1/scopeZoom;
            GUI.color=new Color(previous.r,previous.g,previous.b,previous.a*blend*lens);
            GUI.DrawTextureWithTexCoords(view,ScopeImage(selected),new Rect(scopePan.x-extent/2,scopePan.y-extent/2,extent,extent));
            GUI.DrawTexture(view,microscopeVignette);
        }
        GUI.color=new Color(previous.r,previous.g,previous.b,previous.a*blend);
        GUI.Label(new Rect(12,CompactHeaderHeight+2,uiWidth-24,28),microscopeBlend>.5f?
            "模式図・仮倍率 / 指で観察位置を移動":"3D模型 / 指で回転・2本指で拡大",compactLight);
        GUI.color=previous;
    }

    Rect CompactPanel(string heading,out bool close)
    {
        float bottom=touring?CompactDockTop-8:uiHeight-8;
        float top=CompactLandscape?8:CompactHeaderHeight+8;
        Rect rect=new Rect(8,top,uiWidth-16,bottom-top);
        GUI.DrawTexture(rect,panel);
        GUI.Label(new Rect(rect.x+12,rect.y+5,rect.width-94,44),heading,compactTitle);
        close=CompactButton(new Rect(rect.xMax-70,rect.y+5,62,44),"閉じる");
        return new Rect(rect.x+12,rect.y+58,rect.width-24,Mathf.Max(44,rect.height-70));
    }

    void BeginCompactScroll(Rect area,float contentHeight,ref Vector2 scroll)
    {
        bool overflow=contentHeight>area.height;
        float height=Mathf.Max(24,area.height-(overflow?52:0));
        scroll.y=Mathf.Clamp(scroll.y,0,Mathf.Max(0,contentHeight-height));
        compactScrollViewport=new Rect(area.x,area.y,area.width,height);
        scroll=GUI.BeginScrollView(compactScrollViewport,scroll,
            new Rect(0,0,area.width-20,contentHeight),false,overflow);
        compactScrollOffset=scroll;compactScrollActive=true;
    }

    void EndCompactScroll(Rect area,float contentHeight,ref Vector2 scroll)
    {
        GUI.EndScrollView();compactScrollActive=false;
        if(contentHeight<=area.height) return;
        float width=(area.width-8)/2,step=Mathf.Max(44,area.height-64);
        if(CompactButton(new Rect(area.x,area.yMax-44,width,44),"上へ")) scroll.y=Mathf.Max(0,scroll.y-step);
        if(CompactButton(new Rect(area.x+width+8,area.yMax-44,width,44),"下へ")) scroll.y=Mathf.Min(contentHeight-area.height+52,scroll.y+step);
    }

    void DrawCompactDestinations()
    {
        Rect area=CompactPanel("目的地へ移動",out bool close);
        if(close)listOpen=false;
        float height=(RoomSpecimenCount+2)*62;
        BeginCompactScroll(area,height,ref compactListScroll);
        for(int i=0;i<RoomSpecimenCount+2;i++)
            if(CompactButton(new Rect(0,i*62,area.width-20,52),ListDestinationLabel(i)))Jump(ListDestination(i));
        EndCompactScroll(area,height,ref compactListScroll);
    }

    void DrawCompactMenu()
    {
        Rect area=CompactPanel("見学メニュー",out bool close);
        if(close)compactMenuOpen=false;
        float width=area.width-20;
        string padHelp="片手：上下で前後、左右で旋回。斜めで歩きながら曲がります。中央を0.6秒長押しで見回しへ。中央へ戻して待つと歩行へ戻ります。指を離すと停止します。\n両手：パッドで移動し、もう1本の指で景色をドラッグ。片手モードでも2本目の指で見回せます。";
        float textHeight=compactSmall.CalcHeight(new GUIContent(padHelp),width);
        float height=324+textHeight;
        BeginCompactScroll(area,height,ref compactMenuScroll);
        if(CompactButton(new Rect(0,0,width,52),"アイモナイト君の解説",true))
        {compactMenuOpen=false;compactGuideScroll=Vector2.zero;Talk();}
        if(CompactButton(new Rect(0,62,width,52),"自動見学をはじめる"))
        {compactMenuOpen=false;StartTour();}
        if(CompactButton(new Rect(0,124,width,52),"操作ガイド"))
        {compactMenuOpen=false;helpOpen=true;compactHelpScroll=Vector2.zero;}
        if(CompactButton(new Rect(0,186,width,52),oneHandNavigation?"操作：片手（前後＋旋回）":"操作：両手（移動＋スワイプ）"))SetOneHandNavigation(!oneHandNavigation);
        if(CompactButton(new Rect(0,248,width,52),navigationOnRight?"パッド位置：右":"パッド位置：左"))SetNavigationSide(!navigationOnRight);
        GUI.Label(new Rect(0,312,width,textHeight),padHelp,compactSmall);
        EndCompactScroll(area,height,ref compactMenuScroll);
    }

    void DrawCompactGuide() { DrawGuideBubble(); }

    void DrawCompactHelp()
    {
        Rect area=CompactPanel("探検のしかた",out bool close);
        if(close)helpOpen=false;
        float width=area.width-20;
        string instructions="歩く\n片手モードではパッドの上下で前後、左右で旋回、斜めで歩きながら曲がれます。中央を0.6秒長押しすると移動を止めて上下左右を見回せます。中央へ戻して待つと歩行へ。指を離すと停止します。「メニュー」で両手モードやパッドの左右を選べます。通路の床をタップして歩くこともできます。\n\n見回す\n展示室を1本指でドラッグします。\n\n観察する\n展示や光るサインをタップ。「標本を見る」からも開けます。模型は1本指で回転、2本指のピンチで拡大・縮小。＋／−ボタンも使えます。\n\n顕微鏡\n「顕微鏡で見る」を選びます。拡大後は1本指で観察位置を動かせます。上の「戻る」で展示室へ。\n\nすぐに移動・自動見学\n「移動」から目的地へ。「メニュー」から解説や自動見学を開きます。\n\nPCでは十字キー / WASD、右ドラッグ、ホイール、E / Escも使えます。\n\n標本と拡大図は試作用です。質問は用意された選択肢から選びます。";
        float height=compactBody.CalcHeight(new GUIContent(instructions),width)+12;
        BeginCompactScroll(area,height,ref compactHelpScroll);
        GUI.Label(new Rect(0,0,width,height),instructions,compactBody);
        EndCompactScroll(area,height,ref compactHelpScroll);
    }
}
