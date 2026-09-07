# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-09-07

### Added
- MIT license, contributing guide and changelog.
- Unit test suite (`pytest`) for the provider parsers, the schedule evaluator and localization coverage.
- GitHub Actions CI running `pytest` (Python 3.10–3.12) and `ruff` on pushes and pull requests.
- Ubuntu autostart instructions in the README.

### Changed
- Applied `ruff` autofixes across the codebase (import order, modern typing); no behaviour change.

## [0.4.2] - 2026-09-07

### Changed
- Reverted the Copilot icon to the GitHub mark (0.4.1 shipped a robot-head glyph).
- Refreshed the usage-panel screenshot for the current layout.

## [0.4.1] - 2026-09-07

### Changed
- Replaced the Copilot icon (was the GitHub octocat) with a Copilot mark.

## [0.4.0] - 2026-09-07

### Fixed
- The Claude icon was two triangles rather than the Anthropic mark; replaced with the radial spark.
- Provider icons were invisible on dark themes (`currentColor` resolved to black when loaded as a pixbuf); they are now recolored to the theme foreground.
- Reset dates followed the system locale instead of the app language.

### Changed
- Usage panel: more card padding and contrast, tabular figures instead of a monospace value.
- Metrics with no data show a "No data for this plan" note at normal card height instead of an empty bar.
- Removed the unlabelled pace bar and the redundant in-window title; tightened vertical spacing.

## [0.3.0] - 2026-09-07

### Fixed
- Claude usage was stuck at 100%: the API reports `utilization` as a percentage, not a `0..1` fraction.
- Codex weekly usage was dropped: rate-limit windows are now classified by duration, not by primary/secondary position.
- Behind-schedule notifications repeated on every refresh because `resets_at` jitters between polls; timestamps within 5 minutes now count as the same window.

### Added
- AI spark tray icon, theme-aware (visible on dark panels).
- Tray label reads `AI <used>%` per visible provider.
- Tray menu lists each usage window with a progress bar and opens the panel on click; middle-click opens the panel.
- Panel shows consumed usage with an explicit "no data" state.

## [0.2.0] - 2026-04-16

- Initial public version: GNOME tray app tracking Claude, Codex, and GitHub Copilot usage.

[Unreleased]: https://github.com/jakubgrzywaczewski/ai-usage-gnome/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/jakubgrzywaczewski/ai-usage-gnome/compare/v0.4.2...v0.5.0
[0.4.2]: https://github.com/jakubgrzywaczewski/ai-usage-gnome/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/jakubgrzywaczewski/ai-usage-gnome/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/jakubgrzywaczewski/ai-usage-gnome/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/jakubgrzywaczewski/ai-usage-gnome/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jakubgrzywaczewski/ai-usage-gnome/releases/tag/v0.2.0
