<!-- Shared declarative exhibit frame with optional paper branding.
     Depends on paper.config.ts, theme classes and context-panel chrome. -->
<script lang="ts">
	import type { Snippet } from 'svelte';
	import config from '$paper/paper.config';
	import { base } from '$app/paths';
	import { BARE_CLASS, useBareChrome } from './brandChrome';

	const bare = useBareChrome();

	let {
		label,
		title,
		subtitle,
		source,
		sourceUrl,
		controls,
		children
	}: {
		label?: string;
		title?: string;
		subtitle?: string;
		source?: string;
		sourceUrl?: string;
		controls?: Snippet;
		children: Snippet;
	} = $props();
</script>

<div class="ddl-branded-container {bare ? BARE_CLASS : ''}">
	{#if label || title || subtitle}
		<div class="ddl-branded-header">
			{#if label || title}
				<h3 class="ddl-branded-title">
					{#if label}<span class="ddl-branded-label">{label}</span>{/if}{title}
				</h3>
			{/if}
			{#if subtitle}<p class="ddl-branded-subtitle">{subtitle}</p>{/if}
			{#if controls}<div class="ddl-branded-controls">{@render controls()}</div>{/if}
		</div>
	{/if}
	<div class="ddl-branded-body">
		{@render children()}
	</div>
	<!-- Bare mode drops the mark, so a sourceless footer would render as pure
	     empty space — skip it entirely rather than leave the padding behind. -->
	{#if source || !bare}
		<div class="ddl-branded-footer">
			{#if source}
				<span class="ddl-branded-source">
					Source:
					{#if sourceUrl}
						<a href={sourceUrl} target="_blank" rel="noopener">{source}</a>
					{:else}
						{source}
					{/if}
				</span>
			{:else}
				<span></span>
			{/if}
			{#if !bare && config.logo}<img src="{base}/{config.logo}" alt="Publication logo" height="20" />{/if}
		</div>
	{/if}
</div>

<style>
	.ddl-branded-header {
		padding-top: 0;
		padding-bottom: 8px;
	}

	.ddl-branded-title {
		margin-top: 16.2px;
	}

	.ddl-branded-subtitle {
		margin-bottom: 16.2px;
	}

	.ddl-branded-label {
		display: inline-block;
		font-size: 0.72em;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--accent);
		margin-right: 0.5em;
	}

	.ddl-branded-controls {
		margin-top: 0.6rem;
	}

	/* Bare mode: the margins above stand in for the wrapper's header padding,
	   which is what makes the title clear the container's top edge. With no
	   wrapper there is no edge to clear, so collapse them and let the pane
	   card's own padding do the spacing. (Container-level chrome is stripped in
	   app.css; these two are BrandedFrame's own overrides of the ddl-theme
	   defaults, so they have to be undone here.) */
	.ddl-bare .ddl-branded-title {
		margin-top: 0;
	}

	.ddl-bare .ddl-branded-subtitle {
		margin-bottom: 0;
	}
</style>
