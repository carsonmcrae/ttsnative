// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Connect a ready reader's normal document and skip rules to an agent handoff.
 * Scope: Waits for saved preferences and styling, and explains an actual autoplay refusal.
 * Does NOT belong: Rendering document text or implementing another playback controller.
 */
import type { DocumentDetail } from '@/api/types';
import type { PlayerDocument } from '@/features/player/controller';
import { usePlayer } from '@/features/player/PlayerProvider';
import { useAgentRead, useFailedAgentRead } from './useAgentRead';

export function AgentReader({
  document,
  progress,
  stylesReady,
  stylesFailed,
}: Readonly<{
  document: PlayerDocument;
  progress: DocumentDetail['progress'];
  stylesReady: boolean;
  stylesFailed: boolean;
}>) {
  const { controller, state, preferencesReady } = usePlayer();
  useAgentRead(controller, document, progress?.segmentIndex ?? 0, preferencesReady && stylesReady);
  useFailedAgentRead(document.id, stylesFailed);
  return state.document?.id === document.id && state.autoplayBlocked ? (
    <p role="status">Press Play to allow audio.</p>
  ) : null;
}
