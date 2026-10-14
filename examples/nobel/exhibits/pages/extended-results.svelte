<!--
	Extended Results — a bespoke, full-width Extras page presenting the paper's
	core SES finding across every SES-measure × outcome × subgroup permutation the
	printed paper never enumerates (national/education/global income rank ×
	average-rank / top-10% / top-20% trends × overall/field/gender/region).

	Why it exists: it reimagines the standalone nobel-agents/main_results dashboard
	as a native part of this edition, linked from the Results section. Two selectors
	drive a 2×2 grid of interactive charts (see ExtendedResultsExplorer).

	The route sits in the left nav's "Extras" group and gets the wide explorer
	shell (`shell--explorer`) from the root layout (see `explorerRoutes` in
	src/routes/+layout.svelte).

	Upstream dependencies:
	  - $lib/content (meta — for the document <title>)
	  - $nobel/exhibits/ExtendedResultsExplorer
-->
<script lang="ts">
	import { meta } from '$lib/content';
	import ExtendedResultsExplorer from '$nobel/exhibits/ExtendedResultsExplorer.svelte';
</script>

<svelte:head>
	<title>Extended Results — {meta.title}</title>
</svelte:head>

<article class="explorer">
	<header class="explorer-head">
		<p class="kicker ui">Explore further</p>
		<h1>Extended Results</h1>
		<p class="lede ui">We used this section to give the readers total flexibility over a set of parameter and subset choices for the main exhibits in the paper. This lets you show way more than you would put into an appendix and eliminates any concern about data mining.</p>
	</header>

	<ExtendedResultsExplorer />
</article>

<style>
	.explorer {
		padding-top: 0.5rem;
	}
	.explorer-head {
		max-width: var(--read-max);
		margin-bottom: 2rem;
	}
	.kicker {
		font-size: 0.75rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--accent);
		margin: 0 0 0.6rem;
	}
	.explorer-head h1 {
		font-family: var(--font-serif);
		font-size: clamp(1.8rem, 3.5vw, 2.4rem);
		line-height: 1.15;
		font-weight: 600;
		color: var(--ink);
		margin: 0 0 1rem;
		letter-spacing: -0.01em;
	}
	.lede {
		font-size: 0.85rem;
		line-height: 1.5;
		color: var(--muted);
		margin: 0;
	}
</style>
