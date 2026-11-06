using UnityEngine;
using UnityEngine.InputSystem;
using System.Collections.Generic;

// Observation keeps the visitor in the room: the camera leans toward the
// selected object, then its image expands into the inspection view. Returning
// reverses that move without changing the visitor's walking position.
public partial class MuseumExperience
{
    const float EnterObservationSeconds=.9f;
    const float LeaveObservationSeconds=.65f;
    const float ChangeLensSeconds=.5f;
    MuseumExhibit[] roomExhibits;
    MicroscopeStation[] roomMicroscopes;
    MuseumExhibit nearbyExhibit;
    MicroscopeStation nearbyMicroscope;
    MuseumExhibit observedExhibit;
    MicroscopeStation observedMicroscope;
    // One visit/session: navigation and repeated observations keep this history.
    // A new Play session starts with unexperienced locations.
    readonly HashSet<Component> experiencedInteractions = new();
    bool immersionActive;
    float immersionProgress, microscopeBlend;
    Vector3 restingCameraPosition, focusedCameraPosition;
    Quaternion restingCameraRotation, focusedCameraRotation;
    float restingFieldOfView;
    Vector2 focusViewport=new Vector2(.5f,.5f);
    Texture2D microscopeVignette;

    public bool WayfindingVisible => mode=="walk" && !immersionActive &&
        answer=="" && !listOpen && !helpOpen && !touring;
    public Component ReadyInteraction => nearbyMicroscope ? (Component)nearbyMicroscope : nearbyExhibit;
    public bool HasExperienced(Component target) => target && experiencedInteractions.Contains(target);

    void RecordExperience(Component target)
    {
        if(target) experiencedInteractions.Add(target);
    }

    bool ImmersionActive => immersionActive;
    bool ImmersionTransitioning => immersionActive &&
        (mode=="walk" || immersionProgress<1f ||
         Mathf.Abs(microscopeBlend-(mode=="scope"?1f:0f))>.001f);

    void SetupImmersion()
    {
        roomExhibits=FindObjectsByType<MuseumExhibit>();
        roomMicroscopes=FindObjectsByType<MicroscopeStation>();
        // Transparent centre, soft dark rim: a lens-like field of view, not a
        // rectangular image pasted over the specimen. This is a runtime asset.
        const int size=256;
        microscopeVignette=new Texture2D(size,size,TextureFormat.RGBA32,false);
        microscopeVignette.name="Microscope soft field of view";
        microscopeVignette.wrapMode=TextureWrapMode.Clamp;
        var pixels=new Color[size*size];
        for(int y=0;y<size;y++) for(int x=0;x<size;x++) {
            float radius=new Vector2((x+.5f)/size-.5f,(y+.5f)/size-.5f).magnitude;
            float rim=Mathf.SmoothStep(0,1,Mathf.InverseLerp(.425f,.49f,radius));
            pixels[y*size+x]=new Color(.035f,.12f,.13f,rim);
        }
        microscopeVignette.SetPixels(pixels);microscopeVignette.Apply();
    }

    void PrepareHeldSpecimen(int index)
    {
        zoom=1;
        if(held) Destroy(held);
        held=Instantiate(specimenModels[index],specimenStage);
        held.transform.localPosition=Vector3.zero;
        held.transform.localRotation=Quaternion.Euler(-20,0,0);
        held.transform.localScale=Vector3.one;
        initialRotation=held.transform.localRotation;
        specimenCamera.gameObject.SetActive(true);
        observedExhibit=FindExhibit(index);
    }

    void ReleaseHeldSpecimen()
    {
        if(held) Destroy(held);
        held=null;
        observedExhibit=null;observedMicroscope=null;
        if(specimenCamera) specimenCamera.gameObject.SetActive(false);
    }

    MuseumExhibit FindExhibit(int index)
    {
        if(roomExhibits!=null) foreach(var exhibit in roomExhibits)
            if(exhibit && exhibit.index==index) return exhibit;
        return null;
    }

    Vector3 ExhibitFocus(int index)
    {
        var exhibit=FindExhibit(index);
        if(exhibit) return InteractionPoint(exhibit);
        return visitorCamera.transform.position+visitorCamera.transform.forward*2;
    }

    MicroscopeStation ResolveMicroscope(MicroscopeStation preferred)
    {
        if(preferred) return preferred;
        MicroscopeStation nearest=null;float distance=float.PositiveInfinity;
        if(roomMicroscopes!=null) foreach(var station in roomMicroscopes) {
            if(!station) continue;
            float d=(station.transform.position-visitor.transform.position).sqrMagnitude;
            if(d<distance) {distance=d;nearest=station;}
        }
        return nearest;
    }

    static Vector3 InteractionPoint(Component component)
    {
        var collider=component.GetComponent<Collider>();
        return collider?collider.bounds.center:component.transform.position;
    }

    void BeginImmersion(Vector3 point)
    {
        if(immersionActive) return;
        immersionActive=true;immersionProgress=0;microscopeBlend=mode=="scope"?1:0;
        nearbyExhibit=null;nearbyMicroscope=null;
        var cameraTransform=visitorCamera.transform;
        restingCameraPosition=cameraTransform.localPosition;
        restingCameraRotation=cameraTransform.localRotation;
        restingFieldOfView=visitorCamera.fieldOfView;
        Vector3 viewport=visitorCamera.WorldToViewportPoint(point);
        focusViewport=viewport.z>0?new Vector2(Mathf.Clamp01(viewport.x),Mathf.Clamp01(viewport.y)):new Vector2(.5f,.5f);
        Vector3 delta=point-cameraTransform.position;
        Vector3 direction=delta.sqrMagnitude>.001f?delta.normalized:cameraTransform.forward;
        // A small lean is safe from any part of the room. It is deliberately
        // not an unbounded camera flight through furniture to a distant item.
        float distance=Mathf.Min(.55f,Mathf.Max(0,delta.magnitude-.5f));
        if(Physics.SphereCast(cameraTransform.position,.1f,direction,out var hit,distance,~0,QueryTriggerInteraction.Ignore))
            distance=Mathf.Max(0,hit.distance-.06f);
        Vector3 focusPosition=cameraTransform.position+direction*distance;
        Quaternion focusRotation=Quaternion.RotateTowards(cameraTransform.rotation,
            Quaternion.LookRotation(direction,Vector3.up),55);
        var parent=cameraTransform.parent;
        focusedCameraPosition=parent?parent.InverseTransformPoint(focusPosition):focusPosition;
        focusedCameraRotation=parent?Quaternion.Inverse(parent.rotation)*focusRotation:focusRotation;
    }

    void UpdateImmersion()
    {
        if(!immersionActive || (touring && tourPaused)) return;
        bool closing=mode=="walk";
        float duration=closing?LeaveObservationSeconds:EnterObservationSeconds;
        immersionProgress=Mathf.MoveTowards(immersionProgress,closing?0:1,Time.unscaledDeltaTime/duration);
        // Preserve the last image while closing, so it shrinks back into the
        // room instead of abruptly changing from microscope to specimen.
        if(!closing) microscopeBlend=Mathf.MoveTowards(microscopeBlend,mode=="scope"?1:0,Time.unscaledDeltaTime/ChangeLensSeconds);
        float cameraBlend=Mathf.SmoothStep(0,1,immersionProgress);
        visitorCamera.transform.localPosition=Vector3.Lerp(restingCameraPosition,focusedCameraPosition,cameraBlend);
        visitorCamera.transform.localRotation=Quaternion.Slerp(restingCameraRotation,focusedCameraRotation,cameraBlend);
        visitorCamera.fieldOfView=Mathf.Lerp(restingFieldOfView,43,cameraBlend);
        // Credit the view that actually finished opening, including lens
        // changes inside immersion. Preparing a hidden specimen is not a visit.
        if(!closing && immersionProgress>=1f) {
            if(mode=="observe" && microscopeBlend<=.001f) RecordExperience(observedExhibit);
            else if(mode=="scope" && microscopeBlend>=.999f) RecordExperience(observedMicroscope);
        }
        if(closing && immersionProgress<=0) CloseObservationImmediately();
    }

    void CloseObservationImmediately()
    {
        if(immersionActive && visitorCamera) {
            visitorCamera.transform.localPosition=restingCameraPosition;
            visitorCamera.transform.localRotation=restingCameraRotation;
            visitorCamera.fieldOfView=restingFieldOfView;
        }
        immersionActive=false;immersionProgress=0;microscopeBlend=0;
        mode="walk";walking=false;
        ReleaseHeldSpecimen();
    }

    void UpdateNearbyInteraction(Keyboard keys)
    {
        nearbyExhibit=null;nearbyMicroscope=null;
        if(touring || mode!="walk" || immersionActive || answer!="" || listOpen || helpOpen) return;
        float best=2.7f;
        if(roomExhibits!=null) foreach(var exhibit in roomExhibits) {
            if(!exhibit) continue;
            float score=InteractionScore(exhibit);
            if(score<best) {best=score;nearbyExhibit=exhibit;}
        }
        if(roomMicroscopes!=null) foreach(var station in roomMicroscopes) {
            if(!station) continue;
            float score=InteractionScore(station);
            if(score<best) {best=score;nearbyMicroscope=station;nearbyExhibit=null;}
        }
        if(nearbyExhibit) selected=nearbyExhibit.index;
        if(keys!=null && keys.eKey.wasPressedThisFrame) {
            if(nearbyMicroscope) Microscope(nearbyMicroscope);
            else if(nearbyExhibit) Observe(nearbyExhibit.index);
        }
    }

    float InteractionScore(Component target)
    {
        Vector3 delta=InteractionPoint(target)-visitorCamera.transform.position;
        float distance=delta.magnitude;
        if(distance>.001f && Vector3.Dot(visitorCamera.transform.forward,delta/distance)>.45f) {
            if(!Physics.Linecast(visitorCamera.transform.position,InteractionPoint(target),out var hit,~0,QueryTriggerInteraction.Ignore)
                || hit.collider.transform.IsChildOf(target.transform))
                return distance;
        }
        return float.PositiveInfinity;
    }

    void DrawNearbyPrompt()
    {
        if(!nearbyExhibit && !nearbyMicroscope) return;
        GUI.DrawTexture(new Rect(280,uiHeight-180,500,62),dark);
        Label(302,uiHeight-164,456,34,nearbyMicroscope?"E / クリックで、顕微鏡をのぞく":"E / クリックで、標本を手に取る",darkTextStyle);
    }

    void DrawImmersiveObservation()
    {
        if(!immersionActive) return;
        Color previous=GUI.color;
        // The room remains visible during the initial lean. Then the selected
        // object grows into the view, rather than switching screens instantly.
        float blend=Mathf.SmoothStep(0,1,Mathf.InverseLerp(.16f,1,immersionProgress));
        GUI.color=new Color(previous.r,previous.g,previous.b,previous.a*blend);
        GUI.DrawTexture(new Rect(0,96,1060,uiHeight-196),dark);
        float size=Mathf.Min(810,uiHeight-235);
        Rect full=new Rect((1060-size)/2,112,size,size);
        float originX=Mathf.Clamp(focusViewport.x*uiWidth,120,940);
        float originY=Mathf.Clamp((1-focusViewport.y)*uiHeight,200,uiHeight-200);
        Rect origin=new Rect(originX-80,originY-80,160,160);
        Rect view=new Rect(Mathf.Lerp(origin.x,full.x,blend),Mathf.Lerp(origin.y,full.y,blend),
            Mathf.Lerp(origin.width,full.width,blend),Mathf.Lerp(origin.height,full.height,blend));
        GUI.DrawTexture(view,specimenView,ScaleMode.ScaleToFit,true);
        float lens=Mathf.SmoothStep(0,1,microscopeBlend);
        if(lens>0) {
            ClampPan();float extent=1/scopeZoom;
            GUI.color=new Color(previous.r,previous.g,previous.b,previous.a*blend*lens);
            GUI.DrawTextureWithTexCoords(view,scopeTextures[selected],new Rect(scopePan.x-extent/2,scopePan.y-extent/2,extent,extent));
            GUI.DrawTexture(view,microscopeVignette);
        }
        GUI.color=new Color(previous.r,previous.g,previous.b,previous.a*blend);
        bool scope=microscopeBlend>.5f;
        Label(28,110,800,28,scope?"MICROSCOPE  /  模式図・仮倍率":"OBSERVATION  /  左ドラッグで回転",subtitleStyle);
        Label(28,uiHeight-133,950,30,scope?"左ドラッグで観察位置を移動  ·  ホイールで拡大":"ホイールで拡大  ·  右のボタンから顕微鏡へ",subtitleStyle);
        GUI.color=previous;
    }

    void OnDisable()
    {
        CloseObservationImmediately();
    }

    void OnDestroy()
    {
        ReleaseFonts();
        if(microscopeVignette) Destroy(microscopeVignette);
    }
}
