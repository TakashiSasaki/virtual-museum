using UnityEngine;

// Geometry and images only: never bring a second scene, rig or shader into the room.
public sealed class MuseumRoomPayload : ScriptableObject
{
    public Mesh[] meshes = System.Array.Empty<Mesh>();
    public Texture2D[] textures = System.Array.Empty<Texture2D>();
}
