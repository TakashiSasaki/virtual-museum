Shader "Museum/Wayfinding"
{
    Properties
    {
        _Color ("Tint", Color) = (1,1,1,1)
        _Opacity ("Opacity", Range(0,1)) = 1
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True" }
        Cull Off
        Lighting Off
        ZWrite Off
        ZTest LEqual
        Blend SrcAlpha OneMinusSrcAlpha

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #include "UnityCG.cginc"

            struct appdata
            {
                float4 vertex : POSITION;
                fixed4 color : COLOR;
            };
            struct v2f
            {
                float4 vertex : SV_POSITION;
                fixed4 color : COLOR;
                UNITY_FOG_COORDS(0)
            };

            fixed4 _Color;
            half _Opacity;

            v2f vert(appdata input)
            {
                v2f output;
                output.vertex = UnityObjectToClipPos(input.vertex);
                output.color = input.color * _Color;
                output.color.a *= _Opacity;
                UNITY_TRANSFER_FOG(output, output.vertex);
                return output;
            }

            fixed4 frag(v2f input) : SV_Target
            {
                fixed4 color = input.color;
                UNITY_APPLY_FOG(input.fogCoord, color);
                return color;
            }
            ENDCG
        }
    }
    Fallback Off
}
