using UnityEngine;

public partial class MuseumExperience
{
    MuseumRoomStreaming roomStreaming;
    public bool DetailDownloadInProgress => detailLoading;
    void PrioritizeRoom(Component target)
    {
        if(!roomStreaming)roomStreaming=GetComponent<MuseumRoomStreaming>();
        if(roomStreaming)roomStreaming.Prioritize(target);
    }
    bool RoomStatusVisible => roomStreaming && roomStreaming.Pending && mode=="walk" && !touring && !TouchWorldInputBlocked;
    Rect RoomStatusRect => CompactUI ? new Rect(12,CompactHeaderHeight+66,uiWidth-24,34) : new Rect(28,146,430,38);
    void DrawRoomStatus()
    {
        if(!roomStreaming)roomStreaming=GetComponent<MuseumRoomStreaming>();
        if(!RoomStatusVisible)return;
        var rect=RoomStatusRect;
        if(roomStreaming.Failed>0)
        {
            if(CompactUI?CompactButton(rect,roomStreaming.Status):Button(rect.x,rect.y,rect.width,roomStreaming.Status,false,38))roomStreaming.RetryFailed();
        }
        else
        {
            var previous=GUI.color;GUI.color=new Color(1,1,1,.72f);GUI.DrawTexture(rect,dark);GUI.color=previous;
            GUI.Label(rect,roomStreaming.Status,CompactUI?compactLight:darkTextStyle);
        }
    }
}
