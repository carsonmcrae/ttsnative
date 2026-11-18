// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Execute an authorized agent request through the reader's existing playback controller.
 * Scope: Waits for the normal reader inputs, consumes each handoff once, and reports actual player
 *   state, including a browser's blocked autoplay. Acknowledgements use only a request capability.
 * Does NOT belong: Synthesis, exporting, or discovering an installed app.
 */
import { useEffect } from 'react';
import type { PlaybackController, PlayerDocument } from '@/features/player/controller';
import { acknowledgeRead, takeReadRequest } from './readRequest';
import type { AgentReadRequest, ReadResult } from './readRequest';

async function execute(
  controller: PlaybackController,
  document: PlayerDocument,
  start: number,
  request: AgentReadRequest,
): Promise<void> {
  let status: ReadResult = 'opened';
  let errorCode: string | undefined;
  try {
    let interrupted = false;
    for (const apply of [
      () => controller.load(document, start, false),
      () => controller.setVoice(request.voiceId),
      () => controller.setPace(request.pace),
    ]) {
      await apply();
      if (controller.getState().document?.id !== request.documentId) {
        interrupted = true;
        break;
      }
    }
    if (interrupted) {
      status = 'failed';
      errorCode = 'playback_interrupted';
    } else if (request.autoplay) {
      await controller.play();
      const state = controller.getState();
      if (state.document?.id !== request.documentId) {
        status = 'failed';
        errorCode = 'playback_interrupted';
      } else if (state.status === 'playing' || state.status === 'ended') {
        status = 'playing';
      } else if (state.status === 'error') {
        status = 'failed';
        errorCode = 'playback_failed';
      } else {
        status = 'user_action_required';
        errorCode = state.autoplayBlocked ? 'autoplay_blocked' : 'playback_interrupted';
      }
    }
  } catch {
    status = 'failed';
    errorCode = 'playback_failed';
  }
  await acknowledgeRead(request, status, errorCode);
}

export function useAgentRead(
  controller: PlaybackController,
  document: PlayerDocument,
  start: number,
  ready: boolean,
): void {
  useEffect(() => {
    if (!ready) return;
    const request = takeReadRequest(document.id);
    if (!request) return;
    // Consumption precedes async work: React's effect replay cannot start the request twice.
    void execute(controller, document, start, request).catch(() => undefined);
  }, [controller, document, ready, start]);
}

export function useFailedAgentRead(documentId: string | undefined, failed: boolean): void {
  useEffect(() => {
    if (!documentId || !failed) return;
    const request = takeReadRequest(documentId);
    if (request)
      void acknowledgeRead(request, 'failed', 'document_load_failed').catch(() => undefined);
  }, [documentId, failed]);
}
