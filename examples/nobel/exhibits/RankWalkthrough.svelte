<!--
	RankWalkthrough — the A4 "Additional Information" panel for Data and Methods.

	Walks a reader through how a laureate's father's occupation becomes first a
	national and then a global income percentile rank, one step at a time, on six
	contrasting laureates spanning rich/poor country × high/modest occupation, plus
	two edge cases: Rutherford (New Zealand richer than the U.S., so incomes scale
	*up* and a wheelwright lands globally elite) and Marie Curie (a gentle, not
	steep, downward shift from a moderately poor country). Every value shown is a
	real extracted figure from rankWalkthroughData — the component does no rank
	computation, it only formats and lays out stored values.

	Rendered in the ~300px right pane via appendixRegistry (see AnnotationPanel).
	Takes no props: it owns its own laureate selection. The single visual is a
	static 0–100 SVG track showing the national → global shift.

	Upstream dependencies:
	  - $nobel/data (rankWalkthroughData, RankWalkthroughLaureate)
	  - assets/portraits/credits.json and local Commons portraits, credits and licences
-->
<script lang="ts">
	import { base } from '$app/paths';
	import portraits from '$nobel/assets/portraits/credits.json';
	import {
		rankWalkthroughData,
		type RankWalkthroughLaureate
	} from '$nobel/data';

	const laureates = rankWalkthroughData.laureates;
	let selectedId = $state(laureates[0].id);
	const L = $derived<RankWalkthroughLaureate>(
		laureates.find((l) => l.id === selectedId) ?? laureates[0]
	);

	// Local portraits keep the walkthrough independent of external image hosts.
	const portrait = $derived(portraits[L.id as keyof typeof portraits]);

	// National = blue, global = cranberry — the same hues OccupationRankChart uses
	// for its two rank series, kept explicit so they read the same across themes.
	const NATIONAL_COLOR = '#0072B2';
	const GLOBAL_COLOR = '#A3324C';

	// Whole percentiles, but keep decimals near the ceiling so 99.6 vs 99.97 stay
	// distinct (Sharpless). Presentation only; stored values keep full precision.
	function rank(v: number): string {
		if (v >= 99.9) return v.toFixed(2);
		if (v >= 99) return v.toFixed(1);
		return Math.round(v).toString();
	}
</script>

<div class="rank-walk ui">
	<div class="selector" role="group" aria-label="Choose a laureate">
		{#each laureates as l (l.id)}
			<button
				type="button"
				class="pill"
				class:selected={l.id === selectedId}
				aria-pressed={l.id === selectedId}
				onclick={() => (selectedId = l.id)}
			>
				{l.short}
			</button>
		{/each}
	</div>

	<div class="input-card">
		<p class="name">{L.name}</p>
		<p class="meta">{L.category} {L.prizeYear}</p>
		<p class="meta background">Born {L.country} - Father: {L.fatherOccupation}</p>
		<div class="portrait">
			{#if portrait?.img}
				<img
					src={`${base}/${portrait.img}`}
					alt={`Portrait of ${L.name}. Photo: ${portrait.credit ?? 'Wikimedia Commons'}. ${portrait.license ?? ''}. Source: ${portrait.source ?? ''}`}
					width="250"
					height="250"
					referrerpolicy="no-referrer"
					decoding="async"
				/>
			{/if}
		</div>
		{#if portrait}<p class="photo-credit"><a href={portrait.source}>Photo: {portrait.credit}</a> · {#if 'licenseUrl' in portrait}<a href={portrait.licenseUrl}>{portrait.license}</a>{:else}{portrait.license}{/if}</p>{/if}
	</div>

	<ol class="steps">
		<li>
			<span class="badge">1</span>
			<div class="step-body">
				<p class="step-title">Standardize the occupation</p>
				<p class="step-detail">
					“{L.fatherOccupation}” → the census occ1950 category <em>{L.occ1950Label}</em>.
				</p>
			</div>
		</li>
		<li>
			<span class="badge">2</span>
			<div class="step-body">
				<p class="step-title">Match a U.S. census decade</p>
				<p class="step-detail">
					{#if L.usBorn}
						U.S.-born, so we read the {L.matchedDecade} U.S. census directly.
					{:else}
						{L.country} in the {L.birthDecade}s is matched to the U.S. {L.matchedDecade}
						census — its nearest level of development.
					{/if}
				</p>
			</div>
		</li>
		<li>
			<span class="badge">3</span>
			<div class="step-body">
				<p class="step-title">
					National income rank <span class="rank-val">{rank(L.nationalIncomeRank)}</span>
				</p>
				<p class="step-detail">
					This is the average income rank in {L.matchedDecade} of a working-age man with this occupation.
					<span class="aside"
						>{rank(L.educationRank)} is the average education rank.</span
					>
				</p>
			</div>
		</li>
		<li>
			<span class="badge">4</span>
			<div class="step-body">
				<p class="step-title">
					Global income rank <span class="rank-val">{rank(L.globalIncomeRank)}</span>
				</p>
				<p class="step-detail">
					{#if L.usBorn}
						Rerank in the synthetic global population distribution: the global rank is higher
						because the U.S. is a very rich country.
					{:else if L.id === 'banerjee'}
						Rerank in the synthetic global population distribution: the global rank is lower
						because India was a very poor country (0.05× the U.S.).
					{:else if L.id === 'rutherford'}
						Rerank in the synthetic global population distribution: the global rank is higher
						because New Zealand was a rich country.
					{:else if L.id === 'curie'}
						Rerank in the synthetic global population distribution: the global rank is lower
						because Poland was relatively poor at this time.
					{:else if L.id === 'tsui'}
						Rerank in the synthetic global population distribution: the global rank is lower
						because China was a very poor country (0.06× the U.S.).
					{/if}
				</p>
			</div>
		</li>
	</ol>

	<div class="rank-cards">
		<div class="rank-card" style="--card-color:{NATIONAL_COLOR}">
			<span class="rank-card-label">National income rank</span>
			<span class="rank-card-val">{rank(L.nationalIncomeRank)}</span>
		</div>
		<div class="rank-card" style="--card-color:{GLOBAL_COLOR}">
			<span class="rank-card-label">Global income rank</span>
			<span class="rank-card-val">{rank(L.globalIncomeRank)}</span>
		</div>
	</div>
</div>

<style>
	/* The host .component-block sits on the card's own text margin, so this panel
	   already lines up with the surrounding body copy — no padding of its own. */
	.rank-walk {
		font-size: 0.82rem;
		line-height: 1.5;
		color: var(--ink-soft, #3a3a3a);
	}
	.selector {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		margin-bottom: 0.85rem;
	}
	.pill {
		font-family: var(--font-ui, inherit);
		font-size: 0.75rem;
		padding: 0.25rem 0.55rem;
		border: 1px solid var(--rule-strong, #ccc);
		border-radius: 999px;
		background: var(--bg, #fff);
		color: var(--ink, #1a1a1a);
		cursor: pointer;
	}
	.pill:hover {
		background: var(--ddl-color-hover, rgba(0, 0, 0, 0.05));
	}
	.pill.selected {
		background: var(--accent, #e8871e);
		border-color: var(--accent, #e8871e);
		color: #fff;
	}
	.pill:focus-visible {
		outline: 2px solid var(--accent);
		outline-offset: 1px;
	}
	.input-card {
		padding: 0.55rem 0.65rem;
		border: 1px solid var(--rule, #e7e7e4);
		border-radius: var(--ddl-border-radius, 4px);
		background: var(--bg-panel, rgba(0, 0, 0, 0.02));
		margin-bottom: 0.9rem;
	}

	/* Fixed portraits fill most of an ordinary sidebar without scaling with the page. */
	.portrait {
		width: 250px;
		height: 250px;
		margin-top: 0.5rem;
		overflow: hidden;
		border-radius: var(--ddl-border-radius, 4px);
		background: var(--rule, #e7e7e4);
	}
	.photo-credit {
		margin: 0.35rem 0 0;
		font-size: 0.65rem;
		line-height: 1.4;
		color: var(--muted);
	}
	.portrait img {
		display: block;
		width: 250px;
		height: 250px;
		object-fit: cover;
		object-position: 50% 20%;
	}
	.background {
		min-block-size: 2lh;
	}
	.input-card .name {
		margin: 0 0 0.15rem;
		font-family: var(--font-serif, inherit);
		font-weight: 600;
		font-size: 0.9rem;
		color: var(--ink, #1a1a1a);
	}
	.input-card .meta {
		margin: 0;
		font-size: 0.76rem;
		color: var(--muted, #888);
	}
	.steps {
		list-style: none;
		margin: 0 0 0.9rem;
		padding: 0;
	}
	.steps li {
		display: flex;
		gap: 0.55rem;
		padding: 0.55rem 0;
		border-top: 1px solid var(--rule, #eee);
	}
	.steps li:first-child {
		border-top: none;
	}
	.badge {
		flex: none;
		width: 1.35rem;
		height: 1.35rem;
		border-radius: 50%;
		background: var(--ink, #1a1a1a);
		color: #fff;
		font-size: 0.72rem;
		font-weight: 700;
		display: inline-flex;
		align-items: center;
		justify-content: center;
	}
	.step-body {
		min-width: 0;
	}
	.step-title {
		margin: 0 0 0.15rem;
		font-weight: 600;
		color: var(--ink, #1a1a1a);
	}
	.rank-val {
		margin-left: 0.3rem;
		font-family: var(--font-serif, inherit);
		font-size: 1.05rem;
		font-weight: 700;
		color: var(--accent, #e8871e);
		white-space: nowrap;
	}
	.step-detail {
		margin: 0;
		font-size: 0.78rem;
	}
	.step-detail em {
		font-style: normal;
		font-weight: 600;
		color: var(--ink, #1a1a1a);
	}
	.aside {
		display: block;
		margin-top: 0.2rem;
		color: var(--muted, #888);
		font-size: 0.73rem;
	}
	/* Two summary cards replacing the old 0–100 track: the national and global
	   income ranks side by side, each accented with its series colour. */
	.rank-cards {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.5rem;
	}
	.rank-card {
		display: flex;
		flex-direction: column;
		gap: 0.1rem;
		padding: 0.55rem 0.6rem;
		border: 1px solid var(--rule, #e7e7e4);
		border-left: 3px solid var(--card-color, var(--accent, #e8871e));
		border-radius: var(--ddl-border-radius, 4px);
		background: var(--bg-panel, rgba(0, 0, 0, 0.02));
	}
	.rank-card-label {
		font-size: 0.72rem;
		font-weight: 600;
		color: var(--ink, #1a1a1a);
		line-height: 1.25;
	}
	.rank-card-val {
		font-family: var(--font-serif, inherit);
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--card-color, var(--accent, #e8871e));
		line-height: 1.1;
	}
</style>
