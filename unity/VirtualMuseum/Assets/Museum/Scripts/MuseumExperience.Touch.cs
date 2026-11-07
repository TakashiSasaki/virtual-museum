using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.EnhancedTouch;
using Touch = UnityEngine.InputSystem.EnhancedTouch.Touch;
using TouchPhase = UnityEngine.InputSystem.TouchPhase;

public partial class MuseumExperience
{
    [Serializable] class WebViewport { public float width, height; public bool touch; }
    enum FingerUse { Ignored, Walk, World, UI }
    sealed class Gesture
    {
        public FingerUse use;
        public Vector2 origin, previous;
        public string mode;
        public string panel;
        public bool dragged;
        public bool padLook,holdArmed=true;
        public float centerHeld;
    }
    readonly Dictionary<int, Gesture> gestures = new();
    WebViewport webViewport;
    bool touchSeen, externalOverlay;
    float suppressMouseUntil;
    Vector2 touchMovement;
    int pinchA=-1, pinchB=-1;
    float previousPinch;
    bool enhancedTouchOwned;
    Vector2 uiTapStart, uiTapEnd;
    int uiTapFrame=-1;
    string PanelIdentity => mode+"|"+listOpen+"|"+helpOpen+"|"+compactMenuOpen+"|"+(answer!="")+"|"+touring;

    bool TouchButton(Rect rect)
    {
        if(!GUI.enabled || Event.current.type!=EventType.Repaint || uiTapFrame!=Time.frameCount ||
            !rect.Contains(uiTapStart) || !rect.Contains(uiTapEnd)) return false;
        uiTapFrame=-1;return true;
    }

    float WebViewportScale => webViewport!=null && webViewport.width>0
        ? Screen.width/webViewport.width : 1f;
    bool TouchControlsVisible => touchSeen || (webViewport!=null && webViewport.touch) || Application.isMobilePlatform;
    public bool UsesTouchControls => TouchControlsVisible;
    bool IgnoreGameplayMouse => Time.unscaledTime<suppressMouseUntil;

    // Host sends CSS pixels, not render-buffer pixels: high-DPI phones must
    // retain finger-sized controls even when WebGL renders at a different DPR.
    public void SetWebViewport(string json)
    {
        var viewport=JsonUtility.FromJson<WebViewport>(json);
        if(viewport==null || viewport.width<1 || viewport.height<1) return;
        if(webViewport!=null && (Mathf.Abs(viewport.width-webViewport.width)>1 || Mathf.Abs(viewport.height-webViewport.height)>1)) CancelTouchGestures();
        webViewport=viewport;
    }

    public void SetWebOverlay(string value)
    {
        externalOverlay=value=="1";
        if(externalOverlay) {walking=false;CancelTouchGestures();}
    }

    void OnEnable()
    {
        EnhancedTouchSupport.Enable();enhancedTouchOwned=true;
        oneHandNavigation=PlayerPrefs.GetInt("Museum.OneHandNavigation",1)!=0;
        navigationOnRight=PlayerPrefs.GetInt("Museum.NavigationOnRight",0)!=0;
    }

    void OnApplicationFocus(bool focused)
    {
        if(!focused) {CancelArrivalTurn();walking=false;CancelTouchGestures();}
    }

    void CancelTouchGestures()
    {
        foreach(var gesture in gestures.Values) gesture.use=FingerUse.Ignored;
        touchMovement=Vector2.zero;navigationDeflection=Vector2.zero;navigationLooking=false;navigationHoldProgress=0;pinchA=pinchB=-1;previousPinch=0;uiTapFrame=-1;
    }

    void UpdateTouchInput()
    {
        touchMovement=Vector2.zero;navigationDeflection=Vector2.zero;navigationLooking=false;navigationHoldProgress=0;
        var touches=Touch.activeTouches;
        if(touches.Count==0) {gestures.Clear();pinchA=pinchB=-1;return;}
        touchSeen=true;suppressMouseUntil=Time.unscaledTime+.45f;
        bool blocked=externalOverlay || TouchWorldInputBlocked || touring || ImmersionTransitioning;
        int worldCount=0;Gesture padGesture=null;Vector2 padInput=Vector2.zero;
        Touch first=default, second=default;
        foreach(var touch in touches)
        {
            int id=touch.touchId;
            Vector2 position=touch.screenPosition;
            if(touch.phase==TouchPhase.Began)
            {
                var use=FingerUse.Ignored;
                if(!externalOverlay)
                {
                    if(!blocked && mode=="walk" && !ImmersionActive && TouchNavigationContains(GuiPoint(position)))
                    {
                        bool padOwned=false;foreach(var existing in gestures.Values)if(existing.use==FingerUse.Walk)padOwned=true;
                        use=padOwned?FingerUse.Ignored:FingerUse.Walk;
                    }
                    else if(OverUI(position)) use=FingerUse.UI;
                    else if(!blocked) use=FingerUse.World;
                }
                gestures[id]=new Gesture {use=use,origin=position,previous=position,mode=mode,panel=PanelIdentity};
                if(use==FingerUse.Walk) walking=false;
            }
            if(!gestures.TryGetValue(id,out var gesture)) continue;
            if(externalOverlay || gesture.mode!=mode || (gesture.use==FingerUse.UI ? gesture.panel!=PanelIdentity : blocked)) gesture.use=FingerUse.Ignored;
            if((position-gesture.origin).magnitude/WebViewportScale>9) gesture.dragged=true;
            bool ended=touch.phase==TouchPhase.Ended || touch.phase==TouchPhase.Canceled;
            if(ended)
            {
                if(touch.phase==TouchPhase.Ended && gesture.use==FingerUse.World && gesture.dragged && pinchA==-1)
                {
                    bool otherWorld=false;
                    foreach(var entry in gestures) if(entry.Key!=id && entry.Value.use==FingerUse.World) otherWorld=true;
                    if(!otherWorld) ApplyWorldDrag((position-gesture.previous)/WebViewportScale);
                }
                if(touch.phase==TouchPhase.Ended && gesture.use==FingerUse.World && !gesture.dragged && mode=="walk" && !OverUI(position)) ActivateWorldPoint(position);
                else if(touch.phase==TouchPhase.Ended && gesture.use==FingerUse.UI && !gesture.dragged)
                {uiTapStart=GuiPoint(gesture.origin);uiTapEnd=GuiPoint(position);uiTapFrame=Time.frameCount;}
                gestures.Remove(id);continue;
            }
            if(gesture.use==FingerUse.Walk)
            {
                Vector2 offset=GuiPoint(position)-TouchNavigationRect.center;
                padGesture=gesture;
                padInput=Vector2.ClampMagnitude(new Vector2(offset.x,-offset.y)/(TouchNavigationRect.width*.35f),1);
            }
            else if(gesture.use==FingerUse.World)
            {
                if(worldCount==0) first=touch;else if(worldCount==1) second=touch;
                worldCount++;
            }
        }
        if(padGesture!=null)ProcessNavigationPad(padInput,padGesture,worldCount>0);
        if(worldCount>=2)
        {
            foreach(var gesture in gestures.Values) if(gesture.use==FingerUse.World) gesture.dragged=true;
            float distance=Vector2.Distance(first.screenPosition,second.screenPosition);
            bool same=pinchA==first.touchId && pinchB==second.touchId;
            if(same && previousPinch>1 && distance>1)
            {
                float ratio=distance/previousPinch;
                if(mode=="observe" && held) {zoom=Mathf.Clamp(zoom*ratio,.55f,2.5f);held.transform.localScale=Vector3.one*zoom;}
                else if(mode=="scope") {scopeZoom=Mathf.Clamp(scopeZoom*ratio,1,8);ClampPan();}
            }
            pinchA=first.touchId;pinchB=second.touchId;previousPinch=distance;
        }
        else
        {
            // Lifting one finger after pinching must not jump or dispatch a tap.
            bool wasPinching=pinchA!=-1;pinchA=pinchB=-1;
            if(worldCount==1 && !wasPinching && gestures.TryGetValue(first.touchId,out var gesture) && gesture.dragged)
            {
                ApplyWorldDrag((first.screenPosition-gesture.previous)/WebViewportScale);
            }
        }
        foreach(var touch in touches) if(gestures.TryGetValue(touch.touchId,out var gesture)) gesture.previous=touch.screenPosition;
    }

    void ApplyWorldDrag(Vector2 delta)
    {
        if(mode=="walk"){CancelArrivalTurn();selectionPinned=false;}
        if(mode=="walk") {walking=false;yaw-=delta.x*.18f;pitch=Mathf.Clamp(pitch+delta.y*.18f,-60,60);}
        else if(mode=="observe" && held) {held.transform.Rotate(Vector3.up,-delta.x*.45f,Space.World);held.transform.Rotate(Vector3.right,delta.y*.45f,Space.World);}
        else if(mode=="scope") {scopePan-=delta/Mathf.Max(100,CompactObservationRect.width)/scopeZoom;ClampPan();}
    }

    void ActivateWorldPoint(Vector2 position)
    {
        CancelArrivalTurn();selectionPinned=false;
        Ray ray=visitorCamera.ScreenPointToRay(position);
        if(wayfinding && wayfinding.TryActivate(ray)) return;
        if(!Physics.Raycast(ray,out var hit,40)) return;
        var exhibit=hit.collider.GetComponentInParent<MuseumExhibit>();
        if(exhibit) Observe(exhibit.index);
        else if(hit.collider.GetComponentInParent<MicroscopeStation>() is MicroscopeStation station) Microscope(station);
        else if(hit.collider.name=="Walkable floor" || hit.collider.name=="Work area floor" || hit.collider.name=="Aisle marker" || hit.collider.name=="Metal floor strip") {walkTarget=hit.point;walkTarget.y=visitor.transform.position.y;walking=true;}
        else if(hit.collider.GetComponentInParent<GuideMarker>()) Talk();
    }

}
