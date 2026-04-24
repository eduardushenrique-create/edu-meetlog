import { useState, useEffect, useRef } from 'react';
import './types';

type Tab = 'dashboard' | 'meetings' | 'transcription' | 'settings';

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function formatSec(s: number): string {
  const m = Math.floor(s / 60).toString().padStart(2, '0');
  const ss = (s % 60).toString().padStart(2, '0');
  return `${m}:${ss}`;
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="relative inline-block w-10 h-5.5 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="opacity-0 w-0 h-0"
      />
      <span
        className={`absolute inset-0 rounded-full transition-all duration-200 border ${
          checked ? 'bg-blue-600 border-blue-600' : 'bg-gray-700 border-gray-600'
        }`}
      >
        <span
          className={`absolute left-0.5 top-0.5 w-4 h-4 bg-gray-400 rounded-full transition-all duration-200 ${
            checked ? 'translate-x-5 bg-white' : ''
          }`}
        />
      </span>
    </label>
  );
}

interface Meeting {
  id: string;
  name: string;
  date: string;
  duration: string;
  status: 'done' | 'processing' | 'failed' | 'pending';
  segments: number;
}

interface Segment {
  id: number;
  start: number;
  speaker: string;
  text: string;
}

const MOCK_MEETINGS: Meeting[] = [
  { id: '1', name: 'Sprint Planning Q2', date: '24 abr, 14:32', duration: '48:12', status: 'done', segments: 34 },
  { id: '2', name: 'Reunião com Cliente', date: '24 abr, 10:05', duration: '1:12:44', status: 'done', segments: 87 },
  { id: '3', name: 'Daily Standup', date: '23 abr, 09:00', duration: '14:22', status: 'processing', segments: 0 },
  { id: '4', name: 'Revisão de Design', date: '22 abr, 15:17', duration: '33:09', status: 'done', segments: 41 },
  { id: '5', name: 'Entrevista Dev Senior', date: '21 abr, 11:00', duration: '55:30', status: 'failed', segments: 0 },
];

const MOCK_SEGMENTS: Segment[] = [
  { id: 1, start: 0, speaker: 'USER', text: 'Bom dia a todos, vamos começar a reunião de sprint planning.' },
  { id: 2, start: 8, speaker: 'OTHER', text: 'Bom dia! Estou com o backlog atualizado aqui.' },
  { id: 3, start: 18, speaker: 'USER', text: 'Ótimo. Então, os itens prioritários para este sprint são o módulo de autenticação e a migração do banco.' },
  { id: 4, start: 35, speaker: 'OTHER', text: 'Concordo. A autenticação já está em andamento, deve ficar pronta até quinta.' },
  { id: 5, start: 52, speaker: 'USER', text: 'E a migração? Tem algum bloqueio?' },
  { id: 6, start: 61, speaker: 'OTHER', text: 'Sim, precisamos de acesso ao ambiente de staging. Ainda não tivemos resposta do infra.' },
  { id: 7, start: 78, speaker: 'USER', text: 'Vou seguir isso. Mais algum ponto antes de definirmos os pontos?' },
  { id: 8, start: 91, speaker: 'OTHER', text: 'Acho que vale incluir os testes de integração também. Estão atrasados.' },
  { id: 9, start: 108, speaker: 'USER', text: 'Faz sentido. Vamos adicionar como item de 5 pontos.' },
  { id: 10, start: 122, speaker: 'OTHER', text: 'Ótimo. Eu fico responsável por isso.' },
];

function SidebarItem({
  label,
  icon,
  active,
  onClick,
  badge,
}: {
  label: string;
  icon: string;
  active: boolean;
  onClick: () => void;
  badge?: number;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left flex items-center gap-2.5 px-3 py-2 rounded-md border-none cursor-pointer transition-all relative ${
        active
          ? 'bg-blue-500/20 text-blue-400 font-semibold'
          : 'bg-transparent text-gray-500 font-normal hover:bg-gray-800/50'
      }`}
      style={{ fontSize: '13px', fontFamily: 'Inter, sans-serif' }}
    >
      <span style={{ fontSize: '14px' }}>{icon}</span>
      <span className="flex-1">{label}</span>
      {badge != null && (
        <span className="bg-blue-600 text-white rounded-full px-1.5 py-0.5 text-xs font-semibold">
          {badge}
        </span>
      )}
      {active && (
        <span
          className="absolute left-0 top-1/4 h-3/5 w-0.5 rounded bg-blue-500"
        />
      )}
    </button>
  );
}

function Dashboard({
  isRecording,
  timer,
  status,
  onToggle,
  micEnabled,
  sysEnabled,
}: {
  isRecording: boolean;
  timer: string;
  status: { pending: number; processing: number; done: number; failed: number };
  onToggle: () => void;
  micEnabled: boolean;
  sysEnabled: boolean;
}) {
  return (
    <div className="p-7 h-full flex flex-col gap-7">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs tracking-widest text-gray-600 font-semibold mb-1">STATUS</div>
          <div className={`flex items-center text-sm font-semibold ${isRecording ? 'text-red-400' : 'text-green-400'}`}>
            <span
              className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${
                isRecording ? 'bg-red-500 shadow-red-500/50' : 'bg-green-500'
              }`}
              style={isRecording ? { boxShadow: '0 0 6px #ef4444' } : {}}
            />
            {isRecording ? 'GRAVANDO' : 'PARADO'}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs tracking-widest text-gray-600 font-semibold mb-1">FONTE</div>
          <div className="flex gap-1.5">
            <span
              className={`px-2 py-0.5 rounded text-xs font-semibold font-mono ${
                micEnabled
                  ? 'bg-green-500/10 text-green-400 border border-green-500/25'
                  : 'bg-gray-900 text-gray-700 border border-gray-800'
              }`}
            >
              MIC
            </span>
            <span
              className={`px-2 py-0.5 rounded text-xs font-semibold font-mono ${
                sysEnabled
                  ? 'bg-blue-500/10 text-blue-400 border border-blue-500/25'
                  : 'bg-gray-900 text-gray-700 border border-gray-800'
              }`}
            >
              SYS
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center gap-5">
        <div
          className={`font-mono text-5xl font-semibold tracking-widest ${isRecording ? 'text-red-400' : 'text-gray-200'}`}
          style={{ lineHeight: 1, letterSpacing: '2px' }}
        >
          {timer}
        </div>

        <div className="relative mt-2">
          {isRecording && (
            <div
              className="absolute inset-0 rounded-full animate-ping"
              style={{
                border: '2px solid rgba(239,68,68,0.5)',
                animation: 'pulse-ring 1.4s ease-out infinite',
              }}
            />
          )}
          <button
            onClick={onToggle}
            className={`w-22 h-22 rounded-full border-none cursor-pointer flex items-center justify-center transition-all ${
              isRecording
                ? 'bg-gradient-to-br from-red-400 to-red-700 shadow-red-500/30'
                : 'bg-gradient-to-br from-blue-500 to-blue-700 shadow-blue-500/20'
            }`}
            style={{
              width: '88px',
              height: '88px',
              boxShadow: isRecording
                ? '0 0 32px rgba(239,68,68,0.35), 0 4px 20px rgba(0,0,0,0.5)'
                : '0 0 32px rgba(37,99,235,0.25), 0 4px 20px rgba(0,0,0,0.5)',
            }}
          >
            {isRecording ? (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                <rect x="5" y="5" width="14" height="14" rx="2" />
              </svg>
            ) : (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                <circle cx="12" cy="12" r="6" />
              </svg>
            )}
          </button>
        </div>

        <div className="text-xs text-gray-600 flex items-center gap-2">
          <span>{isRecording ? 'Clique para parar' : 'Clique para iniciar'}</span>
          <kbd
            className="px-1.5 py-0.5 bg-gray-900 border border-gray-800 rounded text-gray-600 font-mono text-xs"
            style={{ fontSize: '10px' }}
          >
            ⌃⌥R
          </kbd>
        </div>
      </div>

      <div>
        <div className="text-xs tracking-widest text-gray-600 font-semibold mb-2.5">FILA DE TRANSCRIÇÃO</div>
        <div className="grid grid-cols-4 gap-2">
          {[
            { label: 'Pendentes', value: status.pending, color: '#f59e0b' },
            { label: 'Processando', value: status.processing, color: '#3b82f6' },
            { label: 'Concluídos', value: status.done, color: '#22c55e' },
            { label: 'Falhas', value: status.failed, color: '#ef4444' },
          ].map((item) => (
            <div
              key={item.label}
              className="bg-gray-950 border border-gray-900 rounded-md p-2.5"
            >
              <div
                className="text-2xl font-bold font-mono"
                style={{ color: item.value > 0 ? item.color : '#2a2a2a' }}
              >
                {item.value}
              </div>
              <div className="text-xs text-gray-700 mt-0.5 font-medium uppercase">
                {item.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Meetings({
  meetings,
  onOpen,
  onDelete,
}: {
  meetings: Meeting[];
  onOpen: (m: Meeting) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="p-7 h-full flex flex-col">
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="text-xs tracking-widest text-gray-600 font-semibold">REUNIÕES</div>
          <div className="text-lg font-semibold mt-0.5">{meetings.length} gravações</div>
        </div>
        <button
          className="bg-gray-900 border border-gray-800 text-gray-500 rounded-md px-3 py-1.5 text-xs cursor-pointer font-sans"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          Exportar todas
        </button>
      </div>
      <div className="flex-1 overflow-y-auto flex flex-col gap-1">
        {meetings.map((m) => (
          <div
            key={m.id}
            className="flex items-center p-3 rounded-md border border-gray-950 bg-gray-950 cursor-pointer transition-all gap-3"
            style={{ borderColor: '#181818' }}
            onMouseEnter={(e) => {
              const target = e.currentTarget as HTMLElement;
              target.style.borderColor = '#2a2a2a';
            }}
            onMouseLeave={(e) => {
              const target = e.currentTarget as HTMLElement;
              target.style.borderColor = '#181818';
            }}
          >
            <div className="flex-1 min-w-0" onClick={() => onOpen(m)}>
              <div
                className="text-sm font-medium text-gray-200 mb-0.5 truncate"
                style={{
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {m.name}
              </div>
              <div className="flex gap-3 items-center">
                <span className="text-xs text-gray-600">{m.date}</span>
                <span className="text-xs text-gray-700 font-mono">{m.duration}</span>
                {m.status === 'processing' && (
                  <span className="text-xs text-amber-500 bg-amber-500/10 px-1.5 py-0.5 rounded font-semibold">
                    PROCESSANDO
                  </span>
                )}
                {m.status === 'failed' && (
                  <span className="text-xs text-red-400 bg-red-500/10 px-1.5 py-0.5 rounded font-semibold">
                    FALHA
                  </span>
                )}
              </div>
            </div>
            <div className="flex gap-1.5 flex-shrink-0">
              {m.status === 'done' && (
                <button
                  className="bg-transparent border border-gray-800 text-gray-600 rounded px-2 py-1 text-xs cursor-pointer font-sans transition-all"
                  onClick={(e) => e.stopPropagation()}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#3b82f6';
                    e.currentTarget.style.color = '#93b4fc';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#222';
                    e.currentTarget.style.color = '#555';
                  }}
                >
                  Export
                </button>
              )}
              <button
                className="bg-transparent border border-gray-800 text-gray-600 rounded px-2 py-1 text-xs cursor-pointer font-sans transition-all"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(m.id);
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#ef4444';
                  e.currentTarget.style.color = '#f87171';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#222';
                  e.currentTarget.style.color = '#555';
                }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Transcription({
  meeting,
  segments,
  onBack,
}: {
  meeting: Meeting | null;
  segments: Segment[];
  onBack: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const text = segments.map((s) => `[${formatSec(s.start)}] ${s.speaker}: ${s.text}`).join('\n');
    navigator.clipboard?.writeText(text).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-7 h-full flex flex-col">
      <div className="mb-5">
        <button
          onClick={onBack}
          className="bg-transparent border-none text-gray-600 text-xs cursor-pointer flex items-center gap-1 mb-2.5 px-0 font-sans"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 5l-7 7 7 7" />
          </svg>
          Meetings
        </button>
        <div className="flex items-end justify-between">
          <div>
            <div className="text-xs tracking-widest text-gray-600 font-semibold">TRANSCRIÇÃO</div>
            <div className="text-lg font-semibold mt-0.5">{meeting?.name}</div>
            <div className="text-xs text-gray-600 mt-0.5">
              {meeting?.date} · {meeting?.duration}
            </div>
          </div>
          <div className="flex gap-1.5">
            <button
              onClick={handleCopy}
              className="px-3 py-1.5 text-xs rounded-md cursor-pointer font-sans transition-all border"
              style={{
                background: copied ? 'rgba(34,197,94,0.1)' : '#1a1a1a',
                borderColor: copied ? 'rgba(34,197,94,0.3)' : '#2a2a2a',
                color: copied ? '#4ade80' : '#888',
              }}
            >
              {copied ? '✓ Copiado' : 'Copiar'}
            </button>
            <button
              className="bg-gray-900 border border-gray-800 text-gray-500 rounded-md px-3 py-1.5 text-xs cursor-pointer font-sans"
            >
              Export .txt
            </button>
            <button
              className="bg-gray-900 border border-gray-800 text-gray-500 rounded-md px-3 py-1.5 text-xs cursor-pointer font-sans"
            >
              Export .json
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto font-mono text-sm flex flex-col gap-0.5">
        {segments.map((seg) => (
          <div
            key={seg.id}
            className="p-1.5 rounded"
            style={{
              borderLeft: `2px solid ${
                seg.speaker === 'USER'
                  ? 'rgba(74,222,128,0.3)'
                  : 'rgba(147,180,252,0.3)'
              }`,
              marginLeft: seg.speaker === 'OTHER' ? '24px' : '0',
            }}
          >
            <span className="text-gray-700 text-xs mr-2.5">[{formatSec(seg.start)}]</span>
            <span
              className="font-semibold mr-2 text-xs"
              style={{
                color: seg.speaker === 'USER' ? '#4ade80' : '#93b4fc',
              }}
            >
              {seg.speaker}:
            </span>
            <span className="text-gray-400">{seg.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface SettingsState {
  mic_enabled: boolean;
  system_enabled: boolean;
  model: string;
  workers: number;
  auto_start: boolean;
}

function SettingsPanel({
  settings,
  onChange,
  onSave,
  saved,
}: {
  settings: SettingsState;
  onChange: (s: SettingsState) => void;
  onSave: () => void;
  saved: boolean;
}) {
  return (
    <div className="p-7 h-full overflow-y-auto">
      <div className="mb-6">
        <div className="text-xs tracking-widest text-gray-600 font-semibold">CONFIGURAÇÕES</div>
        <div className="text-lg font-semibold mt-0.5">Preferências</div>
      </div>

      <div className="mb-6">
        <div className="text-xs tracking-widest text-gray-700 font-semibold mb-2.5 pb-1.5 border-b border-gray-950">
          CAPTURA DE ÁUDIO
        </div>
        <div className="flex flex-col gap-0.5">
          {[
            { key: 'mic_enabled', label: 'Microfone', sub: 'Captura entrada de voz local' },
            { key: 'system_enabled', label: 'Áudio do Sistema', sub: 'Captura saída de áudio (loopback)' },
          ].map((item) => (
            <div
              key={item.key}
              className="flex items-center justify-between p-3 bg-gray-950 rounded-md border border-gray-900"
            >
              <div>
                <div className="text-sm font-medium">{item.label}</div>
                <div className="text-xs text-gray-600 mt-0.5">{item.sub}</div>
              </div>
              <Toggle
                checked={settings[item.key as keyof SettingsState] as boolean}
                onChange={(v) => onChange({ ...settings, [item.key]: v })}
              />
            </div>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <div className="text-xs tracking-widest text-gray-700 font-semibold mb-2.5 pb-1.5 border-b border-gray-950">
          TRANSCRIÇÃO
        </div>
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center justify-between p-3 bg-gray-950 rounded-md border border-gray-900">
            <div>
              <div className="text-sm font-medium">Modelo Whisper</div>
              <div className="text-xs text-gray-600 mt-0.5">Modelo de reconhecimento de fala</div>
            </div>
            <select
              value={settings.model}
              onChange={(e) => onChange({ ...settings, model: e.target.value })}
              className="bg-gray-900 border border-gray-800 text-gray-200 rounded px-2 py-1 text-xs cursor-pointer font-mono"
            >
              {['tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3'].map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center justify-between p-3 bg-gray-950 rounded-md border border-gray-900">
            <div>
              <div className="text-sm font-medium">Workers</div>
              <div className="text-xs text-gray-600 mt-0.5">Processos paralelos (1–8)</div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => onChange({ ...settings, workers: Math.max(1, settings.workers - 1) })}
                className="w-6 h-6 rounded border border-gray-800 bg-gray-900 text-gray-500 cursor-pointer text-sm"
              >
                −
              </button>
              <span className="font-mono text-sm font-semibold w-5 text-center">{settings.workers}</span>
              <button
                onClick={() => onChange({ ...settings, workers: Math.min(8, settings.workers + 1) })}
                className="w-6 h-6 rounded border border-gray-800 bg-gray-900 text-gray-500 cursor-pointer text-sm"
              >
                +
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="mb-7">
        <div className="text-xs tracking-widest text-gray-700 font-semibold mb-2.5 pb-1.5 border-b border-gray-950">
          INICIALIZAÇÃO
        </div>
        <div className="flex items-center justify-between p-3 bg-gray-950 rounded-md border border-gray-900">
          <div>
            <div className="text-sm font-medium">Auto-start</div>
            <div className="text-xs text-gray-600 mt-0.5">Iniciar gravação ao abrir o app</div>
          </div>
          <Toggle
            checked={settings.auto_start}
            onChange={(v) => onChange({ ...settings, auto_start: v })}
          />
        </div>
      </div>

      <div className="mb-7">
        <div className="text-xs tracking-widest text-gray-700 font-semibold mb-2.5 pb-1.5 border-b border-gray-950">
          ATALHOS
        </div>
        <div className="flex flex-col gap-1.5">
          {[
            { keys: '⌃⌥R', desc: 'Iniciar / Parar gravação' },
            { keys: '⌃⌥S', desc: 'Abrir aplicativo' },
          ].map((h) => (
            <div
              key={h.keys}
              className="flex items-center justify-between p-2 bg-gray-950 rounded-md border border-gray-900"
            >
              <span className="text-xs text-gray-500">{h.desc}</span>
              <kbd
                className="px-2 py-0.5 bg-gray-900 border border-gray-800 rounded text-gray-600 font-mono"
                style={{ fontSize: '12px' }}
              >
                {h.keys}
              </kbd>
            </div>
          ))}
        </div>
      </div>

      <button
        onClick={onSave}
        className="rounded-md px-5 py-2.5 text-sm font-semibold cursor-pointer font-sans transition-all border"
        style={{
          background: saved ? 'rgba(34,197,94,0.15)' : '#1d4ed8',
          borderColor: saved ? 'rgba(34,197,94,0.3)' : '#2563eb',
          color: saved ? '#4ade80' : '#fff',
        }}
      >
        {saved ? '✓ Salvo' : 'Salvar configurações'}
      </button>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard');
  const [isRecording, setIsRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [meetings, setMeetings] = useState<Meeting[]>(MOCK_MEETINGS);
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [settings, setSettings] = useState<SettingsState>({
    mic_enabled: true,
    system_enabled: true,
    model: 'large-v3',
    workers: 2,
    auto_start: false,
  });
  const [saved, setSaved] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const status = { pending: 1, processing: 0, done: 28, failed: 1 };

  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => setSeconds((s) => s + 1), 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      if (seconds > 0) setSeconds(0);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRecording]);

  const timer = formatTime(seconds);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const openMeeting = (m: Meeting) => {
    setSelectedMeeting(m);
    setTab('transcription');
  };

  const deleteMeeting = (id: string) => {
    setMeetings((prev) => prev.filter((m) => m.id !== id));
  };

  return (
    <div className="flex h-screen bg-black text-white font-sans" style={{ background: '#080808' }}>
      <div
        className="w-46 p-4 border-r border-gray-950 flex flex-col"
        style={{ borderColor: '#141414', background: '#080808', width: '184px', flexShrink: 0 }}
      >
        <div className="mb-5 pl-2.5">
          <div className="text-sm font-bold text-gray-200" style={{ letterSpacing: '-0.01em' }}>
            Edu MeetLog
          </div>
          <div className="text-xs text-gray-800 mt-0.5">v0.1 · local</div>
        </div>

        <div className="flex flex-col gap-0.5 flex-1">
          <SidebarItem
            label="Dashboard"
            icon="◉"
            active={tab === 'dashboard'}
            onClick={() => {
              setTab('dashboard');
              setSelectedMeeting(null);
            }}
          />
          <SidebarItem
            label="Meetings"
            icon="≡"
            active={tab === 'meetings' || tab === 'transcription'}
            onClick={() => {
              setTab('meetings');
              setSelectedMeeting(null);
            }}
            badge={meetings.filter((m) => m.status === 'done').length}
          />
          <SidebarItem
            label="Settings"
            icon="⚙"
            active={tab === 'settings'}
            onClick={() => setTab('settings')}
          />
        </div>

        <div className="border-t border-gray-950 pt-3 mt-3" style={{ borderColor: '#141414' }}>
          <div className="flex items-center gap-1.5 pl-2.5">
            <div
              className="w-1.5 h-1.5 rounded-full"
              style={{
                background: isRecording ? '#ef4444' : '#22c55e',
                boxShadow: isRecording ? '0 0 5px #ef4444' : 'none',
              }}
            />
            <span
              className="text-xs text-gray-600 font-mono"
              style={{ fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}
            >
              {isRecording ? 'REC' : 'IDLE'}
            </span>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden" style={{ background: '#080808' }}>
        {tab === 'dashboard' && (
          <Dashboard
            isRecording={isRecording}
            timer={timer}
            status={status}
            onToggle={() => setIsRecording((r) => !r)}
            micEnabled={settings.mic_enabled}
            sysEnabled={settings.system_enabled}
          />
        )}
        {tab === 'meetings' && (
          <Meetings meetings={meetings} onOpen={openMeeting} onDelete={deleteMeeting} />
        )}
        {tab === 'transcription' && (
          <Transcription
            meeting={selectedMeeting}
            segments={MOCK_SEGMENTS}
            onBack={() => {
              setTab('meetings');
              setSelectedMeeting(null);
            }}
          />
        )}
        {tab === 'settings' && (
          <SettingsPanel
            settings={settings}
            onChange={setSettings}
            onSave={handleSave}
            saved={saved}
          />
        )}
      </div>
    </div>
  );
}