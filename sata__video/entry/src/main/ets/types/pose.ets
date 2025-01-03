export interface Point2D {
  x: number
  y: number
}

export interface Size {
  width: number
  height: number
}

export interface Keypoint {
  x: number
  y: number
  score: number
}

export type KeypointArray = [number, number, number] // [x, y, score] 