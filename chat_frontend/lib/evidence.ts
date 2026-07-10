import type { Citation } from "@/lib/chat-types";

export type CitationGroup = {
  key: string;
  title: string;
  citations: Citation[];
  evidenceCount: number;
};

export function groupCitationsByDocument(citations: Citation[]): CitationGroup[] {
  const groups = new Map<string, CitationGroup>();

  for (const citation of citations) {
    const key = canonicalSourceKey(citation) || `unknown-${groups.size + 1}`;
    const existing = groups.get(key);
    if (existing) {
      existing.citations.push(citation);
      existing.evidenceCount += 1;
      continue;
    }
    groups.set(key, {
      key,
      title: stringValue(citation.title) || key,
      citations: [citation],
      evidenceCount: 1,
    });
  }

  return Array.from(groups.values());
}

export function canonicalSourceKey(citation: Citation) {
  const raw = stringValue(citation.source_id || citation.sourceId || citation.source_ref);
  return raw.split(/[?#]/, 1)[0].trim();
}

function stringValue(value: unknown) {
  return typeof value === "string" ? value : "";
}
