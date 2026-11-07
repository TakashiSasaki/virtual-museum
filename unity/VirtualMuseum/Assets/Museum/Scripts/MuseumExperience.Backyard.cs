using System.Collections.Generic;
using UnityEngine;

public partial class MuseumExperience
{
    MuseumCollection runtimeCollection;
    bool backyardOpen,viewingBackyard;
    int backyardPage,backyardCategory,selectionBeforeBackyard;
    readonly HashSet<int> backyardSeen=new();
    Texture2D backyardGlass,backyardPanel;
    GUIStyle backyardButton,backyardCaption,backyardCardCaption;
    readonly string[] backyardCategories={"すべて","昆虫","化石","遺物"};
    Rect BackyardButtonRect => CompactUI?new Rect(uiWidth-168,64,156,44):new Rect(872,110,176,44);
    bool BackyardAvailable => SpecimenCount>RoomSpecimenCount;
    bool BackyardButtonVisible => BackyardAvailable && mode=="walk" && !ImmersionActive && !touring && !TouchWorldInputBlocked;

    public void OpenBackyard()
    {
        if(!BackyardAvailable || touring)return;
        CloseGuideConversation();CancelArrivalTurn();CloseObservationImmediately();
        walking=false;helpOpen=false;listOpen=false;compactMenuOpen=false;backyardOpen=true;
        CancelTouchGestures();
    }

    public void ObserveReserve(int reserveIndex)
    {
        if(reserveIndex<0 || reserveIndex>=SpecimenCount-RoomSpecimenCount)return;
        if(!viewingBackyard)selectionBeforeBackyard=Mathf.Clamp(selected,0,RoomSpecimenCount-1);
        viewingBackyard=true;backyardOpen=false;
        Observe(RoomSpecimenCount+reserveIndex);
    }

    void ReturnFromBackyardObservation()
    {
        if(!viewingBackyard)return;
        viewingBackyard=false;selected=selectionBeforeBackyard;backyardOpen=true;
    }

    void DrawBackyard()
    {
        if(!BackyardAvailable)return;
        SetupCompactStyles();
        if(!backyardGlass)backyardGlass=Solid(new Color(.04f,.19f,.18f,.78f));
        if(!backyardPanel)backyardPanel=Solid(new Color(.04f,.16f,.15f,.96f));
        if(backyardButton==null)
        {
            backyardButton=new GUIStyle(compactButton);backyardButton.normal.background=backyardGlass;
            backyardButton.normal.textColor=Color.white;backyardButton.hover.textColor=Color.white;
            backyardCaption=new GUIStyle(compactLight){fontSize=13,alignment=TextAnchor.MiddleCenter};
            backyardCardCaption=new GUIStyle(compactSmall){alignment=TextAnchor.MiddleCenter,wordWrap=true};
        }
        if(BackyardButtonVisible)
        {
            var rect=BackyardButtonRect;
            bool click=GUI.Button(rect,"▦ バックヤード",backyardButton);
            if(IgnoreGameplayMouse)click=TouchButton(rect);
            if(click)OpenBackyard();
        }
        if(!backyardOpen)return;
        float width=CompactUI?uiWidth-24:900;
        var panelRect=new Rect(CompactUI?12:(uiWidth-width)/2,CompactUI?(CompactLandscape?8:64):120,width,uiHeight-(CompactUI?(CompactLandscape?16:76):240));
        GUI.DrawTexture(panelRect,backyardPanel);
        GUI.Label(new Rect(panelRect.x+14,panelRect.y+8,width-100,38),"バックヤード訪問",compactLight);
        if(CompactButton(new Rect(panelRect.xMax-76,panelRect.y+6,66,44),"閉じる")){backyardOpen=false;return;}
        GUI.Label(new Rect(panelRect.x+14,panelRect.y+49,width-28,27),"未展示の模型 · 選ぶと手元で観察",backyardCaption);
        float tab=(width-28)/4;
        for(int i=0;i<4;i++)
            if(CompactButton(new Rect(panelRect.x+14+i*tab,panelRect.y+80,tab-4,40),backyardCategories[i],backyardCategory==i))
            {backyardCategory=i;backyardPage=0;}
        var matches=new List<int>();
        for(int index=RoomSpecimenCount;index<SpecimenCount;index++)
        {
            string category=collection.entries[index].category??"";
            if(backyardCategory==0 || backyardCategory==1 && category.StartsWith("昆虫") ||
                backyardCategory==2 && category=="化石" || backyardCategory==3 && (category=="土器" || category=="石器"))matches.Add(index);
        }
        float gridTop=panelRect.y+132,gridHeight=Mathf.Max(60,panelRect.height-192);
        int cols=width>540?3:2,rows=Mathf.Clamp(Mathf.FloorToInt(gridHeight/132),1,3),pageSize=rows*cols;
        int pages=Mathf.Max(1,Mathf.CeilToInt(matches.Count/(float)pageSize));backyardPage=Mathf.Clamp(backyardPage,0,pages-1);
        float cellWidth=(width-28)/cols,cellHeight=gridHeight/rows;
        for(int slot=0;slot<pageSize && backyardPage*pageSize+slot<matches.Count;slot++)
        {
            int index=matches[backyardPage*pageSize+slot],reserveIndex=index-RoomSpecimenCount;
            var rect=new Rect(panelRect.x+14+(slot%cols)*cellWidth,gridTop+(slot/cols)*cellHeight,cellWidth-6,cellHeight-6);
            if(CompactButton(rect,"")){ObserveReserve(reserveIndex);return;}
            float thumb=Mathf.Min(rect.width-8,rect.height-36);
            if(collection.reserveThumbnails && thumb>16)
            {
                int atlasRows=Mathf.CeilToInt((SpecimenCount-RoomSpecimenCount)/5f);
                var uv=new Rect((reserveIndex%5)/5f,(atlasRows-1-reserveIndex/5)/(float)atlasRows,1/5f,1f/atlasRows);
                GUI.DrawTextureWithTexCoords(new Rect(rect.center.x-thumb/2,rect.y+3,thumb,thumb),collection.reserveThumbnails,uv);
            }
            var caption=new Rect(rect.x+3,rect.yMax-34,rect.width-6,32);
            GUI.Label(caption,(backyardSeen.Contains(index)?"✓ ":"")+names[index],backyardCardCaption);
        }
        float bottom=panelRect.yMax-52;
        bool previous=GUI.enabled;GUI.enabled=previous && backyardPage>0;
        if(CompactButton(new Rect(panelRect.x+14,bottom,80,44),"前へ"))backyardPage--;
        GUI.enabled=previous;
        GUI.Label(new Rect(panelRect.x+100,bottom,width-200,44),$"{backyardPage+1} / {pages}  ·  {matches.Count}点",backyardCaption);
        GUI.enabled=previous && backyardPage<pages-1;
        if(CompactButton(new Rect(panelRect.xMax-94,bottom,80,44),"次へ"))backyardPage++;
        GUI.enabled=previous;
    }
}
