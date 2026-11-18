// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: A reading request handed to this UI by an authorized local agent.
 * Scope: Request-scoped claim/acknowledgement calls and an in-memory handoff to the reader.
 *   Neither the agent's general credential nor request capabilities go into persistent storage.
 * Does NOT belong: Document importing, playback, or desktop activation.
 */
import { api } from '@/api/client';

export interface AgentReadRequest {
  requestId: string;
  documentId: string;
  voiceId: string;
  pace: number;
  autoplay: boolean;
  ackToken: string;
}

export type ReadResult = 'opened' | 'playing' | 'user_action_required' | 'failed';

const pending = new Map<string, AgentReadRequest>();

export function claimRead(ticket: string): Promise<AgentReadRequest> {
  return api('/api/agent-reader/claim', { method: 'POST', json: { ticket } });
}

export function handToReader(request: AgentReadRequest): void {
  pending.set(request.documentId, request);
}

export function takeReadRequest(documentId: string): AgentReadRequest | undefined {
  const request = pending.get(documentId);
  pending.delete(documentId);
  return request;
}

export function acknowledgeRead(
  request: AgentReadRequest,
  status: ReadResult,
  errorCode?: string,
): Promise<void> {
  return api('/api/agent-reader/ack', {
    method: 'POST',
    json: { requestId: request.requestId, ackToken: request.ackToken, status, errorCode },
  });
}
