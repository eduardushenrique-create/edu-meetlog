export interface Status {
  state: 'IDLE' | 'RECORDING' | 'PROCESSING' | 'ERROR' | 'PAUSED';
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
  output_folder: string;
}

export interface Label {
  id: string;
  name: string;
  color: string;
}

export interface Meeting {
  id: string;
  name: string;
  date: string;
  duration: number | string;
  status: 'pending' | 'processing' | 'done' | 'failed';
  archived?: boolean;
  labels?: string[];
  suggested_labels?: string[];
  client_id?: string | null;
  meeting_kind?: 'internal' | 'external' | null;
  person_ids?: string[];
}

export interface Client {
  id: string;
  name: string;
  aliases: string[];
  description: string;
  labels: string[];
  active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Person {
  id: string;
  name: string;
  email?: string;
  aliases: string[];
  notes?: string;
  labels: string[];
  client_ids: string[];
  is_temporary: boolean;
  voice_profile_id?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Stakeholder {
  id: string;
  client_id: string;
  person_id: string;
  role: string;
  influence_level: string;
  notes?: string;
  labels: string[];
  is_primary: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ActionItemEvidence {
  meeting_id?: string | null;
  segment_id?: string | null;
  excerpt: string;
  timestamp_start?: number | null;
  timestamp_end?: number | null;
  source: string;
}

export interface ActionItem {
  id: string;
  title: string;
  client_id?: string | null;
  meeting_id?: string | null;
  assignee_person_id?: string | null;
  suggested_assignee_person_id?: string | null;
  status: string;
  priority: string;
  due_date?: string | null;
  labels: string[];
  notes?: string;
  evidence: ActionItemEvidence[];
  source: string;
  created_at?: string;
  updated_at?: string;
}

export interface ClientIndicators {
  client_id: string;
  reference_date: string;
  weekly_minutes: number;
  monthly_minutes: number;
  weekly_external_minutes: number;
  weekly_internal_minutes: number;
  monthly_external_minutes: number;
  monthly_internal_minutes: number;
  meeting_count: number;
  weekly_meeting_ids: string[];
  monthly_meeting_ids: string[];
  open_action_items: number;
  total_action_items: number;
}

export interface TranscriptSegment {
  id?: number | string;
  start: number;
  end: number;
  source: 'mic' | 'system';
  speaker: string;
  text: string;
}

export interface ElectronAPI {
  startRecording: () => Promise<{ success: boolean; message: string }>;
  stopRecording: () => Promise<{ success: boolean; message: string; duration?: number }>;
  getStatus: () => Promise<Status>;
  getMeetings: () => Promise<Meeting[]>;
  getTranscript: (meetingId: string) => Promise<{
    final_transcript?: { segments: TranscriptSegment[] };
    segments: TranscriptSegment[];
    complete?: boolean;
  }>;
  getSettings: () => Promise<Settings>;
  updateSettings: (settings: Settings) => Promise<{ success: boolean; message: string }>;
  onRecordingToggle: (callback: (recording: boolean) => void) => void;
  minimizeWindow: () => void;
  maximizeWindow: () => void;
  closeWindow: () => void;
  showOverlayPopup: (data: { title: string; message: string; action?: 'start' | 'stop' }) => void;
  closeOverlayPopup: () => void;
  selectOutputFolder: () => Promise<string | null>;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
