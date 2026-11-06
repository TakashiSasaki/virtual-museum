using UnityEngine;
using UnityEngine.InputSystem;

public partial class MuseumExperience : MonoBehaviour
{
    public Camera visitorCamera;
    public CharacterController visitor;
    public Transform guide;
    public GameObject[] specimenModels;
    public Transform[] destinations;
    public Camera specimenCamera;
    public Transform specimenStage;
    public RenderTexture specimenView;
    public Font japaneseFont;

    public int selected;
    public string mode = "walk";
    public bool touring, tourPaused, tourLoop;
    public int tourStep;
    public float tourElapsed;
    public bool tourMoving;
    public string answer = "";
    public int moves, observations, microscopeVisits, questions;
    public int runtimeFrames;

    readonly string[] names = { "コガネムシのかたち", "チョウの翅を見よう", "アンモナイトの渦" };
    readonly string[] english = { "BEETLE / FORM", "BUTTERFLY / PATTERN", "AMMONITE / SPIRAL" };
    readonly string[] descriptions = {
        "硬い前翅と、左右に並ぶ脚に注目してみよう。\nこの模型は操作確認用に形を単純化したダミー標本です。実在の種を再現したものではありません。",
        "左右に広がる翅の形と模様を、向きを変えて見てみよう。\n翅の模様と色は仮設定です。顕微鏡では鱗粉をイメージした模式図を用意しました。",
        "外側へ向かって広がる渦巻きを、表と裏から見てみよう。\nこれは渦の形を試すためのダミー模型です。化石の内部構造を正確に再現していません。"
    };
    readonly string[] tourTitles = { "収蔵庫へようこそ", "01  標本を手に取る", "02  回して、比べてみよう", "03  顕微鏡で観察", "04  アイモナイト君に聞く", "自由に探検してみよう" };
    readonly float[] tourDurations = { 7, 7, 10, 12, 10, 7 };
    GameObject held;
    MuseumWayfinding wayfinding;
    Quaternion initialRotation;
    float yaw, pitch, zoom=1, scopeZoom=1;
    Vector2 scopePan = new Vector2(.5f,.5f);
    Vector3 walkTarget;
    bool walking, listOpen, helpOpen;
    Vector3[] tourRoute;
    int routePoint, tourDestination;
    float npcPhase;
    Texture2D[] scopeTextures;
    Texture2D panel, dark, accent, pale;
    GUIStyle titleStyle, subtitleStyle, bodyStyle, smallStyle, buttonStyle, primaryStyle, darkTextStyle;
    float uiWidth=1440, uiHeight=900;
    string notice="光るサインをクリックして観察。近づいて対象を見ると E キーでも操作できます。";

    void Start()
    {
        Application.runInBackground=true;
        visitorCamera.nearClipPlane=.06f;
        yaw=visitor.transform.eulerAngles.y;
        if(!japaneseFont) japaneseFont=Font.CreateDynamicFontFromOSFont(new[]{"Yu Gothic","Meiryo","Arial"},20);
        scopeTextures = new Texture2D[3];
        for(int i=0;i<3;i++) scopeTextures[i]=MakeScope(i);
        specimenCamera.targetTexture=specimenView;
        specimenCamera.gameObject.SetActive(false);
        SetupImmersion();
        wayfinding=FindAnyObjectByType<MuseumWayfinding>();
    }

    void Update()
    {
        runtimeFrames++;
        var mouse=Mouse.current; var keys=Keyboard.current;
        if(keys!=null && keys.escapeKey.wasPressedThisFrame) {
            if(touring) StopTour(); else if(mode!="walk") CloseObservation(); else { listOpen=false; helpOpen=false; answer=""; }
        }
        UpdateImmersion();
        UpdateNearbyInteraction(keys);
        if(touring) {
            if(!tourPaused) {
                if(tourMoving) { if(!ImmersionActive) UpdateTourTravel(); }
                else if(!ImmersionTransitioning) {
                    tourElapsed+=Time.deltaTime;
                    if(mode=="observe" && held) held.transform.Rotate(Vector3.up,20*Time.deltaTime,Space.World);
                    if(tourElapsed>=tourDurations[tourStep]) AdvanceTour();
                }
            }
        } else if(mode=="walk" && !ImmersionActive && answer=="" && !helpOpen) {
            float x=0,z=0;
            if(keys!=null) {
                x=(keys.rightArrowKey.isPressed||keys.dKey.isPressed?1:0)-(keys.leftArrowKey.isPressed||keys.aKey.isPressed?1:0);
                z=(keys.upArrowKey.isPressed||keys.wKey.isPressed?1:0)-(keys.downArrowKey.isPressed||keys.sKey.isPressed?1:0);
            }
            if(mouse!=null && !OverUI(mouse.position.ReadValue())) {
                if(mouse.rightButton.isPressed) {
                    Vector2 delta=mouse.delta.ReadValue(); yaw+=delta.x*.13f; pitch=Mathf.Clamp(pitch-delta.y*.13f,-60,60);
                }
                if(mouse.leftButton.wasPressedThisFrame) {
                    Ray ray=visitorCamera.ScreenPointToRay(mouse.position.ReadValue());
                    bool usedSign=wayfinding && wayfinding.TryActivate(ray);
                    if(!usedSign && Physics.Raycast(ray,out var hit,40)) {
                        var exhibit=hit.collider.GetComponentInParent<MuseumExhibit>();
                        if(exhibit) Observe(exhibit.index);
                        else if(hit.collider.GetComponentInParent<MicroscopeStation>() is MicroscopeStation station) Microscope(station);
                        else if(hit.collider.name=="Walkable floor" || hit.collider.name=="Work area floor" || hit.collider.name=="Aisle marker" || hit.collider.name=="Metal floor strip") {walkTarget=hit.point;walkTarget.y=visitor.transform.position.y;walking=true;}
                        else if(hit.collider.GetComponentInParent<GuideMarker>()) Talk();
                    }
                }
            }
            if(!ImmersionActive) {
                visitor.transform.rotation=Quaternion.Euler(0,yaw,0);visitorCamera.transform.localRotation=Quaternion.Euler(pitch,0,0);
                var move=Vector3.ClampMagnitude(visitor.transform.right*x+visitor.transform.forward*z,1);
                if(move.sqrMagnitude>0) walking=false;
                if(walking) {
                    var delta=walkTarget-visitor.transform.position;delta.y=0;
                    if(delta.magnitude<.15f) walking=false; else move=delta.normalized;
                }
                Vector3 before=visitor.transform.position;
                visitor.Move((move*2.4f+Vector3.down*2)*Time.deltaTime);
                if(walking && move.sqrMagnitude>0 && (visitor.transform.position-before).sqrMagnitude<.000001f) {walking=false;notice="障害物があります。通路の床を選ぶか、展示一覧を使ってください。";}
            }
        }
        if(mouse!=null && !touring && !ImmersionTransitioning && (mode=="observe"||mode=="scope") && !OverUI(mouse.position.ReadValue())) {
            Vector2 delta=mouse.delta.ReadValue();float scroll=mouse.scroll.ReadValue().y;
            if(mode=="observe" && held) {
                if(mouse.leftButton.isPressed) {held.transform.Rotate(Vector3.up,-delta.x*.35f,Space.World);held.transform.Rotate(Vector3.right,delta.y*.35f,Space.World);}
                if(scroll!=0) zoom=Mathf.Clamp(zoom+Mathf.Sign(scroll)*.12f,.55f,2.5f);
                held.transform.localScale=Vector3.one*zoom;
            } else {
                if(scroll!=0) scopeZoom=Mathf.Clamp(scopeZoom+Mathf.Sign(scroll)*.5f,1,8);
                if(mouse.leftButton.isPressed) scopePan+=new Vector2(-delta.x,-delta.y)/650/scopeZoom;
                ClampPan();
            }
        }
        if(guide && answer=="" && mode=="walk" && !touring) {
            npcPhase+=Time.deltaTime*.18f;
            Vector3 target=new Vector3(.25f+Mathf.Sin(npcPhase)*1.1f,0,6+Mathf.Cos(npcPhase)*2.0f);
            Vector3 away=target-visitor.transform.position;away.y=0;
            if(away.magnitude<1.25f) target+=away.normalized*(1.25f-away.magnitude);
            target.x=Mathf.Clamp(target.x,-2.0f,1.4f);
            Vector3 delta=target-guide.position;delta.y=0;
            if(delta.magnitude>.02f) guide.rotation=Quaternion.Slerp(guide.rotation,Quaternion.LookRotation(delta),Time.deltaTime*3);
            guide.position=Vector3.MoveTowards(guide.position,target,Time.deltaTime*.65f);
        } else if(guide) {
            Vector3 delta=visitor.transform.position-guide.position;delta.y=0;
            if(delta.sqrMagnitude>.01f) guide.rotation=Quaternion.Slerp(guide.rotation,Quaternion.LookRotation(delta),Time.deltaTime*3);
        }
    }

    bool OverUI(Vector2 screen)
    {
        float s=Mathf.Min(Screen.width/1440f,Screen.height/810f);float offset=(Screen.width-1440*s)/2;
        Vector2 p=new Vector2((screen.x-offset)/s,(Screen.height-screen.y)/s);
        return p.y<105 || p.y>uiHeight-100 || p.x>uiWidth-375 || (listOpen && p.x<350) || helpOpen || answer!="";
    }
    public void Jump(int index)
    {
        CloseObservationImmediately();answer="";walking=false;
        visitor.enabled=false; visitor.transform.position=destinations[index].position; visitor.transform.rotation=destinations[index].rotation; visitor.enabled=true;
        yaw=visitor.transform.eulerAngles.y;pitch=0;visitorCamera.transform.localRotation=Quaternion.identity;
        if(index<3) selected=index;
        moves++;listOpen=false;notice=index<3?names[index]+" の前に移動しました。":"目的地に移動しました。";
    }
    public void Observe(int index)
    {
        if(specimenModels==null || index<0 || index>=specimenModels.Length) return;
        selected=index;walking=false;answer="";listOpen=false;mode="observe";
        PrepareHeldSpecimen(index);
        BeginImmersion(ExhibitFocus(index));
        observations++;
    }
    public void Microscope() { Microscope(null); }
    public void Microscope(MicroscopeStation station)
    {
        if(!held) { PrepareHeldSpecimen(selected); observations++; }
        walking=false;answer="";listOpen=false;mode="scope";
        observedMicroscope=ResolveMicroscope(station);
        BeginImmersion(observedMicroscope?InteractionPoint(observedMicroscope):ExhibitFocus(selected));
        scopeZoom=1;scopePan=new Vector2(.5f,.5f);microscopeVisits++;
    }
    public void CloseObservation()
    {
        mode="walk";walking=false;
        if(!ImmersionActive) ReleaseHeldSpecimen();
    }
    public void Talk() {
        walking=false;answer=descriptions[selected];
        if(guide) RecordExperience(guide.GetComponent<GuideMarker>());
    }
    public void Ask(int index)
    {
        questions++;
        answer=index==0?"これは本物の標本？\n\n今はプロトタイプなので、形を単純化したダミー標本を展示しています。将来、実物の資料や監修済みの説明に差し替える予定です。":
        index==1?"顕微鏡では何が見える？\n\nこの版では拡大と移動の操作を試すための模式図が見られます。実際の顕微鏡写真ではなく、表示倍率も操作用の仮倍率です。":
        "どうやって観察する？\n\n「手に取る」で標本を開き、左ドラッグで回転、ホイールで拡大します。「顕微鏡で見る」で模式図に切り替えられます。Escで戻れます。";
    }
    public void StartTour() { touring=true;tourPaused=false;tourStep=0;listOpen=false;helpOpen=false;if(guide)guide.position=new Vector3(-1.8f,0,11.6f);Jump(4);ApplyTourStep(); }
    public void AdvanceTour()
    {
        tourStep++;
        if(tourStep>=tourDurations.Length) {if(tourLoop) tourStep=0;else {StopTour();notice="自動見学が終了しました。自由に展示をお楽しみください。";return;}}
        ApplyTourStep();
    }
    void ApplyTourStep()
    {
        tourElapsed=0;CloseObservation();answer="";
        tourDestination=new[]{4,0,1,3,2,4}[tourStep];
        Vector3 p=visitor.transform.position,goal=destinations[tourDestination].position;
        tourRoute=new[]{new Vector3(0,p.y,p.z),new Vector3(0,p.y,goal.z),new Vector3(goal.x,p.y,goal.z)};
        routePoint=0;tourMoving=true;
    }
    void UpdateTourTravel()
    {
        Vector3 delta=tourRoute[routePoint]-visitor.transform.position;delta.y=0;
        if(delta.magnitude<.12f) {
            routePoint++;
            if(routePoint==tourRoute.Length) {
                tourMoving=false;yaw=destinations[tourDestination].eulerAngles.y;pitch=0;
                visitor.transform.rotation=Quaternion.Euler(0,yaw,0);visitorCamera.transform.localRotation=Quaternion.identity;
                if(tourDestination<3)selected=tourDestination;
                if(tourStep==2)Observe(1);
                if(tourStep==3){Observe(1);Microscope();scopeZoom=3;}
                if(tourStep==4)Talk();
            }
            return;
        }
        visitor.Move((delta.normalized*1.8f+Vector3.down*2)*Time.deltaTime);
        visitor.transform.rotation=Quaternion.Slerp(visitor.transform.rotation,Quaternion.LookRotation(delta),Time.deltaTime*2);
        visitorCamera.transform.localRotation=Quaternion.Slerp(visitorCamera.transform.localRotation,Quaternion.identity,Time.deltaTime*2);
    }
    public void StopTour() {touring=false;tourPaused=false;tourMoving=false;CloseObservationImmediately();answer="";walking=false;yaw=visitor.transform.eulerAngles.y;}
    void ClampPan() {float r=.5f/scopeZoom;scopePan.x=Mathf.Clamp(scopePan.x,r,1-r);scopePan.y=Mathf.Clamp(scopePan.y,r,1-r);}
    void ResetView() {zoom=1;if(held) {held.transform.localRotation=initialRotation;held.transform.localScale=Vector3.one;}scopeZoom=1;scopePan=new Vector2(.5f,.5f);}

    void SetupStyles()
    {
        if(panel) return;
        panel=Solid(new Color(.96f,.95f,.91f,.98f));dark=Solid(new Color(.035f,.12f,.13f,.97f));accent=Solid(new Color(.08f,.36f,.31f));pale=Solid(new Color(.86f,.89f,.84f));
        titleStyle=new GUIStyle(GUI.skin.label){font=japaneseFont,fontSize=30,fontStyle=FontStyle.Bold,wordWrap=true};titleStyle.normal.textColor=new Color(.1f,.22f,.21f);
        subtitleStyle=new GUIStyle(titleStyle){fontSize=15,fontStyle=FontStyle.Normal};subtitleStyle.normal.textColor=new Color(.67f,.77f,.69f);
        bodyStyle=new GUIStyle(titleStyle){fontSize=19,fontStyle=FontStyle.Normal};
        smallStyle=new GUIStyle(bodyStyle){fontSize=15};smallStyle.normal.textColor=new Color(.35f,.43f,.40f);
        buttonStyle=new GUIStyle(GUI.skin.button){font=japaneseFont,fontSize=18,alignment=TextAnchor.MiddleLeft,padding=new RectOffset(18,12,8,8),wordWrap=true};
        buttonStyle.normal.background=pale;buttonStyle.normal.textColor=titleStyle.normal.textColor;buttonStyle.hover.background=panel;buttonStyle.hover.textColor=titleStyle.normal.textColor;buttonStyle.active.background=accent;
        primaryStyle=new GUIStyle(buttonStyle);primaryStyle.normal.background=accent;primaryStyle.normal.textColor=Color.white;
        darkTextStyle=new GUIStyle(bodyStyle);darkTextStyle.normal.textColor=new Color(.96f,.95f,.89f);
    }
    bool Button(float x,float y,float w,string label,bool primary=false,float h=46)
    { return GUI.Button(new Rect(x,y,w,h),label,primary?primaryStyle:buttonStyle); }
    void Label(float x,float y,float w,float h,string text,GUIStyle style=null) {GUI.Label(new Rect(x,y,w,h),text,style??bodyStyle);}
    void OnGUI()
    {
        SetupStyles();float scale=Mathf.Min(Screen.width/1440f,Screen.height/810f);uiWidth=1440;uiHeight=Screen.height/scale;
        GUI.matrix=Matrix4x4.TRS(new Vector3((Screen.width-1440*scale)/2,0,0),Quaternion.identity,new Vector3(scale,scale,1));
        GUI.DrawTexture(new Rect(0,0,1440,96),dark);
        Label(30,14,750,26,"EHIME UNIVERSITY MUSEUM  /  VIRTUAL COLLECTION",subtitleStyle);
        Label(30,39,850,46,"収蔵庫を、探検しよう。",darkTextStyle);
        Label(1090,20,325,28,"PROTOTYPE 01  ·  ダミー展示",subtitleStyle);
        if(Button(1260,53,150,"操作ガイド",false,32)) {helpOpen=!helpOpen;walking=false;}

        DrawImmersiveObservation();
        DrawNearbyPrompt();

        GUI.DrawTexture(new Rect(1065,108,355,uiHeight-220),panel);
        float rx=1085;
        Label(rx,126,310,25,"COLLECTION  /  0"+(selected+1),smallStyle);
        Label(rx,160,310,88,names[selected],titleStyle);
        Label(rx,246,310,25,english[selected],smallStyle);
        Label(rx,287,310,110,mode=="scope"?"拡大資料：操作確認用の模式図\n実際の顕微鏡写真ではありません。": "標本の形を、いろいろな角度から。\nこの展示はダミー標本です。",bodyStyle);
        float by=410;
        if(!touring) {
            bool controlsEnabled=GUI.enabled;
            GUI.enabled=controlsEnabled && !ImmersionTransitioning;
            if(mode=="walk") {
                if(Button(rx,by,310,"標本を手に取る",true)) Observe(selected);
                if(Button(rx,by+58,310,"この展示へ移動")) Jump(selected);
                if(Button(rx,by+116,310,"アイモナイト君の解説")) Talk();
            } else {
                if(Button(rx,by,310,mode=="scope"?"標本に戻る":"顕微鏡で見る",true)) {if(mode=="scope")mode="observe";else Microscope();}
                if(Button(rx,by+58,96,"−")) {if(mode=="scope")scopeZoom=Mathf.Max(1,scopeZoom-.5f);else zoom=Mathf.Max(.55f,zoom-.15f);}
                Label(rx+104,by+65,105,32,(mode=="scope"?scopeZoom:zoom).ToString("0.0")+" ×");
                if(Button(rx+214,by+58,96,"＋")) {if(mode=="scope")scopeZoom=Mathf.Min(8,scopeZoom+.5f);else zoom=Mathf.Min(2.5f,zoom+.15f);}
                if(Button(rx,by+116,310,"向き・倍率をリセット")) ResetView();
                if(Button(rx,by+174,310,"標本を戻して展示室へ")) CloseObservation();
                if(held)held.transform.localScale=Vector3.one*zoom;
            }
            GUI.enabled=controlsEnabled;
        } else Label(rx,by,310,180,"自動見学中です。\n\n下のボタンで一時停止、次の展示への移動、自由見学への切り替えができます。",bodyStyle);

        if(listOpen && !touring) {
            GUI.DrawTexture(new Rect(20,110,330,410),panel);Label(40,130,290,45,"どこへ行きますか？",bodyStyle);
            for(int i=0;i<5;i++) if(Button(36,185+i*61,297,i<3?"0"+(i+1)+"  "+names[i]:i==3?"観察台・顕微鏡":"入口・全体を見渡す")) Jump(i);
        }
        GUI.DrawTexture(new Rect(0,uiHeight-96,1440,96),dark);
        if(!touring) {
            if(Button(24,uiHeight-75,200,listOpen?"展示一覧を閉じる":"展示一覧・移動",true)) {listOpen=!listOpen;walking=false;}
            if(Button(238,uiHeight-75,200,"自動見学をはじめる")) StartTour();
            Label(467,uiHeight-76,940,26,"移動：↑↓←→ / WASD / 床クリック　　視点：右ドラッグ　　観察：E　戻る：Esc",subtitleStyle);
            Label(467,uiHeight-43,940,26,notice,subtitleStyle);
        } else {
            if(Button(24,uiHeight-75,150,tourPaused?"再開":"一時停止",true)) tourPaused=!tourPaused;
            if(Button(186,uiHeight-75,130,"次へ")) AdvanceTour();
            if(Button(328,uiHeight-75,175,"自由見学に戻る")) StopTour();
            if(Button(515,uiHeight-75,180,tourLoop?"繰り返し：ON":"繰り返し：OFF"))tourLoop=!tourLoop;
            Label(725,uiHeight-78,690,30,(tourStep+1)+" / 6   "+tourTitles[tourStep],darkTextStyle);
            GUI.DrawTexture(new Rect(730,uiHeight-31,650*Mathf.Clamp01(tourElapsed/tourDurations[tourStep]),4),accent);
        }
        if(answer!="") {
            GUI.DrawTexture(new Rect(100,150,900,uiHeight-275),panel);
            Label(132,177,820,40,"アイモナイト君の展示ガイド",titleStyle);
            Label(132,239,830,175,answer,bodyStyle);
            Label(132,uiHeight-335,800,25,"よくある質問（用意した回答を表示します）",smallStyle);
            if(!touring) {
                for(int i=0;i<3;i++) if(Button(132+i*277,uiHeight-295,264,new[]{"本物の標本？","顕微鏡で何が見える？","操作を教えて"}[i])) Ask(i);
                if(Button(132,uiHeight-225,820,"会話を閉じる",true))answer="";
            }
        }
        if(helpOpen) {
            GUI.DrawTexture(new Rect(220,140,980,uiHeight-260),panel);
            Label(260,174,900,55,"探検のしかた",titleStyle);
            Label(260,250,890,300,"01  歩く：十字キー / WASD、または通路の床をクリック\n02  見回す：右ボタンを押しながらマウスを動かす\n03  観察する：展示標本をクリック、または「標本を手に取る」\n04  回す・拡大する：左ドラッグ / マウスホイール\n05  すぐ移動する：「展示一覧・移動」から目的地を選ぶ\n06  自動見学：操作なしのデモ。途中から自由見学もできます。\n\n標本・拡大図・キャラクターは試作用です。自由入力のAI回答はありません。",bodyStyle);
            if(Button(260,uiHeight-205,900,"展示室へ戻る",true))helpOpen=false;
        }
    }
    static Texture2D Solid(Color c) {var t=new Texture2D(1,1);t.SetPixel(0,0,c);t.Apply();return t;}
    static Texture2D MakeScope(int kind)
    {
        var t=new Texture2D(512,512);var colors=new Color[512*512];
        for(int y=0;y<512;y++) for(int x=0;x<512;x++) {
            float v;
            if(kind==0) {float xx=(x+(y/34%2)*18)%36-18,yy=y%34-17;v=Mathf.Clamp01(1-Mathf.Sqrt(xx*xx+yy*yy)/22);colors[y*512+x]=Color.Lerp(new Color(.04f,.10f,.08f),new Color(.56f,.73f,.35f),v);}
            else if(kind==1) {float xx=(x+(y/58%2)*16)%34-17,yy=y%58;v=Mathf.Clamp01(1-Mathf.Abs(xx)/17)*(.45f+.55f*yy/58);colors[y*512+x]=Color.Lerp(new Color(.15f,.10f,.12f),new Color(.96f,.60f,.23f),v);}
            else {float dx=x-256,dy=y-256;v=.5f+.5f*Mathf.Sin(Mathf.Sqrt(dx*dx+dy*dy)*.13f+Mathf.Atan2(dy,dx)*6);colors[y*512+x]=Color.Lerp(new Color(.22f,.14f,.10f),new Color(.85f,.72f,.46f),v);}
        }
        t.SetPixels(colors);t.Apply();return t;
    }
}
