import { useState, useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import type { ActionItem, Client, ClientIndicators, Person, Stakeholder } from './types';
import './types';

type Tab = 'dashboard' | 'meetings' | 'transcription' | 'clients' | 'people' | 'action-items' | 'settings' | 'calendar';

const API_URL = 'http://127.0.0.1:8000';

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

function DarkWindow({ children }: { children: ReactNode }) {
  return (
    <div className="dark-window">
      <div className="dark-window-titlebar" style={{ display: 'flex', justifyContent: 'space-between', paddingRight: '0' }}>
        <div className="dark-window-title" style={{ paddingLeft: '12px' }}>Edu MeetLog</div>
        <div className="window-controls" style={{ display: 'flex', height: '100%' }}>
          <div className="window-control minimize" onClick={window.electronAPI?.minimizeWindow} title="Minimizar">
            <svg viewBox="0 0 10 1" width="10" height="1"><path d="M0,0 L10,0" stroke="currentColor" strokeWidth="1" shapeRendering="crispEdges"/></svg>
          </div>
          <div className="window-control maximize" onClick={window.electronAPI?.maximizeWindow} title="Maximizar">
            <svg viewBox="0 0 10 10" width="10" height="10"><path d="M0,0 L10,0 L10,10 L0,10 Z" fill="none" stroke="currentColor" strokeWidth="1" shapeRendering="crispEdges"/></svg>
          </div>
          <div className="window-control close" onClick={window.electronAPI?.closeWindow} title="Fechar">
            <svg viewBox="0 0 10 10" width="10" height="10"><path d="M0,0 L10,10 M10,0 L0,10" stroke="currentColor" strokeWidth="1" shapeRendering="crispEdges"/></svg>
          </div>
        </div>
      </div>
      <div className="dark-window-content">{children}</div>
    </div>
  );
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
  id?: string | number;
  start: number;
  end?: number;
  source?: 'mic' | 'system';
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
  isPaused,
  timer,
  status,
  onToggle,
  onPauseResume,
  micEnabled,
  sysEnabled,
  realtimeSegments = [],
  wsConnected = false,
}: {
  isRecording: boolean;
  isPaused: boolean;
  timer: string;
  status: { pending: number; processing: number; done: number; failed: number };
  onToggle: () => void;
  onPauseResume: () => void;
  micEnabled: boolean;
  sysEnabled: boolean;
  realtimeSegments?: Segment[];
  wsConnected?: boolean;
}) {
  return (
    <div className="h-full flex flex-col gap-7" style={{ padding: '28px 32px' }}>
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
          className={`font-mono text-[52px] font-semibold tracking-widest ${isRecording ? 'text-red-400' : 'text-gray-200'}`}
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
                pointerEvents: 'none',
              }}
            />
          )}
<button
            onClick={onToggle}
            className={`w-22 h-22 rounded-full border-none cursor-pointer flex items-center justify-center transition-all z-10 ${
              isRecording
                ? 'bg-gradient-to-br from-red-400 to-red-700 shadow-red-500/30'
                : 'bg-gradient-to-br from-blue-500 to-blue-700 shadow-blue-500/20'
            }`}
            style={{
              width: '88px',
              height: '88px',
              position: 'relative',
              zIndex: 10,
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
        {isRecording && (
          <button
            onClick={onPauseResume}
            className="px-3 py-1.5 rounded-md text-xs border border-gray-800 bg-gray-950 text-gray-300 hover:border-gray-700 cursor-pointer"
          >
            {isPaused ? 'Continuar' : 'Pausar'}
          </button>
        )}
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

      {isRecording && (
        <div>
          <div className="text-xs tracking-widest text-gray-600 font-semibold mb-2.5">TRANSCRIÇÃO EM TEMPO REAL</div>
          <div className="bg-gray-950 border border-gray-900 rounded-md p-3 max-h-32 overflow-y-auto">
            <div className="flex items-center gap-2 mb-2">
              <span
                className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}
              />
              <span className="text-xs text-gray-600">
                {wsConnected ? 'Conectado' : 'Desconectado'}
              </span>
            </div>
            {realtimeSegments.length > 0 ? (
              <div className="flex flex-col gap-1">
                {realtimeSegments.slice(-5).map((seg, i) => (
                  <div key={i} className="text-sm">
                    <span
                      className={`px-1.5 py-0.5 rounded text-xs font-medium mr-1.5 ${
                        (seg.source || seg.speaker).toLowerCase() === 'system'
                          ? 'bg-blue-500/20 text-blue-400'
                          : 'bg-green-500/20 text-green-400'
                      }`}
                    >
                      {(seg.source || seg.speaker).toUpperCase()}
                    </span>
                    <span className="text-gray-300">{seg.text}</span>
                  </div>
                ))}
              </div>
            ) : (
              <span className="text-xs text-gray-700">Aguardando transcrição...</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Meetings({
  meetings,
  onOpen,
  onDelete,
  onBulkDelete,
  onBulkArchive,
  labels,
  selectedIds,
  onToggleSelection,
  onClearSelection
}: {
  meetings: Meeting[];
  onOpen: (m: Meeting) => void;
  onDelete: (id: string) => void;
  onBulkDelete?: (ids: string[]) => void;
  onBulkArchive?: (ids: string[]) => void;
  labels?: any[];
  selectedIds?: string[];
  onToggleSelection?: (id: string) => void;
  onClearSelection?: () => void;
  onSelectAll?: (ids: string[]) => void;
}) {
  const [showArchived, setShowArchived] = useState(false);
  const [filterLabel, setFilterLabel] = useState<string>('');

  const filteredMeetings = meetings.filter(m => {
    if (showArchived && !m.archived) return false;
    if (!showArchived && m.archived) return false;
    if (filterLabel && !(m.labels || []).includes(filterLabel)) return false;
    return true;
  });

  return (
    <div className="h-full flex flex-col" style={{ padding: '28px 32px' }}>
      <div className="flex items-center justify-between mb-5">
        <div>
          <div className="text-xs tracking-widest text-gray-600 font-semibold">REUNIÕES</div>
          <div className="text-lg font-semibold mt-0.5">{filteredMeetings.length} gravações</div>
        </div>
        <div className="flex gap-2 items-center">
          <select 
            className="bg-transparent border border-gray-700 text-gray-400 rounded px-2 py-1 text-xs outline-none cursor-pointer"
            value={showArchived ? 'archived' : 'active'}
            onChange={(e) => setShowArchived(e.target.value === 'archived')}
          >
            <option value="active">Ativas</option>
            <option value="archived">Arquivadas</option>
          </select>
          <select 
            className="bg-transparent border border-gray-700 text-gray-400 rounded px-2 py-1 text-xs outline-none cursor-pointer"
            value={filterLabel}
            onChange={(e) => setFilterLabel(e.target.value)}
          >
            <option value="">Todas as Etiquetas</option>
            {(labels || []).map(l => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
          {selectedIds && selectedIds.length > 0 && (
            <>
              <button
                className="bg-red-900/50 text-red-400 border border-red-800 rounded-md px-3 py-1.5 text-xs cursor-pointer hover:bg-red-800 transition-colors"
                onClick={() => onBulkDelete?.(selectedIds)}
              >
                Excluir {selectedIds.length}
              </button>
              {!showArchived && (
                <button
                  className="bg-gray-800 text-gray-300 border border-gray-700 rounded-md px-3 py-1.5 text-xs cursor-pointer hover:bg-gray-700 transition-colors"
                  onClick={() => onBulkArchive?.(selectedIds)}
                >
                  Arquivar {selectedIds.length}
                </button>
              )}
              <button
                className="text-gray-500 hover:text-gray-300 text-xs cursor-pointer bg-transparent border-none"
                onClick={() => onClearSelection?.()}
              >
                Cancelar
              </button>
            </>
          )}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto flex flex-col gap-1">
        {filteredMeetings.length > 0 && (
          <div className="flex items-center p-2 mb-2 bg-gray-900 border border-gray-800 rounded-md">
            <input 
              type="checkbox" 
              checked={selectedIds?.length === filteredMeetings.length && filteredMeetings.length > 0} 
              onChange={(e) => {
                if (e.target.checked) {
                  onSelectAll?.(filteredMeetings.map(m => m.id));
                } else {
                  onClearSelection?.();
                }
              }}
              className="w-4 h-4 cursor-pointer accent-blue-600 mx-1"
            />
            <span className="text-xs text-gray-400 font-medium ml-2">Selecionar Tudo ({filteredMeetings.length})</span>
          </div>
        )}
        {filteredMeetings.length === 0 && (
          <div className="text-gray-500 text-sm text-center mt-10">
            Nenhuma transcrição encontrada.
          </div>
        )}
        {filteredMeetings.map((m) => (
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
            <div className="flex items-center" onClick={(e) => e.stopPropagation()}>
              <input 
                type="checkbox" 
                checked={selectedIds?.includes(m.id) || false} 
                onChange={() => onToggleSelection?.(m.id)}
                className="w-4 h-4 cursor-pointer accent-blue-600"
              />
            </div>
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
                {m.labels?.map(lblId => {
                  const lbl = labels?.find(l => l.id === lblId);
                  if (!lbl) return null;
                  return (
                    <span key={lblId} className="text-[10px] px-1.5 py-0.5 rounded-full font-medium" style={{ background: lbl.color + '20', color: lbl.color, border: `1px solid ${lbl.color}40` }}>
                      {lbl.name}
                    </span>
                  );
                })}
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
  labels,
  clients,
  onBack,
  onLabelsUpdated,
  onClassifyMeeting,
}: {
  meeting: Meeting | null;
  segments: Segment[];
  labels?: any[];
  clients: Client[];
  onBack: () => void;
  onLabelsUpdated?: () => void;
  onClassifyMeeting?: (meetingId: string, payload: { client_id?: string | null; meeting_kind?: 'internal' | 'external' | '' }) => Promise<void>;
}) {
  const [suggestedLabels, setSuggestedLabels] = useState<any[]>([]);
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [clientId, setClientId] = useState('');
  const [meetingKind, setMeetingKind] = useState<'internal' | 'external' | ''>('');

  useEffect(() => {
    setClientId(meeting?.client_id || '');
    setMeetingKind(meeting?.meeting_kind || '');
  }, [meeting?.id, meeting?.client_id, meeting?.meeting_kind]);

  useEffect(() => {
    if (meeting?.suggested_labels && labels) {
      const found = labels.filter(l => meeting.suggested_labels!.includes(l.id));
      const newSuggestions = found.filter(l => !(meeting.labels || []).includes(l.id));
      setSuggestedLabels(newSuggestions);
    } else {
      setSuggestedLabels([]);
    }
  }, [meeting?.id, meeting?.suggested_labels, meeting?.labels, labels]);

  const handleSuggest = async () => {
    if (!meeting) return;
    setIsSuggesting(true);
    try {
      const res = await fetch(`${API_URL}/meetings/${meeting.id}/suggest-labels`, { method: 'POST' });
      const data = await res.json();
      if (data.suggested_label_ids) {
        const found = (labels || []).filter(l => data.suggested_label_ids.includes(l.id));
        const newSuggestions = found.filter(l => !(meeting.labels || []).includes(l.id));
        setSuggestedLabels(newSuggestions);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleAcceptSuggestion = async (labelId: string) => {
    if (!meeting) return;
    const current = meeting.labels || [];
    const updated = [...current, labelId];
    try {
      await fetch(`${API_URL}/meetings/${meeting.id}/labels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label_ids: updated })
      });
      setSuggestedLabels(prev => prev.filter(l => l.id !== labelId));
      meeting.labels = updated; 
      onLabelsUpdated?.();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRejectSuggestion = (labelId: string) => {
    setSuggestedLabels(prev => prev.filter(l => l.id !== labelId));
  };

  const handleManualAddLabel = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const labelId = e.target.value;
    if (!labelId || !meeting) return;
    const current = meeting.labels || [];
    if (current.includes(labelId)) {
      e.target.value = "";
      return;
    }
    const updated = [...current, labelId];
    try {
      await fetch(`${API_URL}/meetings/${meeting.id}/labels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label_ids: updated })
      });
      meeting.labels = updated; 
      onLabelsUpdated?.();
      e.target.value = "";
    } catch (err) {
      console.error(err);
    }
  };
  
  const handleRemoveLabel = async (labelId: string) => {
    if (!meeting) return;
    const current = meeting.labels || [];
    const updated = current.filter(id => id !== labelId);
    try {
      await fetch(`${API_URL}/meetings/${meeting.id}/labels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ label_ids: updated })
      });
      meeting.labels = updated; 
      onLabelsUpdated?.();
    } catch (err) {
      console.error(err);
    }
  };
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const text = segments.map((s) => `[${formatSec(s.start)}] ${s.speaker}: ${s.text}`).join('\n');
    try {
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).catch(() => {
          fallbackCopy(text);
        });
      } else {
        fallbackCopy(text);
      }
    } catch {
      fallbackCopy(text);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const fallbackCopy = (text: string) => {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
    } catch {
      console.error('Copy failed');
    }
    document.body.removeChild(textarea);
  };

  return (
    <div className="h-full flex flex-col" style={{ padding: '28px 32px' }}>
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
              onClick={handleSuggest}
              disabled={isSuggesting}
              className="px-3 py-1.5 text-xs rounded-md cursor-pointer font-sans transition-all border bg-purple-900/30 border-purple-800 text-purple-300 hover:bg-purple-800/50 flex items-center gap-1.5"
            >
              {isSuggesting ? '⏳ Pensando...' : '🪄 Sugerir Rótulos'}
            </button>
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
          </div>
        </div>
      </div>

      <div className="flex gap-2 mb-3 items-center flex-wrap">
        {meeting?.labels?.map(lblId => {
          const lbl = labels?.find(l => l.id === lblId);
          if (!lbl) return null;
          return (
            <span key={lblId} className="flex items-center text-[11px] px-2 py-0.5 rounded-full font-medium" style={{ background: lbl.color + '20', color: lbl.color, border: `1px solid ${lbl.color}40` }}>
              {lbl.name}
              <button onClick={() => handleRemoveLabel(lblId)} className="ml-1 text-current opacity-60 hover:opacity-100 bg-transparent border-none cursor-pointer p-0 font-bold">&times;</button>
            </span>
          );
        })}
        <select
          onChange={handleManualAddLabel}
          defaultValue=""
          className="bg-transparent border border-gray-700 text-gray-400 rounded px-1 py-0.5 text-[10px] outline-none cursor-pointer hover:border-gray-500 transition-colors"
        >
          <option value="" disabled>+ Adicionar Rótulo</option>
          {(labels || []).filter(l => !(meeting?.labels || []).includes(l.id)).map(l => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </select>
      </div>

      <div className="mb-4 grid gap-3" style={{ gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 220px) auto' }}>
        <select
          value={clientId}
          onChange={(e) => setClientId(e.target.value)}
          className="bg-gray-950 border border-gray-800 text-gray-200 rounded-md px-3 py-2 text-sm outline-none"
        >
          <option value="">Associar cliente</option>
          {clients.map((client) => (
            <option key={client.id} value={client.id}>{client.name}</option>
          ))}
        </select>
        <select
          value={meetingKind}
          onChange={(e) => setMeetingKind(e.target.value as 'internal' | 'external' | '')}
          className="bg-gray-950 border border-gray-800 text-gray-200 rounded-md px-3 py-2 text-sm outline-none"
        >
          <option value="">Tipo da reunião</option>
          <option value="external">Externa com cliente</option>
          <option value="internal">Interna sobre cliente</option>
        </select>
        <button
          onClick={async () => {
            if (!meeting || !onClassifyMeeting) return;
            await onClassifyMeeting(meeting.id, { client_id: clientId || null, meeting_kind: meetingKind });
          }}
          className="bg-blue-600 hover:bg-blue-700 text-white rounded-md px-3 py-2 text-sm font-medium border-none cursor-pointer"
        >
          Salvar vínculo
        </button>
      </div>

      {suggestedLabels.length > 0 && (
        <div className="mb-4 p-3 bg-purple-900/10 border border-purple-900/50 rounded-md">
          <div className="text-xs font-semibold text-purple-300 mb-2">Sugestões da IA:</div>
          <div className="flex flex-wrap gap-2">
            {suggestedLabels.map(l => (
              <div key={l.id} className="flex items-center gap-2 px-2 py-1 rounded text-xs font-medium bg-gray-900 border border-gray-800 text-gray-200">
                <span className="w-2 h-2 rounded-full" style={{ background: l.color }} />
                {l.name}
                <div className="flex items-center ml-3 gap-3 border-l border-gray-700 pl-3">
                  <button onClick={() => handleAcceptSuggestion(l.id)} className="flex items-center gap-1 bg-green-500/10 border border-green-500/20 text-green-500 hover:bg-green-500/20 rounded px-2 py-0.5 cursor-pointer font-bold text-[10px]" title="Aceitar">✓ Aceitar</button>
                  <button onClick={() => handleRejectSuggestion(l.id)} className="flex items-center gap-1 bg-red-500/10 border border-red-500/20 text-red-500 hover:bg-red-500/20 rounded px-2 py-0.5 cursor-pointer font-bold text-[10px]" title="Recusar">✕ Recusar</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-3 mb-3">
        {['user', 'system'].map((speaker) => (
          <div key={speaker} className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{
                background: speaker === 'user' ? '#4ade80' : '#3b82f6',
              }}
            />
            <span className="text-xs text-gray-600 capitalize">{speaker}</span>
          </div>
        ))}
      </div>

<div className="flex-1 overflow-y-auto font-mono text-sm flex flex-col gap-0.5">
        {segments.map((seg, index) => (
          <div
            key={String(seg.id ?? `${seg.source ?? seg.speaker}-${seg.start}-${seg.end ?? seg.start}-${index}`)}
            className="p-1.5 rounded"
            style={{
              borderLeft: `2px solid ${
                seg.speaker?.toLowerCase() === 'user' || seg.speaker?.toLowerCase() === 'mic'
                  ? '#4ade80'
                  : '#3b82f6'
              }`,
              background: 'rgba(255,255,255,0.02)',
            }}
          >
            <span className="text-gray-700 text-xs mr-2.5">[{formatSec(seg.start)}]</span>
            <span
              className="font-semibold mr-2 text-xs"
              style={{
                color: seg.speaker?.toLowerCase() === 'user' || seg.speaker?.toLowerCase() === 'mic' ? '#4ade80' : '#3b82f6',
              }}
            >
              {seg.speaker?.toUpperCase() || 'SPEAKER'}
            </span>
<span className="text-gray-300">{seg.text}</span>
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
  output_folder?: string;
}

function SettingsPanel({
  settings,
  onChange,
  onSave,
  saved,
  labels = [],
  onAddLabel,
  onRemoveLabel
}: {
  settings: SettingsState;
  onChange: (s: SettingsState) => void;
  onSave: () => void;
  saved: boolean;
  labels?: any[];
  onAddLabel?: (name: string, color: string) => void;
  onRemoveLabel?: (id: string) => void;
}) {
  const [newLabelName, setNewLabelName] = useState('');
  const [newLabelColor, setNewLabelColor] = useState('#3b82f6');
  return (
    <div className="h-full overflow-y-auto" style={{ padding: '28px 32px' }}>
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
          ETIQUETAS (LABELS)
        </div>
        <div className="flex flex-col gap-2">
          <div className="flex gap-2 mb-2">
            <input 
              type="text" 
              placeholder="Nome da etiqueta" 
              value={newLabelName}
              onChange={(e) => setNewLabelName(e.target.value)}
              className="flex-1 bg-gray-900 border border-gray-800 text-gray-200 rounded px-3 py-1.5 text-sm"
            />
            <input 
              type="color" 
              value={newLabelColor}
              onChange={(e) => setNewLabelColor(e.target.value)}
              className="w-8 h-8 rounded border border-gray-800 cursor-pointer p-0 bg-gray-900"
            />
            <button 
              onClick={() => {
                if (newLabelName && onAddLabel) {
                  onAddLabel(newLabelName, newLabelColor);
                  setNewLabelName('');
                }
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white rounded px-3 py-1.5 text-sm font-medium border-none cursor-pointer"
            >
              Adicionar
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {labels.map(l => (
              <div key={l.id} className="flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium" style={{ background: l.color + '20', color: l.color, border: `1px solid ${l.color}40` }}>
                {l.name}
                <button onClick={() => onRemoveLabel?.(l.id)} className="bg-transparent border-none text-current opacity-70 hover:opacity-100 cursor-pointer p-0 ml-1">
                  &times;
                </button>
              </div>
            ))}
            {labels.length === 0 && <span className="text-xs text-gray-600">Nenhuma etiqueta criada.</span>}
          </div>
        </div>
      </div>

      <div className="mb-7">
        <div className="text-xs tracking-widest text-gray-700 font-semibold mb-2.5 pb-1.5 border-b border-gray-950">
          ATALHOS
        </div>
        <div className="flex flex-col gap-1.5">
          {[
            { keys: '⌃⌥R', desc: 'Iniciar / Parar gravação' },
            { keys: '⌃F12', desc: 'Parar gravação' },
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

function SectionHeader({
  eyebrow,
  title,
  subtitle,
  action,
}: {
  eyebrow: string;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-end justify-between mb-5 gap-4">
      <div>
        <div className="text-xs tracking-widest text-gray-600 font-semibold">{eyebrow}</div>
        <div className="text-lg font-semibold mt-0.5">{title}</div>
        {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
      </div>
      {action}
    </div>
  );
}

function ClientsPanel({
  clients,
  stakeholders,
  indicatorsByClient,
  onCreateClient,
}: {
  clients: Client[];
  stakeholders: Stakeholder[];
  indicatorsByClient: Record<string, ClientIndicators>;
  onCreateClient: (payload: { name: string; aliases: string[]; description: string }) => Promise<void>;
}) {
  const [name, setName] = useState('');
  const [aliases, setAliases] = useState('');
  const [description, setDescription] = useState('');

  return (
    <div className="h-full overflow-y-auto" style={{ padding: '28px 32px' }}>
      <SectionHeader
        eyebrow="FASE 4"
        title="Clientes"
        subtitle="Workspace local por cliente com stakeholders, volume de reunião e pendências."
      />

      <div className="grid gap-6" style={{ gridTemplateColumns: 'minmax(0, 320px) minmax(0, 1fr)' }}>
        <div className="bg-gray-950 border border-gray-900 rounded-xl p-4 h-fit">
          <div className="text-xs tracking-widest text-gray-600 font-semibold mb-3">NOVO CLIENTE</div>
          <div className="flex flex-col gap-3">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Nome do cliente"
              className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm"
            />
            <input
              value={aliases}
              onChange={(e) => setAliases(e.target.value)}
              placeholder="Aliases separados por vírgula"
              className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm"
            />
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Contexto, projeto, conta ou observações"
              rows={4}
              className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm resize-none"
            />
            <button
              onClick={async () => {
                if (!name.trim()) return;
                await onCreateClient({
                  name: name.trim(),
                  aliases: aliases.split(',').map((item) => item.trim()).filter(Boolean),
                  description: description.trim(),
                });
                setName('');
                setAliases('');
                setDescription('');
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white rounded-md px-3 py-2 text-sm font-medium border-none cursor-pointer"
            >
              Criar cliente
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-3">
          {clients.length === 0 && (
            <div className="text-sm text-gray-500">Nenhum cliente cadastrado ainda.</div>
          )}
          {clients.map((client) => {
            const clientStakeholders = stakeholders.filter((item) => item.client_id === client.id);
            const indicators = indicatorsByClient[client.id];
            return (
              <div key={client.id} className="bg-gray-950 border border-gray-900 rounded-xl p-4">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div>
                    <div className="text-base font-semibold text-gray-100">{client.name}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {client.aliases.length > 0 ? client.aliases.join(' • ') : 'Sem aliases cadastrados'}
                    </div>
                    {client.description && <div className="text-sm text-gray-400 mt-2">{client.description}</div>}
                  </div>
                  <span className={`px-2 py-1 rounded-full text-[10px] font-semibold border ${client.active ? 'text-green-400 border-green-500/30 bg-green-500/10' : 'text-gray-500 border-gray-700 bg-gray-900'}`}>
                    {client.active ? 'ATIVO' : 'INATIVO'}
                  </span>
                </div>

                <div className="grid grid-cols-2 xl:grid-cols-5 gap-2 mb-4">
                  {[
                    { label: 'Semana', value: `${indicators?.weekly_minutes ?? 0} min` },
                    { label: 'Mês', value: `${indicators?.monthly_minutes ?? 0} min` },
                    { label: 'Externo', value: `${indicators?.weekly_external_minutes ?? 0} min` },
                    { label: 'Interno', value: `${indicators?.weekly_internal_minutes ?? 0} min` },
                    { label: 'Pendências', value: String(indicators?.open_action_items ?? 0) },
                  ].map((item) => (
                    <div key={item.label} className="bg-black/30 border border-gray-900 rounded-lg px-3 py-2">
                      <div className="text-[10px] uppercase tracking-widest text-gray-600">{item.label}</div>
                      <div className="text-sm font-semibold text-gray-200 mt-1">{item.value}</div>
                    </div>
                  ))}
                </div>

                <div>
                  <div className="text-xs tracking-widest text-gray-600 font-semibold mb-2">STAKEHOLDERS</div>
                  <div className="flex flex-wrap gap-2">
                    {clientStakeholders.length > 0 ? clientStakeholders.map((item) => (
                      <span key={item.id} className="px-2 py-1 rounded-full text-xs text-blue-300 border border-blue-500/20 bg-blue-500/10">
                        {item.role} · {item.influence_level}
                      </span>
                    )) : <span className="text-xs text-gray-600">Nenhum stakeholder vinculado ainda.</span>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function PeoplePanel({
  people,
  clients,
  stakeholders,
  onCreatePerson,
  onCreateStakeholder,
}: {
  people: Person[];
  clients: Client[];
  stakeholders: Stakeholder[];
  onCreatePerson: (payload: { name: string; email: string; client_ids: string[]; is_temporary: boolean }) => Promise<void>;
  onCreateStakeholder: (payload: { client_id: string; person_id: string; role: string; influence_level: string; is_primary: boolean }) => Promise<void>;
}) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [clientId, setClientId] = useState('');
  const [temporary, setTemporary] = useState(false);
  const [stakeholderClientId, setStakeholderClientId] = useState('');
  const [stakeholderPersonId, setStakeholderPersonId] = useState('');
  const [role, setRole] = useState('Ponto focal');
  const [influence, setInfluence] = useState('medium');
  const [isPrimary, setIsPrimary] = useState(false);

  return (
    <div className="h-full overflow-y-auto" style={{ padding: '28px 32px' }}>
      <SectionHeader
        eyebrow="FASE 4"
        title="Pessoas e Stakeholders"
        subtitle="Memória local de participantes, contatos recorrentes e relações por cliente."
      />

      <div className="grid gap-6" style={{ gridTemplateColumns: 'minmax(0, 340px) minmax(0, 1fr)' }}>
        <div className="flex flex-col gap-4">
          <div className="bg-gray-950 border border-gray-900 rounded-xl p-4">
            <div className="text-xs tracking-widest text-gray-600 font-semibold mb-3">NOVA PESSOA</div>
            <div className="flex flex-col gap-3">
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nome" className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm" />
              <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="E-mail" className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm" />
              <select value={clientId} onChange={(e) => setClientId(e.target.value)} className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm">
                <option value="">Sem cliente principal</option>
                {clients.map((client) => <option key={client.id} value={client.id}>{client.name}</option>)}
              </select>
              <label className="flex items-center gap-2 text-sm text-gray-400">
                <input type="checkbox" checked={temporary} onChange={(e) => setTemporary(e.target.checked)} className="accent-blue-600" />
                Pessoa temporária / ainda não confirmada
              </label>
              <button
                onClick={async () => {
                  if (!name.trim()) return;
                  await onCreatePerson({
                    name: name.trim(),
                    email: email.trim(),
                    client_ids: clientId ? [clientId] : [],
                    is_temporary: temporary,
                  });
                  setName('');
                  setEmail('');
                  setClientId('');
                  setTemporary(false);
                }}
                className="bg-blue-600 hover:bg-blue-700 text-white rounded-md px-3 py-2 text-sm font-medium border-none cursor-pointer"
              >
                Criar pessoa
              </button>
            </div>
          </div>

          <div className="bg-gray-950 border border-gray-900 rounded-xl p-4">
            <div className="text-xs tracking-widest text-gray-600 font-semibold mb-3">VINCULAR STAKEHOLDER</div>
            <div className="flex flex-col gap-3">
              <select value={stakeholderClientId} onChange={(e) => setStakeholderClientId(e.target.value)} className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm">
                <option value="">Cliente</option>
                {clients.map((client) => <option key={client.id} value={client.id}>{client.name}</option>)}
              </select>
              <select value={stakeholderPersonId} onChange={(e) => setStakeholderPersonId(e.target.value)} className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm">
                <option value="">Pessoa</option>
                {people.map((person) => <option key={person.id} value={person.id}>{person.name}</option>)}
              </select>
              <input value={role} onChange={(e) => setRole(e.target.value)} placeholder="Papel" className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm" />
              <select value={influence} onChange={(e) => setInfluence(e.target.value)} className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm">
                <option value="low">Influência baixa</option>
                <option value="medium">Influência média</option>
                <option value="high">Influência alta</option>
                <option value="decision_maker">Decisor</option>
              </select>
              <label className="flex items-center gap-2 text-sm text-gray-400">
                <input type="checkbox" checked={isPrimary} onChange={(e) => setIsPrimary(e.target.checked)} className="accent-blue-600" />
                Stakeholder principal
              </label>
              <button
                onClick={async () => {
                  if (!stakeholderClientId || !stakeholderPersonId || !role.trim()) return;
                  await onCreateStakeholder({
                    client_id: stakeholderClientId,
                    person_id: stakeholderPersonId,
                    role: role.trim(),
                    influence_level: influence,
                    is_primary: isPrimary,
                  });
                  setStakeholderClientId('');
                  setStakeholderPersonId('');
                  setRole('Ponto focal');
                  setInfluence('medium');
                  setIsPrimary(false);
                }}
                className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-md px-3 py-2 text-sm font-medium border-none cursor-pointer"
              >
                Vincular stakeholder
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-3">
          {people.length === 0 && <div className="text-sm text-gray-500">Nenhuma pessoa registrada.</div>}
          {people.map((person) => {
            const personClients = clients.filter((client) => person.client_ids.includes(client.id));
            const personStakeholders = stakeholders.filter((item) => item.person_id === person.id);
            return (
              <div key={person.id} className="bg-gray-950 border border-gray-900 rounded-xl p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-base font-semibold text-gray-100">{person.name}</div>
                    <div className="text-xs text-gray-500 mt-1">{person.email || 'Sem e-mail cadastrado'}</div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-[10px] font-semibold border ${person.is_temporary ? 'text-amber-300 border-amber-500/30 bg-amber-500/10' : 'text-green-400 border-green-500/30 bg-green-500/10'}`}>
                    {person.is_temporary ? 'TEMPORÁRIA' : 'CONFIRMADA'}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {personClients.map((client) => (
                    <span key={client.id} className="px-2 py-1 rounded-full text-xs text-gray-300 border border-gray-800 bg-black/20">
                      {client.name}
                    </span>
                  ))}
                  {personClients.length === 0 && <span className="text-xs text-gray-600">Sem cliente associado.</span>}
                </div>
                <div className="mt-3 text-xs text-gray-400">
                  {personStakeholders.length > 0 ? personStakeholders.map((item) => item.role).join(' • ') : 'Ainda sem papel de stakeholder.'}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ActionItemsPanel({
  actionItems,
  clients,
  people,
  meetings,
  onCreateActionItem,
}: {
  actionItems: ActionItem[];
  clients: Client[];
  people: Person[];
  meetings: Meeting[];
  onCreateActionItem: (payload: { title: string; client_id?: string; meeting_id?: string; assignee_person_id?: string; priority: string }) => Promise<void>;
}) {
  const [title, setTitle] = useState('');
  const [clientId, setClientId] = useState('');
  const [meetingId, setMeetingId] = useState('');
  const [personId, setPersonId] = useState('');
  const [priority, setPriority] = useState('medium');

  const openItems = actionItems.filter((item) => item.status !== 'done' && item.status !== 'cancelled');

  return (
    <div className="h-full overflow-y-auto" style={{ padding: '28px 32px' }}>
      <SectionHeader
        eyebrow="FASE 4"
        title="Pendências"
        subtitle="Central local de follow-ups, responsáveis e itens em aberto por cliente."
        action={<div className="text-xs text-gray-500">{openItems.length} em aberto</div>}
      />

      <div className="grid gap-6" style={{ gridTemplateColumns: 'minmax(0, 340px) minmax(0, 1fr)' }}>
        <div className="bg-gray-950 border border-gray-900 rounded-xl p-4 h-fit">
          <div className="text-xs tracking-widest text-gray-600 font-semibold mb-3">NOVA PENDÊNCIA</div>
          <div className="flex flex-col gap-3">
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Descrição objetiva" className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm" />
            <select value={clientId} onChange={(e) => setClientId(e.target.value)} className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm">
              <option value="">Cliente opcional</option>
              {clients.map((client) => <option key={client.id} value={client.id}>{client.name}</option>)}
            </select>
            <select value={meetingId} onChange={(e) => setMeetingId(e.target.value)} className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm">
              <option value="">Reunião opcional</option>
              {meetings.map((meeting) => <option key={meeting.id} value={meeting.id}>{meeting.name}</option>)}
            </select>
            <select value={personId} onChange={(e) => setPersonId(e.target.value)} className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm">
              <option value="">Responsável opcional</option>
              {people.map((person) => <option key={person.id} value={person.id}>{person.name}</option>)}
            </select>
            <select value={priority} onChange={(e) => setPriority(e.target.value)} className="bg-gray-900 border border-gray-800 text-gray-100 rounded-md px-3 py-2 text-sm">
              <option value="low">Prioridade baixa</option>
              <option value="medium">Prioridade média</option>
              <option value="high">Prioridade alta</option>
            </select>
            <button
              onClick={async () => {
                if (!title.trim()) return;
                await onCreateActionItem({
                  title: title.trim(),
                  client_id: clientId || undefined,
                  meeting_id: meetingId || undefined,
                  assignee_person_id: personId || undefined,
                  priority,
                });
                setTitle('');
                setClientId('');
                setMeetingId('');
                setPersonId('');
                setPriority('medium');
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white rounded-md px-3 py-2 text-sm font-medium border-none cursor-pointer"
            >
              Criar pendência
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-3">
          {actionItems.length === 0 && <div className="text-sm text-gray-500">Nenhuma pendência cadastrada.</div>}
          {actionItems.map((item) => {
            const client = clients.find((entry) => entry.id === item.client_id);
            const person = people.find((entry) => entry.id === item.assignee_person_id);
            const meeting = meetings.find((entry) => entry.id === item.meeting_id);
            return (
              <div key={item.id} className="bg-gray-950 border border-gray-900 rounded-xl p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-base font-semibold text-gray-100">{item.title}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {client?.name || 'Sem cliente'} · {person?.name || 'Sem responsável'} · {meeting?.name || 'Sem reunião'}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <span className={`px-2 py-1 rounded-full text-[10px] font-semibold border ${item.priority === 'high' ? 'text-red-300 border-red-500/30 bg-red-500/10' : item.priority === 'medium' ? 'text-amber-300 border-amber-500/30 bg-amber-500/10' : 'text-blue-300 border-blue-500/30 bg-blue-500/10'}`}>
                      {item.priority.toUpperCase()}
                    </span>
                    <span className="px-2 py-1 rounded-full text-[10px] font-semibold border text-gray-300 border-gray-700 bg-black/30">
                      {(item.status || 'open').toUpperCase()}
                    </span>
                  </div>
                </div>
                {item.evidence?.length > 0 && (
                  <div className="mt-3 text-sm text-gray-400 border-l-2 border-blue-500/30 pl-3">
                    {item.evidence[0].excerpt}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard');
  const [isRecording, setIsRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [meetingSegments, setMeetingSegments] = useState<Segment[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [people, setPeople] = useState<Person[]>([]);
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([]);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [indicatorsByClient, setIndicatorsByClient] = useState<Record<string, ClientIndicators>>({});
  const [settings, setSettings] = useState<SettingsState>({
    mic_enabled: true,
    system_enabled: true,
    model: 'large-v3',
    workers: 2,
    auto_start: false,
    output_folder: '',
  });
  const [saved, setSaved] = useState(false);
  const [status, setStatus] = useState({ pending: 0, processing: 0, done: 0, failed: 0 });
  const [realtimeSegments, setRealtimeSegments] = useState<Segment[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [labels, setLabels] = useState<any[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const isRecordingRef = useRef(false);
  const settingsRef = useRef(settings);
  settingsRef.current = settings;

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/status`);
      if (res.ok) {
        const data = await res.json();
        setIsRecording(data.state === 'RECORDING');
        setSeconds(Math.floor(data.recording_duration));
        setStatus(data.queue_stats);
      }
    } catch (e) {
      console.error('API not reachable');
    }
  };

  const fetchMeetings = async () => {
    try {
      const res = await fetch(`${API_URL}/meetings`);
      if (res.ok) {
        const data = await res.json();
        setMeetings(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const performToggle = async () => {
    const current = isRecordingRef.current;
    console.log('performToggle called, current state:', current);
    try {
      const endpoint = current ? 'finalize' : 'start';
      const url = `${API_URL}/recording/${endpoint}`;
      console.log('Calling API:', url);
      
      const res = await fetch(url, { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: current ? undefined : JSON.stringify({
          mic_enabled: settingsRef.current.mic_enabled,
          system_enabled: settingsRef.current.system_enabled,
          segment_duration: 300
        })
      });
      
      console.log('Response status:', res.status);
      const data = await res.json();
      console.log('Response data:', data);
      
      if (data.success) {
        showToast(current ? 'Gravação finalizada com sucesso!' : 'Gravação iniciada!', 'success');
      } else {
        showToast(data.message || 'Erro na operação', 'error');
      }
      
      fetchStatus();
      if (current) {
        fetchMeetings();
      } else {
        setRealtimeSegments([]);
      }
    } catch (e) {
      console.error('Error in performToggle:', e);
      showToast('Falha na comunicação com o servidor local', 'error');
    }
  };

  const performPauseResume = async () => {
    try {
      const endpoint = isPaused ? 'resume' : 'pause';
      const res = await fetch(`${API_URL}/recording/${endpoint}`, { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast(isPaused ? 'Gravação continuada' : 'Gravação pausada', 'success');
        setIsPaused(!isPaused);
      } else {
        showToast(data.message || 'Erro ao alterar estado', 'error');
      }
      fetchStatus();
    } catch (e) {
      console.error('Error pausing/resuming:', e);
      showToast('Erro ao pausar/continuar', 'error');
    }
  };

  const handleToggleRecording = () => {
    console.log('Button clicked, isRecording:', isRecordingRef.current);
    performToggle();
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (window.electronAPI?.onRecordingToggle) {
      window.electronAPI.onRecordingToggle((recording: boolean) => {
        setIsRecording(recording);
        if (!recording) setSeconds(0);
      });
    }
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'F12') {
        e.preventDefault();
        performToggle();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  useEffect(() => {
    if (tab === 'meetings') {
      fetchMeetings();
    }
    if (tab === 'clients') {
      fetchClients();
      fetchStakeholders();
    }
    if (tab === 'people') {
      fetchPeople();
      fetchStakeholders();
      fetchClients();
    }
    if (tab === 'action-items') {
      fetchActionItems();
      fetchClients();
      fetchPeople();
      fetchMeetings();
    }
  }, [tab]);

  useEffect(() => {
    if (isRecording) {
      const ws = new WebSocket('ws://127.0.0.1:8000/ws/transcription');
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => setWsConnected(false);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'popup') {
            (window as any).electronAPI?.showOverlayPopup?.({ title: data.title, message: data.message, action: data.action });
            return;
          }
          if (data.final_transcript) {
            const merged = data.final_transcript?.segments;
            if (Array.isArray(merged) && isRecordingRef.current) {
              setRealtimeSegments(merged);
            }
          }
        } catch (e) {}
      };
      return () => ws.close();
    } else {
      setWsConnected(false);
    }
  }, [isRecording]);

  useEffect(() => {
    const loadInitSettings = async () => {
      try {
        const res = await fetch(`${API_URL}/settings`);
        if (res.ok) {
          const data = await res.json();
          setSettings(data);
        }
      } catch (e) {
        console.error(e);
      }
    };
    loadInitSettings();
  }, []);

  useEffect(() => {
    isRecordingRef.current = isRecording;
  }, [isRecording]);

  const timer = formatTime(seconds);

  const handleSave = async () => {
    try {
      await fetch(`${API_URL}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      console.error(e);
    }
  };

  const openMeeting = async (m: Meeting) => {
    try {
      const res = await fetch(`${API_URL}/transcripts/${m.id}`);
      if (res.ok) {
        const data = await res.json();
        const mergedSegments = data.final_transcript?.segments || [];
        setMeetingSegments(mergedSegments);
      } else {
        setMeetingSegments([]);
      }
    } catch (e) {
      setMeetingSegments([]);
    }
    setSelectedMeeting(m);
    setTab('transcription');
  };

  const fetchLabels = async () => {
    try {
      const res = await fetch(`${API_URL}/labels`);
      if (res.ok) setLabels(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchClients = async () => {
    try {
      const res = await fetch(`${API_URL}/clients`);
      if (!res.ok) return;
      const data: Client[] = await res.json();
      setClients(data);

      const indicatorEntries = await Promise.all(
        data.map(async (client) => {
          try {
            const indicatorsRes = await fetch(`${API_URL}/clients/${client.id}/indicators`);
            if (!indicatorsRes.ok) return [client.id, undefined] as const;
            return [client.id, await indicatorsRes.json()] as const;
          } catch {
            return [client.id, undefined] as const;
          }
        })
      );

      setIndicatorsByClient(
        Object.fromEntries(indicatorEntries.filter((entry): entry is readonly [string, ClientIndicators] => Boolean(entry[1])))
      );
    } catch (e) {
      console.error(e);
    }
  };

  const fetchPeople = async () => {
    try {
      const res = await fetch(`${API_URL}/people`);
      if (res.ok) setPeople(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchStakeholders = async () => {
    try {
      const res = await fetch(`${API_URL}/stakeholders`);
      if (res.ok) setStakeholders(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  const fetchActionItems = async () => {
    try {
      const res = await fetch(`${API_URL}/action-items`);
      if (res.ok) setActionItems(await res.json());
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchLabels();
    fetchClients();
    fetchPeople();
    fetchStakeholders();
    fetchActionItems();
  }, []);

  const handleAddLabel = async (name: string, color: string) => {
    try {
      await fetch(`${API_URL}/labels`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: `label_${Date.now()}`, name, color }),
      });
      fetchLabels();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRemoveLabel = async (id: string) => {
    try {
      await fetch(`${API_URL}/labels/${id}`, { method: 'DELETE' });
      fetchLabels();
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateClient = async (payload: { name: string; aliases: string[]; description: string }) => {
    try {
      const res = await fetch(`${API_URL}/clients`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('create client failed');
      showToast('Cliente criado com sucesso', 'success');
      await fetchClients();
    } catch (e) {
      console.error(e);
      showToast('Erro ao criar cliente', 'error');
    }
  };

  const handleCreatePerson = async (payload: { name: string; email: string; client_ids: string[]; is_temporary: boolean }) => {
    try {
      const res = await fetch(`${API_URL}/people`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('create person failed');
      showToast('Pessoa cadastrada', 'success');
      await fetchPeople();
    } catch (e) {
      console.error(e);
      showToast('Erro ao criar pessoa', 'error');
    }
  };

  const handleCreateStakeholder = async (payload: { client_id: string; person_id: string; role: string; influence_level: string; is_primary: boolean }) => {
    try {
      const res = await fetch(`${API_URL}/stakeholders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('create stakeholder failed');
      showToast('Stakeholder vinculado', 'success');
      await fetchStakeholders();
      await fetchClients();
    } catch (e) {
      console.error(e);
      showToast('Erro ao vincular stakeholder', 'error');
    }
  };

  const handleCreateActionItem = async (payload: { title: string; client_id?: string; meeting_id?: string; assignee_person_id?: string; priority: string }) => {
    try {
      const res = await fetch(`${API_URL}/action-items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...payload,
          status: 'open',
          source: 'manual',
        }),
      });
      if (!res.ok) throw new Error('create action item failed');
      showToast('Pendência criada', 'success');
      await fetchActionItems();
      await fetchClients();
    } catch (e) {
      console.error(e);
      showToast('Erro ao criar pendência', 'error');
    }
  };

  const handleClassifyMeeting = async (
    meetingId: string,
    payload: { client_id?: string | null; meeting_kind?: 'internal' | 'external' | '' }
  ) => {
    try {
      const res = await fetch(`${API_URL}/meetings/${meetingId}/classification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error('classify meeting failed');
      showToast('Reunião classificada', 'success');
      await fetchMeetings();
      await fetchClients();
      const updatedMeeting = meetings.find((item) => item.id === meetingId);
      if (updatedMeeting) {
        setSelectedMeeting({
          ...updatedMeeting,
          client_id: payload.client_id ?? null,
          meeting_kind: (payload.meeting_kind || null) as Meeting['meeting_kind'],
        });
      }
    } catch (e) {
      console.error(e);
      showToast('Erro ao classificar reunião', 'error');
    }
  };

  const toggleSelection = (id: string) => {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const clearSelection = () => setSelectedIds([]);
  
  const handleSelectAll = (ids: string[]) => {
    setSelectedIds(ids);
  };

  const handleBulkArchive = async (ids: string[]) => {
    if (!window.confirm(`Tem certeza que deseja arquivar ${ids.length} transcrição(ões)?`)) return;
    try {
      const res = await fetch(`${API_URL}/meetings/bulk-archive`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids }),
      });
      if (res.ok) {
        showToast(`${ids.length} transcrições arquivadas`, 'success');
        clearSelection();
        fetchMeetings();
      }
    } catch (e) {
      console.error(e);
      showToast('Erro ao arquivar', 'error');
    }
  };

  const handleBulkDelete = async (ids: string[]) => {
    if (!window.confirm(`Tem certeza que deseja excluir ${ids.length} transcrição(ões)?`)) return;
    try {
      const res = await fetch(`${API_URL}/meetings/bulk-delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids }),
      });
      if (res.ok) {
        showToast(`${ids.length} transcrições excluídas`, 'success');
        clearSelection();
        fetchMeetings();
      }
    } catch (e) {
      console.error(e);
      showToast('Erro ao excluir', 'error');
    }
  };

  const deleteMeeting = (id: string) => {
    handleBulkDelete([id]);
  };

  return (
    <div className="app-stage">
      <DarkWindow>
        <div className="flex h-full bg-black text-white font-sans" style={{ background: '#080808' }}>
      <div
        className="w-46 border-r border-gray-950 flex flex-col"
        style={{ borderColor: '#141414', background: '#080808', width: '184px', flexShrink: 0, padding: '16px 10px' }}
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
            label="Clientes"
            icon="#"
            active={tab === 'clients'}
            onClick={() => setTab('clients')}
            badge={clients.length}
          />
          <SidebarItem
            label="Pessoas"
            icon="@"
            active={tab === 'people'}
            onClick={() => setTab('people')}
            badge={people.length}
          />
          <SidebarItem
            label="Pendencias"
            icon=">"
            active={tab === 'action-items'}
            onClick={() => setTab('action-items')}
            badge={actionItems.filter((item) => item.status !== 'done' && item.status !== 'cancelled').length}
          />
          <SidebarItem
            label="Calendar"
            icon="📅"
            active={tab === 'calendar'}
            onClick={() => setTab('calendar')}
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
            isPaused={isPaused}
            timer={timer}
            status={status}
            onToggle={handleToggleRecording}
            onPauseResume={performPauseResume}
            micEnabled={settings.mic_enabled}
            sysEnabled={settings.system_enabled}
            realtimeSegments={realtimeSegments}
            wsConnected={wsConnected}
          />
        )}
        {tab === 'meetings' && (
          <Meetings 
            meetings={meetings} 
            onOpen={openMeeting} 
            onDelete={(id) => handleBulkDelete([id])}
            onBulkDelete={handleBulkDelete}
            onBulkArchive={handleBulkArchive}
            labels={labels}
            selectedIds={selectedIds}
            onToggleSelection={toggleSelection}
            onClearSelection={clearSelection}
            onSelectAll={handleSelectAll}
          />
        )}
        {tab === 'transcription' && (
          <Transcription
            meeting={selectedMeeting}
            segments={meetingSegments}
            labels={labels}
            clients={clients}
            onBack={() => {
              setTab('meetings');
              setSelectedMeeting(null);
            }}
            onLabelsUpdated={fetchMeetings}
            onClassifyMeeting={handleClassifyMeeting}
          />
        )}
        {tab === 'clients' && (
          <ClientsPanel
            clients={clients}
            stakeholders={stakeholders}
            indicatorsByClient={indicatorsByClient}
            onCreateClient={handleCreateClient}
          />
        )}
        {tab === 'people' && (
          <PeoplePanel
            people={people}
            clients={clients}
            stakeholders={stakeholders}
            onCreatePerson={handleCreatePerson}
            onCreateStakeholder={handleCreateStakeholder}
          />
        )}
        {tab === 'action-items' && (
          <ActionItemsPanel
            actionItems={actionItems}
            clients={clients}
            people={people}
            meetings={meetings}
            onCreateActionItem={handleCreateActionItem}
          />
        )}
        {tab === 'settings' && (
          <SettingsPanel
            settings={settings}
            onChange={setSettings}
            onSave={handleSave}
            saved={saved}
            labels={labels}
            onAddLabel={handleAddLabel}
            onRemoveLabel={handleRemoveLabel}
          />
        )}
        {tab === 'calendar' && (
          <div className="h-full flex flex-col items-center justify-center text-center p-8">
            <div className="w-16 h-16 rounded-2xl bg-gray-900 border border-gray-800 flex items-center justify-center text-2xl mb-4">
              📅
            </div>
            <h2 className="text-xl font-bold text-gray-200 mb-2">Integração com Google Calendar</h2>
            <p className="text-sm text-gray-500 max-w-sm mb-6">
              Sincronize sua agenda para iniciar gravações automaticamente e associar reuniões aos eventos correspondentes.
            </p>
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-md transition-colors cursor-pointer border-none opacity-50 cursor-not-allowed">
              Conectar Conta do Google (Em Breve)
            </button>
          </div>
        )}
      </div>
    </div>
      </DarkWindow>
      
      {toast && (
        <div 
          className="fixed bottom-4 right-4 px-4 py-3 rounded-lg shadow-lg text-sm font-medium transition-all duration-300 z-50 flex items-center gap-2"
          style={{
            background: toast.type === 'success' ? '#14532d' : '#7f1d1d',
            color: toast.type === 'success' ? '#86efac' : '#fca5a5',
            border: `1px solid ${toast.type === 'success' ? '#166534' : '#991b1b'}`,
            animation: 'slide-up 0.3s ease-out forwards'
          }}
        >
          {toast.type === 'success' ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6L9 17l-5-5"/></svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/></svg>
          )}
          {toast.message}
        </div>
      )}
    </div>
  );
}
