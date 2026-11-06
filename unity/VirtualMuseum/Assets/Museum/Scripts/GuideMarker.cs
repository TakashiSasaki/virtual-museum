using UnityEngine;
public class GuideMarker : MonoBehaviour
{
    void Awake()
    {
        // Also equips existing saved scenes after the articulated FBX imports.
        if (!GetComponent<AimoniteGait>()) gameObject.AddComponent<AimoniteGait>();
    }
}
