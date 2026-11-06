using UnityEngine;

[CreateAssetMenu(menuName="Museum/Specimen collection")]
public sealed class MuseumCollection : ScriptableObject
{
    [System.Serializable]
    public sealed class Entry
    {
        public string title, english;
        [TextArea(3,6)] public string description;
        public GameObject model;
        public int microscopePattern;
        public string microscopeCaption;
    }
    public Entry[] entries;
}
