export const vertexShaderSource = `
  attribute vec4 aVertexPosition;
  attribute vec3 aNormal;
  attribute vec2 aTextureCoord;
  
  uniform mat4 uModelViewMatrix;
  uniform mat4 uProjectionMatrix;
  uniform mat4 uNormalMatrix;
  
  varying vec2 vTextureCoord;
  varying vec3 vNormal;
  
  void main() {
    gl_Position = uProjectionMatrix * uModelViewMatrix * aVertexPosition;
    vTextureCoord = aTextureCoord;
    vNormal = (uNormalMatrix * vec4(aNormal, 0.0)).xyz;
  }
`

export const fragmentShaderSource = `
  precision mediump float;
  
  varying vec2 vTextureCoord;
  varying vec3 vNormal;
  
  uniform sampler2D uSampler;
  uniform vec3 uLightDirection;
  
  void main() {
    vec4 texColor = texture2D(uSampler, vTextureCoord);
    vec3 normal = normalize(vNormal);
    float light = max(dot(normal, uLightDirection), 0.0);
    gl_FragColor = vec4(texColor.rgb * (0.3 + 0.7 * light), texColor.a);
  }
` 