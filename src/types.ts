export interface Status {
  state: 'IDLE' | 'RECORDING' | 'PROCESSING' | 'ERROR';
  recording_duration: number;
  mic_enabled: boolean;
  system_enabled: boolean;
  queue_stats: {
    pending: number;
    processing: number;
    done: number;
    failed: number;
  };
  settings: Settings;
}

export interface Settings {
  mic_enabled: boolean;
  system_enabled: boolean;
  model: string;
  workers: number;
  auto_start: boolean;
}

export interface Meeting {
  id: string;
  date: string;
  duration: number;
  status: 'pending' | 'processing' | 'done' | 'failed';
}

export interface TranscriptSegment {
  id: number;
  start: number;
  end: number;
  speaker: 'user' | 'other';
  text: string;
}

export interface ElectronAPI {
  startRecording: () => Promise<{ success: boolean; message: string }>;
  stopRecording: () => Promise<{ success: boolean; message: string; duration?: number }>;
  getStatus: () => Promise<Status>;
  getMeetings: () => Promise<Meeting[]>;
  getTranscript: (meetingId: string) => Promise<{ segments: TranscriptSegment[] }>;
  getSettings: () => Promise<Settings>;
  updateSettings: (settings: Settings) => Promise<{ success: boolean; message: string }>;
  onRecordingToggle: (callback: (recording: boolean) => void) => void;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}