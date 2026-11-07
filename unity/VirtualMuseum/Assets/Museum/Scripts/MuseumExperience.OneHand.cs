using UnityEngine;

public partial class MuseumExperience
{
    bool oneHandNavigation=true, navigationOnRight;
    Vector2 navigationDeflection;
    bool navigationLooking;
    float navigationHoldProgress;
    const float NavigationHoldSeconds=.6f;

    void SetOneHandNavigation(bool enabled)
    {
        CancelTouchGestures();CancelArrivalTurn();walking=false;
        oneHandNavigation=enabled;PlayerPrefs.SetInt("Museum.OneHandNavigation",enabled?1:0);PlayerPrefs.Save();
    }
    void SetNavigationSide(bool right)
    {
        CancelTouchGestures();walking=false;navigationOnRight=right;
        PlayerPrefs.SetInt("Museum.NavigationOnRight",right?1:0);PlayerPrefs.Save();
    }

    static float NavigationAxis(float value)
    {
        float magnitude=Mathf.Abs(value);
        return magnitude<=.16f?0:Mathf.Sign(value)*Mathf.InverseLerp(.16f,1,magnitude);
    }

    void ProcessNavigationPad(Vector2 input,Gesture gesture,bool secondWorldFinger)
    {
        navigationDeflection=input;
        if(!oneHandNavigation || secondWorldFinger)
        {
            gesture.centerHeld=0;gesture.holdArmed=false;
            touchMovement=input.magnitude<.12f?Vector2.zero:input;
            return;
        }
        // A centre dwell changes modes once. Deflecting rearms the next dwell,
        // so resting a finger at the centre cannot toggle back and forth.
        if(input.magnitude>.28f){gesture.holdArmed=true;gesture.centerHeld=0;}
        else if(input.magnitude<.16f && gesture.holdArmed)
        {
            gesture.centerHeld+=Time.unscaledDeltaTime;
            navigationHoldProgress=Mathf.Clamp01(gesture.centerHeld/NavigationHoldSeconds);
            if(gesture.centerHeld>=NavigationHoldSeconds)
            {
                gesture.padLook=!gesture.padLook;gesture.holdArmed=false;
                gesture.centerHeld=0;navigationHoldProgress=0;
            }
        }
        else gesture.centerHeld=0;
        navigationLooking=gesture.padLook;
        float horizontal=NavigationAxis(input.x),vertical=NavigationAxis(input.y);
        if(horizontal!=0 || vertical!=0)
        {
            CancelArrivalTurn();walking=false;selectionPinned=false;
            if(gesture.padLook)
            {
                // In look mode the scenery follows the finger, like world drag.
                yaw-=horizontal*65*Time.deltaTime;
                pitch=Mathf.Clamp(pitch+vertical*48*Time.deltaTime,-60,60);
            }
            else
            {
                // Steering points the visitor into the bend; no sideways drift.
                yaw+=horizontal*65*Time.deltaTime;
                touchMovement=new Vector2(0,vertical);
            }
        }
    }
}
