import { ConnectionStatus, RealtimeEvent, RealtimeEventType } from '../types/realtime';

type EventHandler = (event: RealtimeEvent) => void;
type StatusHandler = (status: ConnectionStatus) => void;

export class FinGraphWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private status: ConnectionStatus = 'DISCONNECTED';
  private eventHandlers: Map<string, Set<EventHandler>> = new Map();
  private statusHandlers: Set<StatusHandler> = new Set();
  private reconnectAttempts: number = 0;
  private maxReconnectDelay: number = 30000;
  private reconnectTimeoutId: any = null;
  private processedEventIds: Set<string> = new Set();
  private maxEventIdCache: number = 500;
  private shouldReconnect: boolean = true;

  constructor(customUrl?: string) {
    if (customUrl) {
      this.url = customUrl;
    } else {
      const apiBase =
        (typeof process !== 'undefined' && process.env?.REACT_APP_API_BASE_URL) ||
        (typeof window !== 'undefined' && (window as any).__ENV__?.REACT_APP_API_BASE_URL) ||
        'http://localhost:8000';

      const wsProtocol = apiBase.startsWith('https') ? 'wss:' : 'ws:';
      const hostPart = apiBase.replace(/^https?:\/\//, '');
      this.url = `${wsProtocol}//${hostPart}/api/v1/ws`;
    }
  }

  public connect(tokenOverride?: string): void {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const token = tokenOverride || localStorage.getItem('fingraph_token');
    if (!token) {
      this.setStatus('DISCONNECTED');
      return;
    }

    const wsUrl = `${this.url}?token=${encodeURIComponent(token)}`;
    this.shouldReconnect = true;
    this.setStatus('CONNECTING');

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.setStatus('LIVE');
        this.reconnectAttempts = 0;
        this.send({ action: 'subscribe', channels: ['alerts', 'risk', 'transactions', 'graph'] });
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const parsed: RealtimeEvent = JSON.parse(event.data);
          this.handleIncomingEvent(parsed);
        } catch (err) {
          console.debug('Failed to parse WebSocket message:', err);
        }
      };

      this.ws.onerror = (error) => {
        console.debug('WebSocket error encountered:', error);
      };

      this.ws.onclose = (event) => {
        this.setStatus('DISCONNECTED');
        this.ws = null;
        if (this.shouldReconnect) {
          this.scheduleReconnect();
        }
      };
    } catch (err) {
      this.setStatus('DISCONNECTED');
      if (this.shouldReconnect) {
        this.scheduleReconnect();
      }
    }
  }

  public disconnect(): void {
    this.shouldReconnect = false;
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
      this.reconnectTimeoutId = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setStatus('DISCONNECTED');
  }

  public send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  public watchAccount(accountId: string): void {
    this.send({ action: 'watch_account', account_id: accountId });
  }

  public on(eventType: RealtimeEventType | '*', handler: EventHandler): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)!.add(handler);

    return () => {
      this.eventHandlers.get(eventType)?.delete(handler);
    };
  }

  public onStatusChange(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    handler(this.status);
    return () => {
      this.statusHandlers.delete(handler);
    };
  }

  public getStatus(): ConnectionStatus {
    return this.status;
  }

  private setStatus(status: ConnectionStatus): void {
    this.status = status;
    this.statusHandlers.forEach((h) => h(status));
  }

  private handleIncomingEvent(event: RealtimeEvent): void {
    if (event.event_id && this.processedEventIds.has(event.event_id)) {
      return;
    }
    if (event.event_id) {
      this.processedEventIds.add(event.event_id);
      if (this.processedEventIds.size > this.maxEventIdCache) {
        const first = this.processedEventIds.values().next().value;
        if (first) this.processedEventIds.delete(first);
      }
    }

    if (event.event === 'system.ping') {
      this.send({ action: 'ping' });
    }

    const specific = this.eventHandlers.get(event.event);
    if (specific) {
      specific.forEach((h) => h(event));
    }

    const wildcard = this.eventHandlers.get('*');
    if (wildcard) {
      wildcard.forEach((h) => h(event));
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimeoutId) {
      clearTimeout(this.reconnectTimeoutId);
    }

    const baseDelay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), this.maxReconnectDelay);
    const jitter = baseDelay * (0.9 + Math.random() * 0.2);
    this.reconnectAttempts++;

    this.reconnectTimeoutId = setTimeout(() => {
      this.connect();
    }, jitter);
  }
}

export const realtimeClient = new FinGraphWebSocketClient();
