import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { PageRecord } from "../api/types";
import { WordBboxOverlay } from "../components/WordBboxOverlay";
import { diffLines } from "../lib/lineDiff";
import { LineDiffView } from "../lib/LineDiffView";
import {
  buildWordOffsetIndex,
  offsetToWord,
  wordToRange,
  type OcrWord,
} from "../lib/wordOffsets";

interface OcrPageResponse {
  text: string;
  text_key: string;
  words: OcrWord[];
}

export function TextReviewPage() {
  const { projectId = "", idx0: idx0Str = "0" } = useParams();
  const idx0 = Number(idx0Str);
  const queryClient = useQueryClient();

  const [splitSuffix, setSplitSuffix] = useState<string>("");
  const [text, setText] = useState<string>("");
  const [dirty, setDirty] = useState(false);
  const [activeWordIndex, setActiveWordIndex] = useState<number | null>(null);
  const [words, setWords] = useState<OcrWord[]>([]);
  // Re-OCR diff (P1 #7): snapshot of `text` taken via the reocr
  // mutation's `onMutate`, kept in state until the user dismisses /
  // accepts the diff, saves the page, navigates away, or the
  // mutation fails. `null` means "no pending diff to show".
  const [priorText, setPriorText] = useState<string | null>(null);
  const [showDiff, setShowDiff] = useState<boolean>(true);

  // Image-load state drives the overlay sizing — Konva Stage waits
  // until the <img> has rendered so we know natural & rendered sizes.
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const selectDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [imgEl, setImgEl] = useState<HTMLImageElement | null>(null);
  const [naturalSize, setNaturalSize] = useState<{ w: number; h: number }>({
    w: 0,
    h: 0,
  });

  const page = useQuery({
    queryKey: ["page", projectId, idx0],
    queryFn: () =>
      api.get<PageRecord>(`/api/data/projects/${projectId}/pages/${idx0}`),
  });

  const text$ = useQuery({
    enabled: !!page.data,
    queryKey: ["page-text", projectId, idx0, splitSuffix],
    queryFn: () =>
      api.get<{ text: string; text_key: string; words: OcrWord[] }>(
        `/api/data/projects/${projectId}/pages/${idx0}/text/${splitSuffix || "_"}`,
      ),
  });

  useEffect(() => {
    if (text$.data) {
      setText(text$.data.text);
      setWords(text$.data.words ?? []);
      setDirty(false);
      setActiveWordIndex(null);
    } else if (text$.error) {
      // 404 = no text yet (probably needs OCR first)
      setText("");
      setWords([]);
      setDirty(false);
      setActiveWordIndex(null);
    }
  }, [text$.data, text$.error]);

  useEffect(() => {
    return () => {
      if (selectDebounceRef.current) {
        clearTimeout(selectDebounceRef.current);
      }
    };
  }, []);

  // Router stays mounted on Prev/Next (only :idx0 changes), so the
  // re-OCR diff snapshot would otherwise leak across pages. Clear
  // it whenever the page identity (project / idx0 / split) changes.
  useEffect(() => {
    setPriorText(null);
  }, [projectId, idx0, splitSuffix]);

  const wordIndex = useMemo(
    () => buildWordOffsetIndex(text, words),
    [text, words],
  );

  const save = useMutation({
    mutationFn: () =>
      api.patch<{ text_key: string }>(
        `/api/data/projects/${projectId}/pages/${idx0}/text`,
        { split_suffix: splitSuffix || null, text },
      ),
    onSuccess: () => {
      setDirty(false);
      // Persisting the user's edits ends the "compare against
      // prior re-OCR" workflow — the new content is now canonical.
      setPriorText(null);
      queryClient.invalidateQueries({
        queryKey: ["page-text", projectId, idx0, splitSuffix],
      });
    },
  });

  const reocr = useMutation({
    mutationFn: () =>
      api.post<OcrPageResponse>("/api/gpu/run-ocr-page", {
        project_id: projectId,
        idx0,
        split_suffix: splitSuffix || null,
      }),
    onMutate: () => {
      // Snapshot the textarea content right before the new OCR
      // result lands. Closure captures the current `text`, so
      // back-to-back re-OCR clicks always compare against the
      // text that was on screen immediately before THIS click —
      // not the very first prior-text we ever captured.
      setPriorText(text);
      setShowDiff(true);
    },
    onSuccess: (resp) => {
      setText(resp.text);
      setWords(resp.words ?? []);
      setDirty(false);
      setActiveWordIndex(null);
      queryClient.invalidateQueries({
        queryKey: ["page-text", projectId, idx0, splitSuffix],
      });
    },
    onError: () => {
      // No new text was written; nothing meaningful to diff.
      setPriorText(null);
    },
  });

  // Memoised so typing in the textarea doesn't re-run the LCS on
  // every keystroke. Only computed when a snapshot exists; the
  // empty-array fallback is cheap and keeps the render path
  // unconditional.
  const diff = useMemo(
    () => (priorText !== null ? diffLines(priorText, text) : []),
    [priorText, text],
  );
  const diffHasChanges = useMemo(
    () => diff.some((d) => d.kind !== "equal"),
    [diff],
  );

  if (page.isLoading) return <p className="text-slate-500">Loading…</p>;
  if (!page.data) return <p className="text-red-600">Page not found.</p>;

  const splits = page.data.splits as Array<{ suffix: string; reading_order: number }>;
  const imageKey = page.data.processed_image_key || page.data.thumbnail_key;

  const handleTextareaSelect = () => {
    const ta = textareaRef.current;
    if (!ta) return;
    // Debounce: drag-selecting fires onSelect repeatedly and would
    // thrash Konva re-renders. Coalesce to ~75ms; the bbox→textarea
    // path stays synchronous (a single click).
    const off = ta.selectionStart;
    if (selectDebounceRef.current) {
      clearTimeout(selectDebounceRef.current);
    }
    selectDebounceRef.current = setTimeout(() => {
      selectDebounceRef.current = null;
      const hit = offsetToWord(wordIndex, off);
      setActiveWordIndex(hit ? hit.wordIndex : null);
    }, 75);
  };

  const handleWordClick = (i: number) => {
    setActiveWordIndex(i);
    const r = wordToRange(wordIndex, i);
    if (r && textareaRef.current) {
      const ta = textareaRef.current;
      ta.focus();
      ta.setSelectionRange(r.start, r.end);
      // Best-effort scroll into view: textarea doesn't expose a
      // built-in scrollToSelection. Use the textarea's actual
      // computed line-height; some browsers report "normal" so fall
      // back to font-size × 1.2.
      try {
        const before = text.slice(0, r.start);
        const line = before.split("\n").length - 1;
        const cs = window.getComputedStyle(ta);
        const lhRaw = cs.lineHeight;
        let lineHeight = parseFloat(lhRaw);
        if (!Number.isFinite(lineHeight)) {
          lineHeight = parseFloat(cs.fontSize) * 1.2;
        }
        const target = Math.max(0, line * lineHeight - ta.clientHeight / 3);
        ta.scrollTop = target;
      } catch {
        /* non-fatal */
      }
    }
  };

  return (
    <section className="space-y-3">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-lg font-semibold">
            Text review — {page.data.prefix || `#${idx0}`}
          </h1>
          <p className="text-xs text-slate-500">{page.data.source_stem}</p>
        </div>
        <div className="flex items-center gap-2">
          {splits.length > 0 && (
            <select
              value={splitSuffix}
              onChange={(e) => setSplitSuffix(e.target.value)}
              className="rounded border border-slate-300 px-2 py-1 text-sm"
            >
              <option value="">(whole page)</option>
              {[...splits]
                .sort((a, b) => a.reading_order - b.reading_order)
                .map((s) => (
                  <option key={s.suffix} value={s.suffix}>
                    {page.data!.prefix}
                    {s.suffix}
                  </option>
                ))}
            </select>
          )}
          <Link
            to={`/projects/${projectId}/pages/${Math.max(0, idx0 - 1)}/review`}
            className="rounded border border-slate-300 px-2 py-1 text-sm hover:bg-slate-50"
          >
            ← Prev
          </Link>
          <Link
            to={`/projects/${projectId}/pages/${idx0 + 1}/review`}
            className="rounded border border-slate-300 px-2 py-1 text-sm hover:bg-slate-50"
          >
            Next →
          </Link>
        </div>
      </header>

      <div className="grid gap-3 lg:grid-cols-2">
        <div className="rounded border bg-white p-2">
          {imageKey ? (
            <div className="relative inline-block w-full">
              <img
                ref={setImgEl}
                src={`/cdn/${imageKey}`}
                alt={page.data.prefix}
                className="max-h-[80vh] w-full object-contain"
                onLoad={(e) => {
                  const el = e.currentTarget;
                  setNaturalSize({
                    w: el.naturalWidth,
                    h: el.naturalHeight,
                  });
                }}
              />
              <WordBboxOverlay
                naturalWidth={naturalSize.w}
                naturalHeight={naturalSize.h}
                words={words}
                activeWordIndex={activeWordIndex}
                onWordClick={handleWordClick}
                trackElement={imgEl}
              />
            </div>
          ) : (
            <div className="flex h-96 items-center justify-center text-slate-400">
              no image
            </div>
          )}
        </div>

        <div className="flex flex-col rounded border bg-white p-2">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              setDirty(true);
            }}
            onSelect={handleTextareaSelect}
            onClick={handleTextareaSelect}
            onKeyUp={handleTextareaSelect}
            spellCheck
            className="min-h-[60vh] w-full resize-y rounded border-0 p-2 font-mono text-sm focus:outline-none"
            placeholder={
              text$.error
                ? "No OCR text yet. Click 're-OCR' to run OCR for this page."
                : "Loading…"
            }
          />
          <div className="flex items-center gap-2 border-t pt-2">
            <button
              onClick={() => save.mutate()}
              disabled={!dirty || save.isPending}
              className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white disabled:opacity-50 hover:bg-slate-800"
            >
              {save.isPending ? "Saving…" : dirty ? "Save" : "Saved"}
            </button>
            <button
              onClick={() => reocr.mutate()}
              disabled={reocr.isPending}
              className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
            >
              {reocr.isPending ? "Re-OCR…" : "Re-OCR this page"}
            </button>
            {save.isError && (
              <span className="text-xs text-red-600">
                save failed: {(save.error as Error).message}
              </span>
            )}
            {reocr.isError && (
              <span className="text-xs text-red-600">
                ocr failed: {(reocr.error as Error).message}
              </span>
            )}
            {priorText !== null && (
              <>
                <button
                  onClick={() => setShowDiff((v) => !v)}
                  className="ml-auto rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-50"
                >
                  {showDiff ? "Hide diff" : "Show diff"}
                </button>
                <button
                  onClick={() => setPriorText(null)}
                  className="rounded border border-slate-300 px-2 py-1 text-xs hover:bg-slate-50"
                  title="Dismiss the diff and accept the new OCR text"
                >
                  Accept
                </button>
              </>
            )}
          </div>
          {priorText !== null && showDiff && (
            <div className="mt-2">
              <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
                <span>Re-OCR diff (prior → new)</span>
                {!diffHasChanges && (
                  <span className="italic">
                    no changes — re-OCR returned identical text
                  </span>
                )}
              </div>
              {diffHasChanges && <LineDiffView diff={diff} />}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
