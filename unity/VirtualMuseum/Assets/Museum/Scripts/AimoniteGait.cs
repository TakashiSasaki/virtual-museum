using System;
using UnityEngine;

/// <summary>
/// Drives the Blender skeleton from actual NPC displacement. Stance feet stay
/// in world space, swing feet clear the floor, and two-bone IK bends the knees.
/// Patrol and conversation code remain responsible for the guide's root pose.
/// </summary>
[DisallowMultipleComponent]
[DefaultExecutionOrder(100)]
public sealed class AimoniteGait : MonoBehaviour
{
    [Range(.65f, 1.0f)] public float strideToLegLength = .85f;
    [Range(.08f, .25f)] public float footLiftToLegLength = .16f;
    public bool IsRigReady { get; private set; }
    public float LastSpeed { get; private set; }
    public float TravelledDistance { get; private set; }
    public float LastFootPlantError { get; private set; }
    public float LastFootLift { get; private set; }
    public int RecoverySteps { get; private set; }

    const float StanceFraction = .60f;
    Transform rootBone, leftArm, leftForearm, rightArm, rightForearm;
    BonePose[] restPose;
    Leg left, right;
    Vector3 previousPosition, travelDirection, rootRestPosition, locomotionCenter;
    Quaternion rootRestRotation;
    float phase = .30f, walkingWeight;
    bool wasMoving;

    struct BonePose
    {
        public Transform bone;
        public Quaternion rotation;
    }

    sealed class Leg
    {
        public Transform thigh, shin, foot;
        public Vector3 neutralPosition, plant, swingStart, landing, lastTarget;
        public Quaternion neutralRotation;
        public float upperLength, lowerLength;
        public bool swinging;
        public bool recovering, suppressSwing;
        public float recoveryProgress;
    }

    void Start()
    {
        rootBone = FindBone("AM_Root");
        leftArm = FindBone("AM_UpperArm_L");
        leftForearm = FindBone("AM_Forearm_L");
        rightArm = FindBone("AM_UpperArm_R");
        rightForearm = FindBone("AM_Forearm_R");
        left = MakeLeg("L");
        right = MakeLeg("R");
        if (!rootBone || left == null || right == null || !leftArm || !leftForearm || !rightArm || !rightForearm)
        {
            Debug.LogWarning("Aimonite walking needs the articulated Aimonite FBX. Reimport the updated model.", this);
            enabled = false;
            return;
        }

        var bones = new[] { rootBone, left.thigh, left.shin, left.foot, right.thigh, right.shin,
            right.foot, leftArm, leftForearm, rightArm, rightForearm };
        restPose = new BonePose[bones.Length];
        for (int i = 0; i < bones.Length; i++)
            restPose[i] = new BonePose { bone = bones[i], rotation = bones[i].localRotation };
        rootRestPosition = rootBone.localPosition;
        rootRestRotation = rootBone.localRotation;
        locomotionCenter = (left.neutralPosition + right.neutralPosition) * .5f;
        locomotionCenter.y = 0;
        previousPosition = transform.TransformPoint(locomotionCenter);
        travelDirection = transform.forward;
        ResetContacts();
        IsRigReady = true;
    }

    Transform FindBone(string name)
    {
        foreach (Transform item in GetComponentsInChildren<Transform>(true))
            if (item.name == name) return item;
        return null;
    }

    Leg MakeLeg(string side)
    {
        var thigh = FindBone("AM_Thigh_" + side);
        var shin = FindBone("AM_Shin_" + side);
        var foot = FindBone("AM_Foot_" + side);
        if (!thigh || !shin || !foot) return null;
        return new Leg {
            thigh = thigh, shin = shin, foot = foot,
            upperLength = Vector3.Distance(thigh.position, shin.position),
            lowerLength = Vector3.Distance(shin.position, foot.position),
            neutralPosition = transform.InverseTransformPoint(foot.position),
            neutralRotation = Quaternion.Inverse(transform.rotation) * foot.rotation,
        };
    }

    void ResetContacts()
    {
        foreach (var leg in new[] { left, right })
        {
            leg.plant = leg.swingStart = leg.landing = leg.lastTarget = NeutralFoot(leg);
            leg.swinging = false;
            leg.recovering = leg.suppressSwing = false;
            leg.recoveryProgress = 0;
        }
    }

    Vector3 NeutralFoot(Leg leg)
    {
        return transform.TransformPoint(leg.neutralPosition);
    }

    void LateUpdate()
    {
        if (!IsRigReady || Time.deltaTime <= 0) return;
        // The feet are offset from the shell's object origin. Count the
        // movement at the feet, including the arc traced when the NPC turns.
        Vector3 center = transform.TransformPoint(locomotionCenter);
        Vector3 displacement = center - previousPosition;
        previousPosition = center;
        displacement.y = 0;
        float distance = displacement.magnitude;
        float legLength = (left.upperLength + left.lowerLength + right.upperLength + right.lowerLength) * .5f;
        float stride = Mathf.Max(.05f, legLength * strideToLegLength);

        foreach (var pose in restPose) pose.bone.localRotation = pose.rotation;
        rootBone.localPosition = rootRestPosition;
        rootBone.localRotation = rootRestRotation;
        LastFootPlantError = 0;
        LastFootLift = 0;

        // Starting the tour deliberately relocates the guide. It is a teleport,
        // so reset contacts rather than interpreting it as an enormous stride.
        if (distance > Mathf.Max(stride, Time.deltaTime * 3f))
        {
            phase = .30f;
            walkingWeight = LastSpeed = 0;
            wasMoving = false;
            ResetContacts();
            return;
        }

        LastSpeed = distance / Time.deltaTime;
        bool moving = LastSpeed > .012f;
        if (moving)
        {
            travelDirection = displacement / distance;
            if (!wasMoving) { phase = .30f; ResetContacts(); }
            TravelledDistance += distance;
            phase = Mathf.Repeat(phase + distance / stride, 1f);
        }
        walkingWeight = Mathf.MoveTowards(walkingWeight, moving ? 1 : 0, Time.deltaTime * 5f);
        wasMoving = moving;
        if (walkingWeight <= 0)
        {
            ResetContacts();
            return;
        }

        float angle = phase * Mathf.PI * 2;
        float lowerBody = legLength * (-.07f + .01f * Mathf.Cos(angle * 2)) * walkingWeight;
        rootBone.position += Vector3.up * lowerBody;
        rootBone.rotation = Quaternion.AngleAxis(Mathf.Sin(angle) * 1.2f * walkingWeight, transform.forward) * rootBone.rotation;

        PoseLeg(left, phase, stride, legLength, distance, moving);
        PoseLeg(right, Mathf.Repeat(phase + .5f, 1), stride, legLength, distance, moving);

        // The brush arm swings more freely; the arm cradling the seal stays
        // close to the body. A bent elbow keeps the brush clear of the floor.
        RotateArm(leftArm, (10 + Mathf.Sin(angle) * 14) * walkingWeight);
        RotateArm(leftForearm, (30 - Mathf.Abs(Mathf.Sin(angle)) * 5) * walkingWeight);
        RotateArm(rightArm, -Mathf.Sin(angle) * 4 * walkingWeight);
        RotateArm(rightForearm, 2 * walkingWeight);
    }

    void RotateArm(Transform bone, float degrees)
    {
        bone.rotation = Quaternion.AngleAxis(degrees, transform.right) * bone.rotation;
    }

    void PoseLeg(Leg leg, float progress, float stride, float legLength, float distance, bool moving)
    {
        Vector3 neutral = NeutralFoot(leg);
        Vector3 target;
        if (progress < StanceFraction) leg.suppressSwing = false;
        // A sharp turn can shorten the available stance. Release the foot
        // early and take a short recovery step before the knee overextends.
        if (moving && !leg.swinging && !leg.recovering &&
            Vector3.Distance(leg.thigh.position, leg.plant) > (leg.upperLength + leg.lowerLength) * .98f)
        {
            leg.recovering = leg.swinging = true;
            leg.recoveryProgress = 0;
            leg.swingStart = ReachableTarget(leg, leg.lastTarget);
            RecoverySteps++;
        }
        if (!moving)
        {
            // Settle a lifted foot and straighten the knees when conversation
            // or observation pauses patrol, instead of freezing mid-step.
            target = Vector3.Lerp(leg.lastTarget, neutral, 1 - Mathf.Exp(-Time.deltaTime * 16));
            leg.plant = target;
            leg.swinging = false;
            leg.recovering = false;
        }
        else if (leg.recovering)
        {
            leg.recoveryProgress = Mathf.Min(1, leg.recoveryProgress + distance / (stride * .30f));
            float swing = leg.recoveryProgress;
            leg.landing = ReachableTarget(leg, neutral + travelDirection * (stride * .22f));
            float lift = Mathf.Sin(swing * Mathf.PI) * legLength * footLiftToLegLength;
            target = Vector3.Lerp(leg.swingStart, leg.landing, Mathf.SmoothStep(0, 1, swing)) + Vector3.up * lift;
            LastFootLift = Mathf.Max(LastFootLift, lift * walkingWeight);
            if (swing >= 1)
            {
                leg.plant = leg.landing;
                leg.recovering = leg.swinging = false;
                leg.suppressSwing = progress >= StanceFraction;
            }
        }
        else if (progress < StanceFraction || leg.suppressSwing)
        {
            if (leg.swinging)
            {
                leg.plant = leg.landing;
                leg.swinging = false;
            }
            target = leg.plant;
        }
        else
        {
            if (!leg.swinging)
            {
                leg.swingStart = leg.lastTarget;
                leg.swinging = true;
            }
            float swing = (progress - StanceFraction) / (1 - StanceFraction);
            leg.landing = ReachableTarget(leg, neutral + travelDirection * (stride * StanceFraction * .5f));
            // Floor height comes from the unbobbed guide root, so toes do not
            // follow body bob or drift down through the floor.
            leg.landing.y = neutral.y;
            float lift = Mathf.Sin(swing * Mathf.PI) * legLength * footLiftToLegLength;
            target = Vector3.Lerp(leg.swingStart, leg.landing, Mathf.SmoothStep(0, 1, swing)) + Vector3.up * lift;
            LastFootLift = Mathf.Max(LastFootLift, lift * walkingWeight);
        }
        target = ReachableTarget(leg, target);
        leg.lastTarget = target;
        target = Vector3.Lerp(neutral, target, walkingWeight);
        SolveLeg(leg, target);
        leg.foot.rotation = transform.rotation * leg.neutralRotation;
        if (moving && !leg.swinging && walkingWeight > .99f)
            LastFootPlantError = Mathf.Max(LastFootPlantError, Vector3.Distance(leg.foot.position, target));
    }

    Vector3 ReachableTarget(Leg leg, Vector3 target)
    {
        // Shorten a step in the floor plane, preserving sole height. This is
        // primarily for swing landing and early replanting on tight turns.
        Vector3 hip = leg.thigh.position;
        float reach = leg.upperLength + leg.lowerLength - .0002f;
        float vertical = target.y - hip.y;
        float horizontalReach = Mathf.Sqrt(Mathf.Max(0, reach * reach - vertical * vertical));
        Vector3 horizontal = target - hip;
        horizontal.y = 0;
        if (horizontal.magnitude > horizontalReach)
        {
            horizontal = horizontal.normalized * horizontalReach;
            target.x = hip.x + horizontal.x;
            target.z = hip.z + horizontal.z;
        }
        return target;
    }

    void SolveLeg(Leg leg, Vector3 target)
    {
        Vector3 hip = leg.thigh.position;
        Vector3 delta = target - hip;
        float actualDistance = delta.magnitude;
        if (actualDistance < .0001f) return;
        Vector3 direction = delta / actualDistance;
        float length = Mathf.Clamp(actualDistance, Mathf.Abs(leg.upperLength - leg.lowerLength) + .0001f,
            leg.upperLength + leg.lowerLength - .0001f);
        float along = (leg.upperLength * leg.upperLength - leg.lowerLength * leg.lowerLength + length * length) / (2 * length);
        float height = Mathf.Sqrt(Mathf.Max(0, leg.upperLength * leg.upperLength - along * along));
        Vector3 kneeForward = Vector3.ProjectOnPlane(transform.forward, direction).normalized;
        if (kneeForward.sqrMagnitude < .001f) kneeForward = Vector3.ProjectOnPlane(transform.up, direction).normalized;
        Vector3 knee = hip + direction * along + kneeForward * height;
        leg.thigh.rotation = Quaternion.FromToRotation(leg.shin.position - hip, knee - hip) * leg.thigh.rotation;
        leg.shin.rotation = Quaternion.FromToRotation(leg.foot.position - leg.shin.position,
            hip + direction * length - leg.shin.position) * leg.shin.rotation;
    }

    void OnDisable()
    {
        if (restPose == null) return;
        foreach (var pose in restPose) if (pose.bone) pose.bone.localRotation = pose.rotation;
        if (rootBone) rootBone.localPosition = rootRestPosition;
    }
}
