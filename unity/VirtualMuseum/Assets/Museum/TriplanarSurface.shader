Shader "Museum/Triplanar Surface"
{
    Properties
    {
        _MainTex ("Base color (RGB) / legacy height (A)", 2D) = "white" {}
        _NormalMap ("Surface normal (OpenGL)", 2D) = "bump" {}
        _RoughnessMap ("Surface roughness (R)", 2D) = "white" {}
        _HeightMap ("Surface height (R)", 2D) = "gray" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _ColorUniformity ("Reduce broad color mottling", Range(0,1)) = 0
        _Tiling ("Texture repeats per metre", Float) = 1
        _TextureRotation ("Texture rotation (degrees)", Float) = 0
        _ObjectCoordinates ("Use object-oriented metric coordinates", Range(0,1)) = 0
        _ObjectVariation ("Variation between wooden parts", Range(0,0.1)) = 0
        _Metallic ("Metallic", Range(0,1)) = 0
        _Smoothness ("Fallback smoothness", Range(0,1)) = 0.2
        _RoughnessMin ("Photographic roughness minimum", Range(0,1)) = 0
        _RoughnessMax ("Photographic roughness maximum", Range(0,1)) = 1
        _NormalStrength ("Normal strength", Range(0,2)) = 0.5
        _Relief ("Height relief (metres)", Range(0,0.02)) = 0.0002
        _TileSize ("Carpet tile width (metres; 0 disables)", Float) = 0
        _TileSeamWidth ("Carpet joint half-width (metres)", Float) = 0.0008
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "DisableBatching"="True" }
        LOD 300
        CGPROGRAM
        #pragma surface surf Standard fullforwardshadows
        #pragma target 3.0
        #pragma shader_feature_local _SURFACE_NORMAL
        #pragma shader_feature_local _SURFACE_ROUGHNESS
        #pragma shader_feature_local _SURFACE_HEIGHT

        sampler2D _MainTex, _NormalMap, _RoughnessMap, _HeightMap;
        fixed4 _Color;
        float _Tiling, _TextureRotation, _ObjectCoordinates, _ObjectVariation;
        half _Metallic, _Smoothness, _RoughnessMin, _RoughnessMax, _NormalStrength, _ColorUniformity;
        float _Relief, _TileSize, _TileSeamWidth;

        struct Input
        {
            float3 worldPos;
            float3 worldNormal;
            INTERNAL_DATA
        };

        float hash(float3 p)
        {
            return frac(sin(dot(p, float3(12.9898, 78.233, 37.719))) * 43758.5453);
        }

        float2 rotateUV(float2 uv, float2 cs)
        {
            return float2(cs.x * uv.x - cs.y * uv.y, cs.y * uv.x + cs.x * uv.y);
        }

        float2 normalSlope(float2 uv, float2 cs)
        {
            float3 n = UnpackNormal(tex2D(_NormalMap, uv));
            // Transform the sampled slope back from the rotated texture frame.
            float2 slope = n.xy / max(n.z, 0.3);
            return float2(cs.x * slope.x + cs.y * slope.y,
                         -cs.y * slope.x + cs.x * slope.y) * _NormalStrength;
        }

        void surf(Input IN, inout SurfaceOutputStandard o)
        {
            float3 normal = normalize(WorldNormalVector(IN, float3(0,0,1)));
            float3 axisX = normalize(unity_ObjectToWorld._m00_m10_m20);
            float3 axisY = normalize(unity_ObjectToWorld._m01_m11_m21);
            float3 axisZ = normalize(unity_ObjectToWorld._m02_m12_m22);
            float3 origin = unity_ObjectToWorld._m03_m13_m23;
            float3 relative = IN.worldPos - origin;
            // Unlike normalized mesh UVs, these remain in metres on long thin
            // drawer fronts. Grain follows a drawer when its shelf is rotated.
            float3 localMetres = float3(dot(relative, axisX), dot(relative, axisY), dot(relative, axisZ));
            float3 localNormal = float3(dot(normal, axisX), dot(normal, axisY), dot(normal, axisZ));
            float3 projectionNormal = lerp(normal, localNormal, _ObjectCoordinates);
            float3 blend = pow(abs(projectionNormal), 6);
            blend /= max(blend.x + blend.y + blend.z, 0.0001);
            float3 p = lerp(IN.worldPos, localMetres, _ObjectCoordinates) * _Tiling;
            float seed = hash(origin);
            // A different portion of the same timber photograph on each part.
            p += step(0.001, _ObjectVariation) * float3(seed * 9.13, seed * 3.71, seed * 5.47);
            float angle = radians(_TextureRotation);
            float2 cs = float2(cos(angle), sin(angle));
            float2 uvX = rotateUV(p.zy, cs), uvY = rotateUV(p.xz, cs), uvZ = rotateUV(p.xy, cs);
            fixed4 surface = tex2D(_MainTex, uvX) * blend.x +
                             tex2D(_MainTex, uvY) * blend.y +
                             tex2D(_MainTex, uvZ) * blend.z;
            o.Albedo = lerp(surface.rgb, float3(1,1,1), _ColorUniformity) * _Color.rgb *
                (1 + (seed - 0.5) * 2 * _ObjectVariation);
            o.Metallic = _Metallic;
            o.Smoothness = _Smoothness;
            #if defined(_SURFACE_ROUGHNESS)
                float roughness = tex2D(_RoughnessMap, uvX).r * blend.x +
                                  tex2D(_RoughnessMap, uvY).r * blend.y +
                                  tex2D(_RoughnessMap, uvZ).r * blend.z;
                o.Smoothness = 1 - lerp(_RoughnessMin, _RoughnessMax, roughness);
            #endif
            o.Alpha = 1;

            // Very narrow, antialiased butt joints and slight dye-lot variation
            // distinguish 50 cm carpet tiles without a checkerboard pattern.
            if (_TileSize > 0.01 && abs(normal.y) > 0.7)
            {
                float2 grid = IN.worldPos.xz / _TileSize;
                float2 edge = min(frac(grid), 1 - frac(grid)) * _TileSize;
                float distanceToJoint = min(edge.x, edge.y);
                float seam = 1 - smoothstep(_TileSeamWidth,
                    _TileSeamWidth + max(fwidth(distanceToJoint), 0.0004), distanceToJoint);
                float tileTone = 1 + (hash(float3(floor(grid), 2.31)) - 0.5) * 0.035;
                o.Albedo *= tileTone * (1 - seam * 0.10);
            }

            float3 displaced = normal;
            #if defined(_SURFACE_NORMAL)
                float2 nx = normalSlope(uvX, cs), ny = normalSlope(uvY, cs), nz = normalSlope(uvZ, cs);
                float3 slope = float3(0, nx.y, nx.x) * blend.x +
                               float3(ny.x, 0, ny.y) * blend.y +
                               float3(nz.x, nz.y, 0) * blend.z;
                float3 localSlope = slope.x * axisX + slope.y * axisY + slope.z * axisZ;
                slope = lerp(slope, localSlope, _ObjectCoordinates);
                displaced = normalize(normal + slope - normal * dot(normal, slope));
            #else
                float height = surface.a;
                #if defined(_SURFACE_HEIGHT)
                    height = tex2D(_HeightMap, uvX).r * blend.x +
                             tex2D(_HeightMap, uvY).r * blend.y +
                             tex2D(_HeightMap, uvZ).r * blend.z;
                #endif
                // Legacy alpha height and dedicated PBR height share a metric
                // surface-gradient path. Do not double-count height + normal.
                float3 dpdx = ddx(IN.worldPos), dpdy = ddy(IN.worldPos);
                float3 crossX = cross(dpdy, normal), crossY = cross(normal, dpdx);
                float determinant = dot(dpdx, crossX);
                float3 gradient = sign(determinant) * (ddx(height) * crossX + ddy(height) * crossY);
                displaced = normalize(max(abs(determinant), 1e-8) * normal - _Relief * gradient);
            #endif
            float3 tangent = normalize(WorldNormalVector(IN, float3(1,0,0)));
            float3 bitangent = normalize(WorldNormalVector(IN, float3(0,1,0)));
            o.Normal = normalize(float3(dot(displaced,tangent), dot(displaced,bitangent), dot(displaced,normal)));
        }
        ENDCG
    }
    FallBack "Standard"
}
