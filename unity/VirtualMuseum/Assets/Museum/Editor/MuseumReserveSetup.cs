using System;
using System.Linq;
using System.IO;
using UnityEngine;
using UnityEditor;
public static class MuseumReserveSetup
{
 const string Models="Assets/Museum/Models/Reserve/", Mats="Assets/Museum/Materials/Reserve/";
 [MenuItem("Museum/Prepare Reserve Collection")]
 public static void Prepare()
 {
  if(EditorApplication.isPlaying)throw new InvalidOperationException("Stop Play first");
  var rows=File.ReadAllLines(Path.GetFullPath("../../docs/reserve-collection.md")).Where(l=>System.Text.RegularExpressions.Regex.IsMatch(l,@"^\| \d\d \|")).Select(l=>l.Split('|').Select(s=>s.Trim().Trim('`')).ToArray()).ToArray();
  if(rows.Length!=25)throw new InvalidOperationException("Expected 25 catalog rows");
  foreach(var r in rows)if(!AssetDatabase.LoadAssetAtPath<GameObject>(Models+r[4]+".fbx"))throw new FileNotFoundException(r[4]);
  Directory.CreateDirectory(Mats);AssetDatabase.Refresh();
  foreach(var r in rows)
  {
   var path=Models+r[4]+".fbx";var importer=(ModelImporter)AssetImporter.GetAtPath(path);
   var materials=AssetDatabase.LoadAllAssetsAtPath(path).OfType<Material>().Concat(importer.GetExternalObjectMap().Values.OfType<Material>()).GroupBy(m=>m.name).Select(g=>g.First()).ToArray();
   foreach(var source in materials)
   {
    var targetPath=Mats+source.name+".mat";var m=AssetDatabase.LoadAssetAtPath<Material>(targetPath);
    if(!m){m=new Material(source);m.name=source.name;AssetDatabase.CreateAsset(m,targetPath);}
    m.shader=Shader.Find("Standard");float alpha=source.name.Contains("WingMembrane")?(r[4]=="Cicada"?.35f:.24f):1;
    var color=m.color;color.a=alpha;m.color=color;m.SetFloat("_Metallic",source.name.Contains("GoldenEyes")?.24f:source.name.Contains("SilverFlanks")?.12f:0);
    m.DisableKeyword("_ALPHATEST_ON");m.DisableKeyword("_ALPHAPREMULTIPLY_ON");
    if(alpha<1){m.SetFloat("_Mode",2);m.SetInt("_SrcBlend",5);m.SetInt("_DstBlend",10);m.SetInt("_ZWrite",0);m.EnableKeyword("_ALPHABLEND_ON");m.renderQueue=3000;m.SetOverrideTag("RenderType","Transparent");}
    else{m.SetFloat("_Mode",0);m.SetInt("_SrcBlend",1);m.SetInt("_DstBlend",0);m.SetInt("_ZWrite",1);m.DisableKeyword("_ALPHABLEND_ON");m.renderQueue=-1;m.SetOverrideTag("RenderType","");}
    EditorUtility.SetDirty(m);importer.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material),source.name),m);
   }
   importer.SaveAndReimport();
  }
  const string catalog="Assets/Museum/ReserveCollection.asset";var data=AssetDatabase.LoadAssetAtPath<MuseumCollection>(catalog);
  if(!data){data=ScriptableObject.CreateInstance<MuseumCollection>();AssetDatabase.CreateAsset(data,catalog);}
  data.entries=rows.Select(r=>new MuseumCollection.Entry{title=r[3],english=r[4],category=r[2],description=r[5]+"を観察するための制作模型です。実物のスキャンや実寸比ではありません。",model=AssetDatabase.LoadAssetAtPath<GameObject>(Models+r[4]+".fbx"),microscopePattern=3,microscopeCaption="体表・表面をイメージした模式図（実測画像ではありません）"}).ToArray();
  EditorUtility.SetDirty(data);AssetDatabase.SaveAssets();Debug.Log("Prepared 25 reserve models; current exhibition unchanged.");
 }
}
