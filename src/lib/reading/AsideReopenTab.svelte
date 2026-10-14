<!--
	AsideReopenTab — a slim button pinned to the right viewport edge that
	brings the collapsed "Additional Information" aside back. Rendered by
	+layout.svelte only while the aside is collapsed on a content page (never
	on the title/explorer pages or in mobile mode). Its own component so the
	fixed-position chrome and label styling stay out of the layout file.

	Upstream dependency: asidePanel store.
-->
<script lang="ts">
	import { asidePanel } from '$lib/state/asidePanel.svelte';
</script>

<button
	type="button"
	class="reopen-tab ui"
	aria-label="Show additional information"
	onclick={() => asidePanel.expand()}
>
	<span class="chevron" aria-hidden="true">‹</span>
	<span class="label">Additional<br />Info</span>
</button>

<style>
	/* A small floating button pinned to the right edge, vertically centered.
	   Left-pointing chevron cues that it slides a panel in from the right. Sits
	   flush against the right edge with only its left corners rounded. */
	.reopen-tab {
		position: fixed;
		right: 0;
		top: 50%;
		transform: translateY(-50%);
		z-index: 9;
		display: flex;
		align-items: center;
		gap: 0.4rem;
		padding: 0.5rem 0.8rem;
		border: 1px solid var(--rule-strong);
		border-right: none;
		border-radius: var(--ddl-border-radius, 4px) 0 0 var(--ddl-border-radius, 4px);
		background: var(--bg-panel);
		color: var(--ink-soft);
		font-size: 0.78rem;
		font-weight: 600;
		letter-spacing: 0.02em;
		cursor: pointer;
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
		transition:
			color var(--ddl-transition-fast, 0.15s ease),
			background var(--ddl-transition-fast, 0.15s ease),
			box-shadow var(--ddl-transition-fast, 0.15s ease);
	}
	.reopen-tab:hover {
		color: var(--accent);
		background: #fff;
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.14);
	}
	.chevron {
		font-size: 1.05rem;
		line-height: 1;
		margin-top: -1px;
	}
	.label {
		white-space: nowrap;
		line-height: 1.15;
	}
</style>
