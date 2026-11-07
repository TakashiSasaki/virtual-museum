using UnityEngine;

[CreateAssetMenu(menuName="Museum/Specimen collection")]
public sealed class MuseumCollection : ScriptableObject
{
    [System.Serializable]
    public sealed class Entry
    {
        public string title, english;
        public string category;
        [TextArea(3,6)] public string description;
        public GameObject model;
        // Web-only catalog: a lightweight model plus an optional mesh bundle.
        public string detailBundle;
        public long detailBytes;
        public int microscopePattern;
        public string microscopeCaption;
    }
    public Entry[] entries;
    public int exhibitionCount;
    public Texture2D reserveThumbnails;
}
