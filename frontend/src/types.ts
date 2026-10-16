export interface FileInfo {
  name: string;
  path: string;
  ext: string;
  is_3d: boolean;
}

export interface PreviewState {
  inputFolder: string;
  outputFolder: string;
  sameFolder: boolean;
  invertTriangles: boolean;
  solidColor: string;
  logoPath: string;
  logoScale: number;
  logoOpacity: number;
  logoPosX: number;
  logoPosY: number;
  text: string;
  textPosX: number;
  textPosY: number;
  textColor: string;
  fontPath: string;
  fontScale: number;
  hasOutline: boolean;
  outlineColor: string;
  outlineThickness: number;
  opacity: number;
  yaw: number;
  pitch: number;
  modelColor?: string;
  theme: "light" | "dark";
}

export interface RenderPreviewResult {
  dataUrl?: string;
  width?: number;
  height?: number;
  name?: string;
  error?: string;
}

export interface ScanFolderResult {
  files: FileInfo[];
  total: number;
}

export interface PyWebViewApi {
  get_initial_state: () => Promise<Partial<PreviewState>>;
  browse_input_folder: () => Promise<string>;
  browse_output_folder: () => Promise<string>;
  browse_logo: () => Promise<string>;
  browse_font: () => Promise<string>;
  open_folder: (path: string) => Promise<void>;
  scan_folder: (path: string) => Promise<ScanFolderResult>;
  render_preview: (
    filePath: string,
    config: PreviewState
  ) => Promise<RenderPreviewResult>;
  start_batch: (
    inputFolder: string,
    outputFolder: string,
    config: PreviewState
  ) => Promise<{ success: number; failed: number }>;
  cancel_batch: () => Promise<void>;
  save_settings: (settings: PreviewState) => Promise<void>;
}

declare global {
  interface Window {
    pywebview?: {
      api?: PyWebViewApi;
    };
    __onBatchProgress?: (current: number, total: number, message: string) => void;
    __onBatchFinished?: (
      success: number,
      failed: number,
      errors: string[],
      cancelled: boolean
    ) => void;
  }
}
