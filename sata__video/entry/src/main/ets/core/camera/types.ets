export interface CameraContext {
  stageMode: boolean;
  surfaceId: string;
}

export interface PreviewConfig {
  width: number;
  height: number;
  format: number;
  frameRate: number;
  surfaceId?: string;
}

export interface CameraInfo {
  cameraId: string;
  cameraPosition: string;
  cameraType: string;
}

export interface CameraSession {
  start(): Promise<void>;
  stop(): Promise<void>;
  release(): Promise<void>;
  capture(): Promise<void>;
  resume(): Promise<void>;
  pause(): Promise<void>;
}

export interface CameraInput {
  open(): Promise<void>;
  close(): Promise<void>;
  createPreviewSession(config: PreviewConfig): Promise<CameraSession>;
  release(): Promise<void>;
  getSupportedPreviewFormats(): Promise<number[]>;
  getSupportedPhotoFormats(): Promise<number[]>;
  getSupportedVideoFormats(): Promise<number[]>;
}

export interface CameraManager {
  getSupportedCameras(): Promise<CameraInfo[]>;
  createCameraInput(cameraInfo: CameraInfo): Promise<CameraInput>;
}

export interface CameraDevice extends CameraInput {
  id: string;
  position: string;
  type: string;
} 