<!--
	SearchBox — the site-wide search field in the header, with a results
	dropdown.

	Why it exists: lets a reader find any passage in the paper (prose, headings,
	figure/table captions, collapsible panels, FAQ, footnotes) without knowing
	which section it lives in. Choosing a result navigates to that section,
	opens any collapsed panel around the block, scrolls to it and briefly
	highlights it.

	Behaviour:
	  - Follows the ARIA 1.2 combobox pattern: the input owns a listbox of
	    results; ↑/↓ move, Enter opens, Esc clears then closes.
	  - "/" or Ctrl/⌘+K focuses the field from anywhere on the page.
	  - The index is built lazily on first focus (see searchIndex.ts), so pages
	    load no search code until a reader reaches for it.
	  - On phones the field collapses to an icon button; tapping it expands
	    the field over the header.

	Upstream dependencies: $lib/search/searchIndex (index, query, excerpts),
	$lib/search/revealBlock (scroll + flash), SvelteKit's `goto`/`base`, and
	theme tokens from ddl-theme.css and app.css (--search-hit, --rule, etc.).
-->
<script lang="ts">
	import { tick } from 'svelte';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import {
		search,
		loadIndex,
		excerpt,
		type SearchHit,
		type SearchRecord
	} from '$lib/search/searchIndex';
	import { revealBlock } from '$lib/search/revealBlock';

	const LISTBOX_ID = 'site-search-results';

	let query = $state('');
	let hits = $state<SearchHit[]>([]);
	let active = $state(-1);
	let focused = $state(false);
	let status = $state<'idle' | 'loading' | 'ready' | 'error'>('idle');
	// Phones only: whether the icon button has been expanded into the field.
	let expanded = $state(false);

	let root: HTMLDivElement;
	let input: HTMLInputElement;
	let listbox = $state<HTMLUListElement>();

	let showPanel = $derived(focused && query.trim().length > 0);

	// Guards against out-of-order results: only the latest query's hits land.
	let requestSeq = 0;

	async function runSearch() {
		const seq = ++requestSeq;
		if (!query.trim()) {
			hits = [];
			active = -1;
			return;
		}
		if (status !== 'ready') status = 'loading';
		try {
			const result = await search(query);
			if (seq !== requestSeq) return;
			hits = result;
			active = result.length ? 0 : -1;
			status = 'ready';
		} catch {
			if (seq === requestSeq) status = 'error';
		}
	}

	function onFocus() {
		focused = true;
		// Warm the index while the reader starts typing.
		if (status === 'idle' || status === 'error') {
			status = 'loading';
			loadIndex().then(
				() => {
					status = 'ready';
					if (query.trim()) runSearch();
				},
				() => (status = 'error')
			);
		}
	}

	function onFocusOut(e: FocusEvent) {
		if (root.contains(e.relatedTarget as Node | null)) return;
		focused = false;
		expanded = false;
	}

	async function moveActive(delta: number) {
		if (!hits.length) return;
		active = (active + delta + hits.length) % hits.length;
		await tick();
		listbox?.querySelector(`#${LISTBOX_ID}-${active}`)?.scrollIntoView({ block: 'nearest' });
	}

	function onKeydown(e: KeyboardEvent) {
		switch (e.key) {
			case 'ArrowDown':
				e.preventDefault();
				moveActive(1);
				break;
			case 'ArrowUp':
				e.preventDefault();
				moveActive(-1);
				break;
			case 'Enter':
				if (showPanel && active >= 0 && hits[active]) {
					e.preventDefault();
					choose(hits[active]);
				}
				break;
			case 'Escape':
				e.preventDefault();
				if (query) {
					query = '';
					runSearch();
				} else {
					input.blur();
					expanded = false;
				}
				break;
		}
	}

	async function choose(hit: SearchHit) {
		const { sectionId, anchor } = hit.record;
		input.blur();
		focused = false;
		expanded = false;
		// revealBlock does the scrolling (after opening any collapsed panel
		// around the target) and moves focus, so SvelteKit must do neither.
		// keepFocus matters: without it SvelteKit's focus reset runs after us
		// and restores the pre-navigation scroll position.
		await goto(`${base}/${sectionId}#${anchor}`, { noScroll: true, keepFocus: true });
		await tick();
		revealBlock(anchor);
	}

	function isEditable(el: EventTarget | null): boolean {
		if (!(el instanceof HTMLElement)) return false;
		return el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName);
	}

	// "/" or Ctrl/⌘+K focuses search, unless the reader is already typing.
	async function onWindowKeydown(e: KeyboardEvent) {
		const slash = e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey;
		const cmdK = e.key?.toLowerCase() === 'k' && (e.ctrlKey || e.metaKey);
		if ((!slash && !cmdK) || (slash && isEditable(e.target))) return;
		e.preventDefault();
		expanded = true;
		await tick();
		input.focus();
		input.select();
	}

	async function expand() {
		expanded = true;
		await tick();
		input.focus();
	}

	/** Where in the section a hit sits, e.g. "Figure 2" or "Note 4". */
	function hitContext(r: SearchRecord): string {
		switch (r.kind) {
			case 'heading':
				return `Section ${r.label}`;
			case 'epigraph':
				return 'Epigraph';
			case 'collapsible':
				return 'Panel';
			default:
				return r.label;
		}
	}
</script>

<svelte:window onkeydown={onWindowKeydown} />

<div
	class="search ui"
	class:search--expanded={expanded}
	bind:this={root}
	onfocusout={onFocusOut}
	role="search"
>
	<button type="button" class="search-toggle" aria-label="Search the paper" onclick={expand}>
		<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"
			><circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" stroke-width="1.8" /><path
				d="M12.8 12.8 17 17"
				stroke="currentColor"
				stroke-width="1.8"
				stroke-linecap="round"
			/></svg
		>
	</button>

	<div class="search-field">
		<svg class="search-icon" viewBox="0 0 20 20" width="15" height="15" aria-hidden="true"
			><circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" stroke-width="1.8" /><path
				d="M12.8 12.8 17 17"
				stroke="currentColor"
				stroke-width="1.8"
				stroke-linecap="round"
			/></svg
		>
		<input
			bind:this={input}
			bind:value={query}
			type="search"
			placeholder="Search the paper"
			aria-label="Search the paper"
			role="combobox"
			aria-autocomplete="list"
			aria-expanded={showPanel}
			aria-controls={LISTBOX_ID}
			aria-activedescendant={showPanel && active >= 0 ? `${LISTBOX_ID}-${active}` : undefined}
			autocomplete="off"
			spellcheck="false"
			oninput={runSearch}
			onfocus={onFocus}
			onkeydown={onKeydown}
		/>
		{#if !query && !focused}<kbd class="search-kbd" aria-hidden="true">/</kbd>{/if}
	</div>

	{#if showPanel}
		<div class="search-panel">
			{#if status === 'error'}
				<p class="search-note">Search couldn't load. Check your connection and try again.</p>
			{:else if status === 'loading' && hits.length === 0}
				<p class="search-note">Loading…</p>
			{:else if hits.length === 0}
				<p class="search-note">No matches for “{query.trim()}”.</p>
			{/if}
			<ul id={LISTBOX_ID} role="listbox" aria-label="Search results" bind:this={listbox}>
				{#each hits as hit, i (hit.record.id)}
					<!-- Keyboard interaction lives on the input (combobox pattern), so
					     options are pointer-only targets by design. -->
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<li
						id="{LISTBOX_ID}-{i}"
						role="option"
						aria-selected={i === active}
						class:active={i === active}
						onmousedown={(e) => e.preventDefault()}
						onmousemove={() => (active = i)}
						onclick={() => choose(hit)}
					>
						<span class="hit-where">
							{hit.record.sectionLabel}{#if hitContext(hit.record)}<span class="hit-sep">·</span
								>{hitContext(hit.record)}{/if}
						</span>
						<span class="hit-text"
							>{#each excerpt(hit.record.text, hit.terms) as part, j (j)}{#if part.match}<mark
										>{part.text}</mark
									>{:else}{part.text}{/if}{/each}</span
						>
					</li>
				{/each}
			</ul>
			{#if hits.length}
				<p class="search-foot" aria-hidden="true">
					<span><kbd>↑</kbd><kbd>↓</kbd> to move</span>
					<span><kbd>Enter</kbd> to open</span>
					<span><kbd>Esc</kbd> to clear</span>
				</p>
			{/if}
		</div>
	{/if}

	<p class="sr-only" aria-live="polite">
		{#if showPanel && status === 'ready'}{hits.length === 0
				? 'No results'
				: `${hits.length} result${hits.length === 1 ? '' : 's'}`}{/if}
	</p>
</div>

<style>
	.search {
		position: relative;
	}

	.search-toggle {
		display: none;
		border: none;
		background: none;
		padding: 0.35rem;
		color: var(--muted);
		cursor: pointer;
	}
	.search-toggle:hover {
		color: var(--accent);
	}

	.search-field {
		position: relative;
		display: flex;
		align-items: center;
	}
	.search-icon {
		position: absolute;
		left: 0.6rem;
		color: var(--muted);
		pointer-events: none;
	}
	input {
		width: clamp(9rem, 16vw, 15rem);
		height: 2rem;
		padding: 0 1.8rem 0 1.9rem;
		font-family: var(--font-ui);
		font-size: 0.85rem;
		color: var(--ink);
		background: var(--bg-panel);
		border: 1px solid var(--rule-strong);
		border-radius: var(--ddl-border-radius, 4px);
		transition:
			border-color var(--ddl-transition-fast, 0.15s),
			background-color var(--ddl-transition-fast, 0.15s);
	}
	input::placeholder {
		color: var(--muted);
	}
	input:focus {
		outline: none;
		background: var(--bg);
		border-color: var(--accent);
		box-shadow: 0 0 0 3px rgba(30, 136, 229, 0.15);
	}
	/* Use our own clear affordance (Esc) rather than the WebKit "x". */
	input::-webkit-search-cancel-button {
		-webkit-appearance: none;
	}
	.search-kbd {
		position: absolute;
		right: 0.5rem;
		pointer-events: none;
	}
	kbd {
		display: inline-block;
		min-width: 1.2em;
		padding: 0 0.3em;
		font-family: var(--font-mono);
		font-size: 0.7rem;
		line-height: 1.5;
		text-align: center;
		color: var(--muted);
		border: 1px solid var(--rule-strong);
		border-radius: 3px;
		background: var(--bg);
	}

	.search-panel {
		position: absolute;
		top: calc(100% + 0.5rem);
		right: 0;
		z-index: 30;
		width: min(34rem, calc(100vw - 2rem));
		max-height: min(32rem, calc(100vh - var(--header-h) - 2rem));
		display: flex;
		flex-direction: column;
		background: var(--bg);
		border: 1px solid var(--rule-strong);
		border-radius: var(--ddl-border-radius, 4px);
		box-shadow: var(--ddl-shadow-medium, 0 8px 24px rgba(0, 0, 0, 0.12));
		overflow: hidden;
	}
	ul {
		flex: 1 1 auto;
		min-height: 0;
		overflow-y: auto;
		overscroll-behavior: contain;
		margin: 0;
		padding: 0.35rem;
		list-style: none;
	}
	ul:empty {
		display: none;
	}
	li {
		display: flex;
		flex-direction: column;
		gap: 0.2rem;
		padding: 0.55rem 0.7rem;
		border-radius: 3px;
		cursor: pointer;
	}
	li.active {
		background: var(--bg-inset);
	}
	.hit-where {
		font-size: 0.72rem;
		font-weight: 600;
		letter-spacing: 0.03em;
		color: var(--accent);
	}
	.hit-sep {
		margin: 0 0.4em;
		color: var(--muted);
	}
	.hit-text {
		font-family: var(--font-serif);
		font-size: 0.9rem;
		line-height: 1.45;
		color: var(--ink-soft);
	}
	mark {
		background: var(--search-hit);
		color: var(--ink);
		border-radius: 2px;
		padding: 0 0.05em;
	}
	.search-note {
		margin: 0;
		padding: 0.9rem 1rem;
		font-size: 0.85rem;
		color: var(--muted);
	}
	.search-foot {
		display: flex;
		gap: 1rem;
		margin: 0;
		padding: 0.45rem 0.9rem;
		font-size: 0.72rem;
		color: var(--muted);
		border-top: 1px solid var(--rule);
		background: var(--bg-panel);
	}
	.search-foot kbd {
		margin-right: 0.15rem;
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}

	/* Phones: an icon button in the header; once tapped, the field expands to
	   cover the header (the header is the containing block — it's sticky). */
	@media (max-width: 719px) {
		.search {
			position: static;
		}
		.search-toggle {
			display: block;
		}
		.search-field,
		.search-foot {
			display: none;
		}
		.search--expanded {
			position: absolute;
			inset: 0;
			z-index: 20;
			display: flex;
			align-items: center;
			padding: 0 1.25rem;
			background: var(--bg);
		}
		.search--expanded .search-toggle {
			display: none;
		}
		.search--expanded .search-field {
			display: flex;
			flex: 1;
		}
		.search--expanded input {
			width: 100%;
			/* 16px stops iOS Safari zooming the page on focus. */
			font-size: 1rem;
		}
		.search-kbd {
			display: none;
		}
		.search-panel {
			left: 0.75rem;
			right: 0.75rem;
			width: auto;
			top: calc(100% + 0.25rem);
		}
	}
</style>
