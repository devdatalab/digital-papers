<!--
	SectionNav — the left-hand table of contents.

	Why it exists: gives the reader persistent, one-click navigation between the
	top-level sections of the paper (the publication serves one section per page).
	Lives in the layout so it persists across section navigations.

	Props:
	  - entries: paper sections, split into numbered content and unnumbered revisions/FAQ
	  - extras: bespoke interactive pages shown under "Explore further"
	  - currentId: slug of the section currently being read (for active styling)
-->
<script lang="ts">
	import { base } from '$app/paths';
	import type { ManifestEntry } from '$lib/content';

	let {
		entries,
		extras = [],
		currentId
	}: { entries: ManifestEntry[]; extras?: ManifestEntry[]; currentId: string | null } = $props();

	const revisionIds = new Set(['referee-comments-and-responses', 'faq']);
	let paperEntries = $derived(entries.filter((entry) => !revisionIds.has(entry.id)));
	let revisionEntries = $derived(entries.filter((entry) => revisionIds.has(entry.id)));
</script>

<nav class="ui section-nav" aria-label="Sections">
	<a class="home" class:active={currentId === null} href="{base}/">Title &amp; abstract</a>
	<ol>
		{#each paperEntries as entry (entry.id)}
			<li>
				<a href="{base}/{entry.id}" class:active={entry.id === currentId}>
					<span class="num">{entry.number}</span>
					<span class="label">{entry.title}</span>
				</a>
			</li>
		{/each}
	</ol>

	{#if revisionEntries.length > 0}
		<p class="group-label">Revisions and FAQ</p>
		<ul class="extras">
			{#each revisionEntries as entry (entry.id)}
				<li>
					<a href="{base}/{entry.id}" class:active={entry.id === currentId}>
						<span class="label">{entry.title}</span>
					</a>
				</li>
			{/each}
		</ul>
	{/if}

	{#if extras.length > 0}
		<p class="group-label">Explore further</p>
		<ul class="extras">
			{#each extras as entry (entry.id)}
				<li>
					<a href="{base}/{entry.id}" class:active={entry.id === currentId}>
						<span class="label">{entry.title}</span>
					</a>
				</li>
			{/each}
		</ul>
	{/if}

</nav>

<style>
	.section-nav {
		font-size: 0.9rem;
		line-height: 1.4;
	}

	.home {
		display: block;
		font-weight: 600;
		color: var(--ink);
		padding: 0.4rem 0.6rem 0.4rem 0.7rem;
		margin-bottom: 0.5rem;
		border-bottom: 1px solid var(--rule);
	}

	ol,
	ul.extras {
		list-style: none;
		margin: 0.75rem 0 0;
		padding: 0;
		counter-reset: none;
	}

	li {
		margin: 0;
	}

	/* Group headers separate the unnumbered navigation groups from the paper. */
	.group-label {
		margin: 1.1rem 0 0;
		padding-top: 0.9rem;
		border-top: 1px solid var(--rule);
		font-size: 0.72rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--muted);
	}

	a {
		display: flex;
		gap: 0.6rem;
		padding: 0.5rem 0.6rem 0.5rem 0;
		color: var(--ink-soft);
		border-left: 2px solid transparent;
		padding-left: 0.7rem;
		margin-left: -0.7rem;
		transition:
			color 0.12s ease,
			border-color 0.12s ease;
	}

	a:hover {
		color: var(--ink);
		text-decoration: none;
	}

	a.active {
		color: var(--accent);
		border-left-color: var(--accent);
		font-weight: 500;
	}

	.num {
		flex-shrink: 0;
		color: var(--muted);
		font-variant-numeric: tabular-nums;
		min-width: 1.1em;
	}

	a.active .num {
		color: var(--accent);
	}
</style>
