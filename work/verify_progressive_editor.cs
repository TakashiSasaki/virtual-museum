var app=UnityEngine.Object.FindAnyObjectByType<MuseumExperience>();
var flags=System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance;
var type=app.GetType();
var check=new System.Collections.Generic.List<string>();
if(app.collection.entries.Length!=48 || (int)type.GetProperty("RoomSpecimenCount",flags).GetValue(app)!=23 || app.destinations.Length!=25)throw new System.Exception("Catalog/destination counts differ");
check.Add("48 models; room destinations remain 23+2");
int before=app.selected;app.OpenBackyard();
if(!(bool)type.GetProperty("TouchWorldInputBlocked",flags).GetValue(app))throw new System.Exception("Gallery does not block walking");
for(int i=0;i<25;i++){
 app.ObserveReserve(i);
 var held=(UnityEngine.GameObject)type.GetField("held",flags).GetValue(app);
 if(!held || app.selected!=23+i || held.GetComponentsInChildren<UnityEngine.Renderer>().Length==0)throw new System.Exception("Missing reserve "+i);
 type.GetMethod("CloseObservationImmediately",flags).Invoke(app,null);
 if(app.selected!=before || !(bool)type.GetField("backyardOpen",flags).GetValue(app))throw new System.Exception("Return failed "+i);
}
check.Add("All 25 reserves open and return to the gallery, preserving the room selection");
app.ObserveReserve(0);
var target=(UnityEngine.GameObject)type.GetField("held",flags).GetValue(app);
target.transform.localRotation=UnityEngine.Quaternion.Euler(12,37,8);target.transform.localScale=UnityEngine.Vector3.one*1.6f;
var rotation=target.transform.localRotation;var scale=target.transform.localScale;
var filter=target.GetComponentInChildren<UnityEngine.MeshFilter>();
type.GetMethod("ApplyDetailMesh",flags).Invoke(app,new object[]{filter.sharedMesh});
if(UnityEngine.Quaternion.Angle(rotation,target.transform.localRotation)>.001f || target.transform.localScale!=scale)throw new System.Exception("Swap changed view");
check.Add("Mesh replacement preserves held rotation and scale");
type.GetMethod("CloseObservationImmediately",flags).Invoke(app,null);
app.SetWebViewport("{\"width\":390,\"height\":844,\"touch\":true}");
return check;
