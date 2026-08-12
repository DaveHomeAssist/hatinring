# Hat in Ring makes its daily tracker substantially lighter

Hat in Ring has shipped a generator-level portrait delivery upgrade for its 2028 presidential field tracker.

The leaderboard and card views previously displayed candidates at 30–48px while downloading portrait files sized for full dossier presentation. The daily builder now creates dedicated 96px and 192px WebP thumbnails and emits responsive srcset instructions with explicit dimensions, lazy loading, and asynchronous decoding.

The full optimized portrait remains available where readers actually need it: detailed dossier and static candidate pages. The initial field views now request assets matched to their visible size, reducing the generated thumbnail set to roughly 444KB across 40 candidates and avoiding multi-megabyte overdelivery.

The release is covered by the existing 207-test pipeline suite plus new thumbnail-format and size assertions. It also adds pinned dependency, secret, and configuration scanning; weekly dependency updates; a formal changelog; and a release checklist that keeps evidence review and live proof in the gate.
