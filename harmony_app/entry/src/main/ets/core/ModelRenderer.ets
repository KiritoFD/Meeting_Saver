import webgl from '@ohos.webgl'
import matrix4 from '@ohos.matrix4'
import { vertexShaderSource, fragmentShaderSource } from './shaders'
import quaternion from '@ohos.quaternion'

export class ModelRenderer {
  private gl: webgl.WebGLRenderingContext
  private program: webgl.WebGLProgram
  private model: any // 3D模型数据
  private animationMixer: any
  
  constructor() {
    // WebGL初始化
    this.initWebGL()
    // 加载3D模型
    this.loadModel()
  }

  private initWebGL() {
    // 初始化WebGL上下文
    const canvas = new OffscreenCanvas(640, 480)
    this.gl = canvas.getContext('webgl') as webgl.WebGLRenderingContext
    
    // 设置着色器程序
    const vertexShader = this.createShader(this.gl.VERTEX_SHADER, this.vertexShaderSource)
    const fragmentShader = this.createShader(this.gl.FRAGMENT_SHADER, this.fragmentShaderSource)
    
    this.program = this.gl.createProgram()
    this.gl.attachShader(this.program, vertexShader)
    this.gl.attachShader(this.program, fragmentShader)
    this.gl.linkProgram(this.program)
  }

  private async loadModel() {
    try {
      // 加载GLTF模型
      const response = await fetch('/resources/model/avatar.gltf')
      const modelData = await response.json()
      this.model = this.parseGLTF(modelData)
      
      // 设置动画混合器
      this.animationMixer = new AnimationMixer(this.model)
    } catch (error) {
      console.error('加载3D模型失败:', error)
    }
  }

  updatePose(keypoints: number[][]) {
    if (!this.model) return
    
    // 更新骨骼位置
    this.updateSkeleton(keypoints)
    
    // 渲染新的姿态
    this.render()
  }

  private updateSkeleton(keypoints: number[][]) {
    // 将2D关键点映射到3D骨骼
    const bones = this.model.skeleton.bones
    
    // 更新头部
    if (keypoints[0] && bones.head) {
      bones.head.position.set(
        keypoints[0][0],
        keypoints[0][1],
        keypoints[0][2] || 0
      )
    }
    
    // 更新躯干
    if (keypoints[11] && keypoints[12] && bones.spine) {
      const center = {
        x: (keypoints[11][0] + keypoints[12][0]) / 2,
        y: (keypoints[11][1] + keypoints[12][1]) / 2,
        z: ((keypoints[11][2] || 0) + (keypoints[12][2] || 0)) / 2
      }
      bones.spine.position.set(center.x, center.y, center.z)
    }
    
    // 更新四肢
    this.updateLimb(keypoints, bones, 13, 15, 'leftArm')
    this.updateLimb(keypoints, bones, 14, 16, 'rightArm')
  }

  private updateLimb(keypoints: number[][], bones: any, start: number, end: number, boneName: string) {
    if (keypoints[start] && keypoints[end] && bones[boneName]) {
      const direction = {
        x: keypoints[end][0] - keypoints[start][0],
        y: keypoints[end][1] - keypoints[start][1],
        z: (keypoints[end][2] || 0) - (keypoints[start][2] || 0)
      }
      
      // 计算四元数旋转
      const quaternion = this.calculateRotation(direction)
      bones[boneName].quaternion.copy(quaternion)
    }
  }

  private render() {
    this.gl.clear(this.gl.COLOR_BUFFER_BIT | this.gl.DEPTH_BUFFER_BIT)
    
    // 更新动画
    if (this.animationMixer) {
      this.animationMixer.update(0.016) // 假设60fps
    }
    
    // 渲染模型
    this.model.traverse((object: any) => {
      if (object.isMesh) {
        this.renderMesh(object)
      }
    })
  }

  private renderMesh(mesh: any) {
    // 设置着色器变量
    const modelViewMatrix = matrix4.create()
    const projectionMatrix = matrix4.create()
    
    this.gl.uniformMatrix4fv(
      this.gl.getUniformLocation(this.program, 'uModelViewMatrix'),
      false,
      modelViewMatrix
    )
    
    this.gl.uniformMatrix4fv(
      this.gl.getUniformLocation(this.program, 'uProjectionMatrix'),
      false,
      projectionMatrix
    )
    
    // 绘制网格
    this.gl.drawElements(
      this.gl.TRIANGLES,
      mesh.geometry.index.count,
      this.gl.UNSIGNED_SHORT,
      0
    )
  }

  private createShader(type: number, source: string): webgl.WebGLShader {
    const shader = this.gl.createShader(type)
    this.gl.shaderSource(shader, source)
    this.gl.compileShader(shader)

    if (!this.gl.getShaderParameter(shader, this.gl.COMPILE_STATUS)) {
      console.error('着色器编译错误:', this.gl.getShaderInfoLog(shader))
      this.gl.deleteShader(shader)
      throw new Error('着色器编译失败')
    }

    return shader
  }

  private parseGLTF(data: any): any {
    // 解析GLTF模型数据
    const model = {
      meshes: [],
      skeleton: {
        bones: {}
      }
    }

    // 解析网格
    data.meshes?.forEach((mesh: any) => {
      const vertices = new Float32Array(mesh.primitives[0].attributes.POSITION)
      const normals = new Float32Array(mesh.primitives[0].attributes.NORMAL)
      const indices = new Uint16Array(mesh.primitives[0].indices)

      model.meshes.push({
        geometry: {
          vertices,
          normals,
          indices,
          index: { count: indices.length }
        }
      })
    })

    // 解析骨骼
    data.nodes?.forEach((node: any) => {
      if (node.name && node.translation) {
        model.skeleton.bones[node.name] = {
          position: {
            x: node.translation[0],
            y: node.translation[1],
            z: node.translation[2]
          },
          quaternion: {
            x: 0, y: 0, z: 0, w: 1
          }
        }
      }
    })

    return model
  }

  private calculateRotation(direction: { x: number, y: number, z: number }): any {
    // 计算旋转四元数
    const up = { x: 0, y: 1, z: 0 }
    const angle = Math.atan2(direction.y, Math.sqrt(direction.x * direction.x + direction.z * direction.z))
    const axisAngle = quaternion.fromAxisAngle(up, angle)
    return axisAngle
  }
} 