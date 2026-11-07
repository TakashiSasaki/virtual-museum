using UnityEngine;

public partial class MuseumExperience
{
    bool arrivalTurning;
    Component beaconWalkTarget;
    float arrivalElapsed, arrivalYaw, arrivalPitch, arrivalEndYaw, arrivalEndPitch;
    Component arrivalTarget;
    bool activateAfterTurn;

    void CancelArrivalTurn() { beaconWalkTarget=null; arrivalTurning=false;arrivalTarget=null;activateAfterTurn=false; }

    public void WalkToBeacon(Component target,Vector3 approach)
    {
        if(!target || !WayfindingVisible)return;
        PrioritizeRoom(target);
        CancelArrivalTurn();CancelTouchGestures();
        beaconWalkTarget=target;walkTarget=approach;walkTarget.y=visitor.transform.position.y;walking=true;
        if(target is MuseumExhibit exhibit){selected=exhibit.index;selectionPinned=true;}
        notice="ビーコンへ移動しています。到着すると対象へ向き直ります。";
    }

    void BeginArrivalTurn(Component target, bool activate=false, float fallbackYaw=0)
    {
        CancelArrivalTurn();
        arrivalTarget=target;activateAfterTurn=activate;
        arrivalYaw=yaw;arrivalPitch=pitch;arrivalElapsed=0;
        arrivalEndYaw=fallbackYaw;arrivalEndPitch=0;
        if(target) ArrivalAngles(target,out arrivalEndYaw,out arrivalEndPitch);
        arrivalTurning=true;
    }

    void ArrivalAngles(Component target,out float targetYaw,out float targetPitch)
    {
        var delta=InteractionPoint(target)-visitorCamera.transform.position;
        targetYaw=Mathf.Atan2(delta.x,delta.z)*Mathf.Rad2Deg;
        targetPitch=Mathf.Clamp(-Mathf.Atan2(delta.y,new Vector2(delta.x,delta.z).magnitude)*Mathf.Rad2Deg,-60,60);
    }

    // The sign identifies the actual item, not its floor anchor or badge.
    public void ApproachInteraction(Component target)
    {
        if(!target || !WayfindingVisible)return;
        walking=false;CancelTouchGestures();
        BeginArrivalTurn(target,true);
    }

    void UpdateArrivalTurn()
    {
        if(!arrivalTurning)return;
        if(mode!="walk" || ImmersionActive || touring){CancelArrivalTurn();return;}
        if(TouchWorldInputBlocked || externalOverlay)return;
        if(activateAfterTurn && !arrivalTarget){CancelArrivalTurn();return;}
        if(arrivalTarget)ArrivalAngles(arrivalTarget,out arrivalEndYaw,out arrivalEndPitch);
        arrivalElapsed+=Time.unscaledDeltaTime;
        float t=Mathf.SmoothStep(0,1,Mathf.Clamp01(arrivalElapsed/.8f));
        yaw=Mathf.LerpAngle(arrivalYaw,arrivalEndYaw,t);pitch=Mathf.LerpAngle(arrivalPitch,arrivalEndPitch,t);
        visitor.transform.rotation=Quaternion.Euler(0,yaw,0);
        visitorCamera.transform.localRotation=Quaternion.Euler(pitch,0,0);
        if(t<1)return;
        var target=arrivalTarget;bool activate=activateAfterTurn;CancelArrivalTurn();
        if(!activate)return;
        if(target is MuseumExhibit exhibit)Observe(exhibit.index);
        else if(target is MicroscopeStation station)Microscope(station);
        else if(target is GuideMarker)Talk();
    }
}
