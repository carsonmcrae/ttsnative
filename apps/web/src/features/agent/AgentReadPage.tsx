// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
/**
 * Purpose: Consume a one-shot local-agent reading ticket and open the existing reader.
 * Scope: Removes the ticket from browser history immediately, claims it once even when React
 *   replays effects, and keeps the returned acknowledgement capability only in memory.
 * Does NOT belong: A general agent API credential, document processing, or a second audio player.
 */
import { BookOpen } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router';
import { describeError } from '@/api/client';
import { buttonClasses } from '@/components/ui/Button';
import { EmptyState, StatusRegion } from '@/components/ui/Feedback';
import { Spinner } from '@/components/ui/Spinner';
import type { AgentReadRequest } from './readRequest';
import { claimRead, handToReader } from './readRequest';

export default function AgentReadPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [ticket] = useState(() => location.hash.slice(1));
  const valid = /^[0-9a-f]{64}$/.test(ticket);
  const [error, setError] = useState<string | null>(
    valid ? null : 'This reading link is invalid. Ask your agent to create a new request.',
  );
  const claim = useRef<Promise<AgentReadRequest> | null>(null);

  useEffect(() => {
    // Keep React Router's own history bookkeeping; the secret is never needed in the URL again.
    history.replaceState(history.state, '', location.pathname + location.search);
    if (!valid) return undefined;
    let active = true;
    claim.current ??= claimRead(ticket);
    void claim.current.then(
      (request) => {
        if (!active) return;
        handToReader(request);
        void navigate(`/read/${encodeURIComponent(request.documentId)}`, { replace: true });
      },
      (failure: unknown) => {
        if (active) setError(describeError(failure));
      },
    );
    return () => {
      active = false;
    };
  }, [location.pathname, location.search, navigate, ticket, valid]);

  if (error) {
    return (
      <EmptyState
        icon={<BookOpen size={24} />}
        title="This reading request couldn't be opened"
        actions={
          <Link to="/library" className={buttonClasses('primary')}>
            Go to your library
          </Link>
        }
      >
        {error}
      </EmptyState>
    );
  }
  return (
    <StatusRegion label="Opening requested document">
      <Spinner size={24} />
    </StatusRegion>
  );
}
