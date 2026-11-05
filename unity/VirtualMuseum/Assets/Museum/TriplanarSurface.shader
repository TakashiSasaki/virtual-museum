Shader "Museum/Triplanar Surface"
{
    Properties
    {
        _MainTex ("Albedo (RGB) / Height (A)", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _Tiling ("Texture repeats per metre", Float) = 1
        _Metallic ("Metallic", Range(0,1)) = 0
        _Smoothness ("Smoothness", Range(0,1)) = 0.2
        _Relief ("Surface relief (metres)", Range(0,0.02)) = 0.002
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" }
        LOD 250

        CGPROGRAM
        #pragma surface surf Standard fullforwardshadows
        #pragma target 3.0

        sampler2D _MainTex;
        fixed4 _Color;
        half _Tiling, _Metallic, _Smoothness, _Relief;

        struct Input
        {
            float3 worldPos;
            float3 worldNormal;
            INTERNAL_DATA
        };

        void surf(Input IN, inout SurfaceOutputStandard o)
        {
            float3 normal = normalize(WorldNormalVector(IN, float3(0,0,1)));
            float3 blend = pow(abs(normal), 4);
            blend /= max(blend.x + blend.y + blend.z, 0.0001);
            float3 p = IN.worldPos * _Tiling;
            // On the long fronts of the specimen drawers, U runs horizontally.
            fixed4 xFace = tex2D(_MainTex, p.zy);
            fixed4 yFace = tex2D(_MainTex, p.zx);
            fixed4 zFace = tex2D(_MainTex, p.xy);
            fixed4 surface = xFace * blend.x + yFace * blend.y + zFace * blend.z;
            o.Albedo = surface.rgb * _Color.rgb;
            o.Metallic = _Metallic;
            o.Smoothness = _Smoothness;
            o.Alpha = 1;

            // Screen-space surface gradient converts the height in alpha to a
            // world-space perturbation, independent of the mesh's UV layout.
            float3 dpdx = ddx(IN.worldPos), dpdy = ddy(IN.worldPos);
            float dhdx = ddx(surface.a), dhdy = ddy(surface.a);
            float3 crossX = cross(dpdy, normal), crossY = cross(normal, dpdx);
            float determinant = dot(dpdx, crossX);
            float3 gradient = sign(determinant) * (dhdx * crossX + dhdy * crossY);
            float3 displaced = normalize(max(abs(determinant), 1e-8) * normal - _Relief * gradient);
            float3 tangent = normalize(WorldNormalVector(IN, float3(1,0,0)));
            float3 bitangent = normalize(WorldNormalVector(IN, float3(0,1,0)));
            o.Normal = normalize(float3(dot(displaced,tangent), dot(displaced,bitangent), dot(displaced,normal)));
        }
        ENDCG
    }
    FallBack "Standard"
}
