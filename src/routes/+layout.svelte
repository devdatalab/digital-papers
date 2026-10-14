<!-- Shared responsive reading shell with navigation, search and context panels.
     Depends on the selected paper configuration and ddl-charts theme tokens. -->
<script lang="ts">
	import '@devdatalab/ddl-charts/styles/ddl-theme.css';
	import '$lib/styles/app.css';

	import { onMount } from 'svelte';
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/stores';
	import { base } from '$app/paths';
	import { navEntries, extrasEntries, meta } from '$lib/content';
	import config from '$paper/paper.config';
	import SectionNav from '$lib/reading/SectionNav.svelte';
	import ReadingProgress from '$lib/reading/ReadingProgress.svelte';
	import SearchBox from '$lib/reading/SearchBox.svelte';
	import AnnotationPanel from '$lib/reading/AnnotationPanel.svelte';
	import AsidePageIndex from '$lib/reading/AsidePageIndex.svelte';
	import AsideResizeHandle from '$lib/reading/AsideResizeHandle.svelte';
	import AsideReopenTab from '$lib/reading/AsideReopenTab.svelte';
		import ReadingTour from '$lib/reading/ReadingTour.svelte';
	import { tour } from '$lib/state/tour.svelte';
	import { annotationStack } from '$lib/state/annotationStack.svelte';
	import { asidePanel } from '$lib/state/asidePanel.svelte';
	import { stickyAvoidFullBleed } from '$lib/actions/stickyAvoidFullBleed';

	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
	let mobileNavOpen = $state(false);
	let mobileNavButton: HTMLButtonElement;
	afterNavigate(() => { mobileNavOpen = false; });
	function closeMobileNav(event: KeyboardEvent) {
		if (event.key === 'Escape' && mobileNavOpen) {
			mobileNavOpen = false;
			mobileNavButton?.focus();
		}
	}

	// The bespoke "Extras" routes (static pages, not `[section]` slugs) are
	// detected via the route id so they can drive both nav highlighting and their
	// own shell mode. `$page.params.section` is undefined there, so route-id is the
	// reliable signal. Each Extras route's slug matches its trailing path segment.
	let routeId = $derived($page.route.id);
	const explorerRoutes = config.extras.map((entry) => `/${entry.id}`);
	let isExplorer = $derived(config.extras.some((entry) => entry.id === $page.params.section) || explorerRoutes.includes(routeId ?? ''));
	// Current nav item: an Extras page's slug (its trailing path segment), else the
	// section param, else null (the title page).
	let currentId = $derived(
		isExplorer
			? (($page.params.section as string | undefined) ?? (routeId ?? '').replace(/^\//, ''))
			: (($page.params.section as string | undefined) ?? null)
	);
	// An open "Additional Information" panel belongs to the section it was opened
	// from: once the reader navigates to a different section (or any other page),
	// drop it so it can't linger over unrelated content. `prevSection` is a plain
	// (non-reactive) variable, so this effect depends only on `currentId` and
	// never fires merely because a panel opened — that leaves `currentId`
	// unchanged. Clearing on the first run is harmless: nothing is open on load.
	let prevSection: string | null = null;
	$effect(() => {
		const section = currentId;
		if (section !== prevSection) {
			annotationStack.clear();
			prevSection = section;
		}
	});
	// The title/abstract shares the left TOC and fluid main column, but omits
	// the right context panel to leave room for the guided feature chart.
	let isTitle = $derived(routeId === '/');
	// Route path — passed to the sticky action so it re-queries full-bleed
	// targets when the reader navigates between pages.
	let pathname = $derived($page.url.pathname);

	// Responsive mode. Server render + pre-hydration assume the common `wide`
	// case; onMount corrects it from matchMedia. Guarded because the site is
	// prerendered (no window at build time).
	let mode = $state<'wide' | 'narrow' | 'mobile'>('wide');

	onMount(() => {
		// Seed the aside width proportional to the viewport so it starts at a
		// sensible ratio on large monitors (the store default is a fixed px).
		// Runs once on load; the reader's later drags take over from here.
		asidePanel.setWidth(Math.round(window.innerWidth * 0.28));

		const narrowMq = window.matchMedia('(max-width: 1079px)');
		const mobileMq = window.matchMedia('(max-width: 719px)');
		const sync = () => {
			const next: 'wide' | 'narrow' | 'mobile' = mobileMq.matches
				? 'mobile'
				: narrowMq.matches
					? 'narrow'
					: 'wide';
			// Auto-collapse whenever we're not in wide mode so the reading
			// column keeps its measure; the reader can reopen as an overlay.
			if (next !== 'wide') asidePanel.collapse();
			mode = next;
		};
		sync();
		narrowMq.addEventListener('change', sync);
		mobileMq.addEventListener('change', sync);
		return () => {
			narrowMq.removeEventListener('change', sync);
			mobileMq.removeEventListener('change', sync);
		};
	});

	// In-grid aside: wide mode, content page, not collapsed.
	let asideInGrid = $derived(
		mode === 'wide' && !isTitle && !isExplorer && !asidePanel.collapsed
	);
	// Overlay aside: narrow mode, content page, expanded by the reader.
	let asideOverlay = $derived(
		mode === 'narrow' && !isTitle && !isExplorer && !asidePanel.collapsed
	);
	// The aside is rendered in either the grid or the overlay case.
	let showAside = $derived(asideInGrid || asideOverlay);
	// Reopen tab: content page, collapsed, and not mobile (mobile hides the
	// aside entirely).
	let showReopenTab = $derived(
		mode !== 'mobile' && !isTitle && !isExplorer && asidePanel.collapsed
	);
	// On mobile the aside is never in the layout, so a tapped annotation tag has
	// nowhere to open. Instead surface the same AnnotationPanel as a full-screen
	// overlay whenever a tag is open in mobile mode.
	let showMobileAnnotation = $derived(mode === 'mobile' && annotationStack.openId != null);
</script>

<svelte:window onkeydown={closeMobileNav} />

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<header class="ui site-header">
	<a class="brand" href="{base}/" aria-label="{meta.title} — home">
		{#if config.logo}<img src="{base}/{config.logo}" alt="Publication logo" height="28" />{/if}
		<span class="brand-title">{config.headerTitle ?? meta.title}</span>
	</a>
	<div class="header-links">
		<!-- Site search stays on the section and explorer pages. -->
		{#if !isTitle}
			<SearchBox />
		{/if}
		<!-- Replay the first-visit reading tour from any page, including the title
		     and abstract. Hidden on mobile, where the tour doesn't apply. -->
		{#if config.tour}<button type="button" class="tour-link" onclick={() => tour.start()}>Tour</button>{/if}

		{#if meta.pdf}<a class="pdf-link" href="{base}/{meta.pdf}" target="_blank" rel="noopener">PDF ↗</a>{/if}
		<a class="pdf-link" href="{base}/paper.md">Markdown ↓</a>
	</div>
	<ReadingProgress />
</header>

<div
	class="shell"
	class:shell--title={isTitle}
	class:shell--explorer={isExplorer}
	class:shell--3col={asideInGrid}
	style="--aside-w:{asidePanel.width}px"
>
	<aside class="col-nav" class:nav-open={mobileNavOpen}>
		<button class="mobile-nav-toggle ui" bind:this={mobileNavButton}
			aria-expanded={mobileNavOpen} aria-controls="section-navigation"
			onclick={() => mobileNavOpen = !mobileNavOpen}>
			<span aria-hidden="true">{mobileNavOpen ? '×' : '☰'}</span>
			{mobileNavOpen ? 'Close contents' : 'Contents'}
		</button>
		<div id="section-navigation" class="sticky" use:stickyAvoidFullBleed={pathname}>
			<SectionNav entries={navEntries} extras={extrasEntries} {currentId} />
		</div>
	</aside>

	<main class="col-main" data-col-main>
		{@render children()}
	</main>

	{#if showAside}
		<aside
			class="col-tools"
			class:col-tools--overlay={asideOverlay}
			aria-label="Tools and context"
		>
			{#if asideInGrid}
				<AsideResizeHandle />
			{/if}
			<div class="sticky">
				<div class="tools-head ui">
					<div class="tools-head-row">
						<h2>Additional Information</h2>
						<button
							type="button"
							class="tools-collapse"
							aria-label="Collapse additional information panel"
							onclick={() => asidePanel.collapse()}
						>
							Hide ›
						</button>
					</div>
					<p>
						Click the numbered tags (A1, A2, etc.) in the paper to surface supplementary
						information.
					</p>
				</div>
				{#if annotationStack.openId}
					<div class="tools-stack">
						{#key annotationStack.openId}
							<AnnotationPanel
								id={annotationStack.openId}
								currentSectionId={currentId ?? ''}
							/>
						{/key}
					</div>
				{:else if currentId}
					<AsidePageIndex sectionId={currentId} />
				{/if}
			</div>
		</aside>
	{/if}
</div>

{#if showReopenTab}
	<AsideReopenTab />
{/if}

{#if showMobileAnnotation && annotationStack.openId}
	<div class="mobile-annotation" role="dialog" aria-label="Additional information">
		<div class="mobile-annotation-head ui">
			<h2>Additional Information</h2>
			<button
				type="button"
				class="mobile-annotation-close"
				aria-label="Close additional information"
				onclick={() => annotationStack.clear()}
			>
				Close ✕
			</button>
		</div>
		<div class="mobile-annotation-body">
			{#key annotationStack.openId}
				<AnnotationPanel id={annotationStack.openId} currentSectionId={currentId ?? ''} />
			{/key}
		</div>
	</div>
{/if}

{#if config.exampleNotice}<p class="example-notice ui">{config.exampleNotice}</p>{/if}
{#if config.credit}<footer class="design-credit ui">{config.credit}</footer>{/if}
{#if config.tour}<ReadingTour />{/if}

<style>
	.design-credit { text-align: center; color: var(--muted); font-size: 0.75rem; padding: 2rem 1rem; }
	.example-notice { max-width: 65rem; margin: 2rem auto 0; padding: 1rem; color: var(--muted); font-size: 0.8rem; }
	.mobile-nav-toggle { display: none; }

	.site-header {
		position: sticky;
		top: 0;
		z-index: 10;
		height: var(--header-h);
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		padding: 0 var(--gutter);
		background: rgba(255, 255, 255, 0.92);
		backdrop-filter: saturate(1.4) blur(6px);
		border-bottom: 1px solid var(--rule);
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 0.85rem;
		min-width: 0;
		color: var(--ink);
	}
	.brand:hover {
		text-decoration: none;
	}
	/* Logo rendered from ddl-theme.css's --ddl-logo token (data-URI). The mark's
	   viewBox is ~1877×207, so an aspect ratio of ~9.06:1 keeps it undistorted. */
	.brand-title {
		font-weight: 600;
		font-size: 0.95rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;


	}

	.header-links {
		display: flex;
		align-items: center;
		gap: 1.25rem;
	}
	.tour-link {
		border: none;
		background: none;
		padding: 0;
		font-family: var(--font-ui);
		font-size: 0.85rem;
		font-weight: 500;
		color: var(--muted);
		white-space: nowrap;
		cursor: pointer;
	}
	.tour-link:hover {
		color: var(--accent);
	}

	.pdf-link {
		font-size: 0.85rem;
		font-weight: 500;
		color: var(--muted);
		white-space: nowrap;
	}
	.pdf-link:hover {
		color: var(--accent);
		text-decoration: none;
	}

	/* Base shell: a fluid two-column grid (nav + main). The aside is added as a
	   third track only in wide mode via .shell--3col (see Task 3); on narrow it
	   floats as an overlay and on mobile it's hidden, so it never squeezes the
	   reading column. */
	.shell {
		display: grid;
		grid-template-columns: var(--nav-w) minmax(0, 1fr);
		gap: var(--gutter);
		padding: 0 var(--gutter) 0 var(--gutter);
		align-items: start;
	}

	/* Wide mode with the aside expanded: nav + reading column, then a flexible
	   spacer, then the aside pinned FLUSH to the viewport's right edge (the right
	   gutter is dropped so nothing sits to its right; the left gutter stays so the
	   nav keeps its margin). The spacer (track 3) absorbs leftover width on large
	   screens, so nav + prose stay grouped on the left while the pane always hugs
	   the right edge. The aside is placed explicitly on the last line — otherwise,
	   with only three grid children, auto-flow would drop it into the spacer track.
	   The reading column is capped at the readable measure (--read-max); the
	   content tracks use minmax(0, …) so they shrink gracefully on tighter widths. */
	.shell--3col {
		grid-template-columns:
			var(--nav-w)
			minmax(0, var(--read-max))
			minmax(0, 1fr)
			minmax(0, var(--aside-w));
		padding: 0 0 0 var(--gutter);
	}
	.shell--3col .col-tools {
		grid-column: 4;
	}

	/* The title page ends on its pinned scrolly chart (with "Begin reading" in
	   the last card); trailing padding would scroll the chart's top edge under
	   the header at the very bottom. */
	.shell.shell--title .col-main {
		padding-top: 0.5rem;
		padding-bottom: 0;
	}

	/* Data Explorer: keep the left TOC, drop the aside, let main claim the
	   width (the analysis table wants room). */
	.shell.shell--explorer {
		grid-template-columns: var(--nav-w) minmax(0, 1fr);
		padding-right: var(--gutter);
	}

	.sticky {
		position: sticky;
		top: calc(var(--header-h) + 1.75rem);
		max-height: calc(100vh - var(--header-h) - 2.5rem);
		overflow-y: auto;
		/* Wheel/trackpad scrolling inside the nav or aside stays there: reaching
		   the panel's end doesn't chain on to scroll the article. Only applies
		   while the panel actually overflows — a short panel still passes the
		   scroll through to the page. */
		overscroll-behavior: contain;
	}

	.col-nav {
		padding-top: 2.5rem;
		/* Stretch to the full content-row height (the grid sets align-items:start)
		   so the sticky TOC can travel the whole scroll, not just this column's
		   short content box. */
		align-self: stretch;
	}

	.col-main {
		padding: 2.5rem 0 6rem;
		min-width: 0;
	}

	.col-tools {
		position: relative;
		/* No padding-top (unlike .col-nav): the panel must be flush against
		   the header with no gap, since its background is what makes it a
		   visible "surface" rather than plain page background. */
		/* Stretch to the full content-row height (matches .col-nav's own
		   align-self: stretch) so the border-left separator and the beige
		   sticky surface both run the whole length of the page, not just
		   the height of the "Coming soon" text. */
		align-self: stretch;
		border-left: 1px solid var(--rule);
	}

	/* The panel's beige "surface" lives on the sticky wrapper (not the whole
	   .col-tools column) so it's pinned to the viewport and scrolls its own
	   content independently of the page. Both top and height are overridden
	   from the shared .sticky rule so the surface starts flush at the header
	   (no gap) and fills exactly to the bottom of the viewport (no gap) —
	   unlike the nav, which keeps its breathing-room offset. */
	.col-tools .sticky {
		top: var(--header-h);
		height: calc(100vh - var(--header-h));
		max-height: calc(100vh - var(--header-h));
		background: var(--bg-panel);
	}

	/* Narrow mode: the aside floats over the content from the right edge
	   instead of taking a grid track, so the reading column keeps its width.
	   Fixed below the header, full remaining height, its own scroll. */
	.col-tools--overlay {
		position: fixed;
		top: var(--header-h);
		right: 0;
		width: min(380px, 90vw);
		height: calc(100vh - var(--header-h));
		z-index: 8;
		border-left: 1px solid var(--rule);
		background: var(--bg-panel);
		box-shadow: -6px 0 20px rgba(0, 0, 0, 0.08);
		overflow-y: auto;
		overscroll-behavior: contain;
	}
	.col-tools--overlay .sticky {
		position: static;
		height: auto;
		max-height: none;
		background: none;
	}

	.tools-head {
		padding: 1.25rem;
		border-bottom: 1px solid var(--rule);
	}
	.tools-head h2 {
		margin: 0 0 0.4rem;
		font-family: var(--font-serif);
		font-size: 1.05rem;
		font-weight: 600;
		color: var(--ink);
	}
	.tools-head p {
		margin: 0;
		color: var(--muted);
		font-size: 0.85rem;
		line-height: 1.5;
	}

	.tools-head-row {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 0.75rem;
	}
	.tools-collapse {
		border: none;
		background: none;
		padding: 0;
		font-family: var(--font-ui);
		font-size: 0.8rem;
		font-weight: 500;
		color: var(--muted);
		cursor: pointer;
		white-space: nowrap;
	}
	.tools-collapse:hover {
		color: var(--accent);
	}

	.tools-stack {
		display: flex;
		flex-direction: column;
		gap: 0.9rem;
		padding: 0 1.25rem 1.25rem;
	}

	/* Mobile annotation overlay: the aside isn't in the layout on phones, so a
	   tapped tag opens the AnnotationPanel as a full-screen sheet instead. Only
	   rendered in mobile mode (see `showMobileAnnotation`). */
	.mobile-annotation {
		position: fixed;
		inset: 0;
		z-index: 40;
		display: flex;
		flex-direction: column;
		background: var(--bg-panel);
	}
	.mobile-annotation-head {
		flex: none;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		padding: 0 1.25rem;
		height: var(--header-h);
		border-bottom: 1px solid var(--rule);
		background: rgba(255, 255, 255, 0.92);
		backdrop-filter: saturate(1.4) blur(6px);
	}
	.mobile-annotation-head h2 {
		margin: 0;
		font-family: var(--font-serif);
		font-size: 1.05rem;
		font-weight: 600;
		color: var(--ink);
	}
	.mobile-annotation-close {
		border: none;
		background: none;
		padding: 0.4rem 0;
		font-family: var(--font-ui);
		font-size: 0.85rem;
		font-weight: 600;
		color: var(--muted);
		cursor: pointer;
		white-space: nowrap;
	}
	.mobile-annotation-close:hover {
		color: var(--accent);
	}
	.mobile-annotation-body {
		flex: 1;
		min-height: 0;
		overflow-y: auto;
		padding: 1.25rem;
	}

	/* Mobile: single column with a collapsible, sticky contents menu. Aside is not
	   rendered in this mode (handled in the markup by the `mode` logic). */
	@media (max-width: 719px) {
		.shell,
		.shell--3col,
		.shell.shell--explorer {
			grid-template-columns: minmax(0, 1fr);
			gap: 0;
			padding: 0 1.25rem;
		}
		.col-nav {
			padding-top: 0;
			position: sticky;
			top: var(--header-h);
			z-index: 9;
			background: var(--bg);
			border-bottom: 1px solid var(--rule);
		}
		.mobile-nav-toggle {
			display: flex;
			align-items: center;
			gap: 0.65rem;
			width: 100%;
			min-height: 48px;
			padding: 0.65rem 0;
			border: 0;
			background: none;
			color: var(--ink);
			font-size: 0.9rem;
			cursor: pointer;
		}
		.mobile-nav-toggle span { font-size: 1.25rem; }
		.col-nav:not(.nav-open) .sticky { display: none; }
		.col-nav .sticky {
			position: static;
			max-height: calc(100svh - var(--header-h) - 64px);
			overflow-y: auto;
			padding: 0.5rem 0.75rem 1rem;
			overscroll-behavior: auto;
		}
		.col-main {
			padding-top: 1.5rem;
		}
		.site-header {
			padding: 0 1.25rem;
		}
		/* Phones keep only search (icon), bug report and PDF: the paper title
		   and the features tour (which doesn't apply on mobile) are dropped, and
		   the wordmark shrinks to the DDL symbol so the three controls fit. */
		.brand-title { font-size: 0.8rem; }
		.header-links {
			gap: 1rem;
		}
		.tour-link:not(.bug-link) {
			display: none;
		}
	}
</style>
