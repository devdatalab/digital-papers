<!--
	One submission in the public referee-response section. Reads the author's saved
	text from referee-submissions.json; private reports and editing tools stay separate.
	Uses the site's reading/theme tokens and ordinary prerendered links for navigation.
	Paragraphs and numbered lists retain the saved wording; manuscript URLs start empty.
	The section JSON supplies the introduction; only disclosed votes are shown as votes.
-->
<script lang="ts">
	import { base } from '$app/paths';
	import content from '$paper/content/referee-submissions.json';
	import { getSection } from '$lib/content';
	import { inlineText } from '$lib/content/text';

	let { submission = 1 }: { submission?: number } = $props();
	const submissions = content.submissions as {
		id: string;
		journal: string;
		journalUrl: string;
		manuscriptUrl: string | null;
		submissionDate: string | null;
		responseDate: string | null;
		preamble: string;
		editor: string;
		editorName?: string;
		response: string;
		referees: { name: string; vote: string }[];
	}[];
	const first = getSection('referee-comments-and-responses')?.blocks[0];
	const introduction = first?.type === 'paragraph' ? inlineText(first.nodes) : '';
	const dateFormat = new Intl.DateTimeFormat('en-US', {
		month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC'
	});
	const formatDate = (date: string) => dateFormat.format(new Date(date));
	let current = $derived(submissions[submission - 1]);
	const href = (number: number) =>
		`${base}/referee-comments-and-responses${number === 1 ? '' : `/${number}`}`;

	type TextBlock = { type: 'paragraph'; text: string } | { type: 'list'; start: number; items: string[] };

	function textBlocks(text: string): TextBlock[] {
		const blocks: TextBlock[] = [];
		for (const paragraph of text.trim().split(/\n\s*\n/).filter(Boolean)) {
			for (const line of paragraph.split('\n')) {
				const numbered = line.match(/^(\d+)\.\s+(.*)$/);
				const previous = blocks.at(-1);
				if (numbered) {
					const number = Number(numbered[1]);
					if (previous?.type === 'list' && previous.start + previous.items.length === number) {
						previous.items.push(numbered[2]);
					} else {
						blocks.push({ type: 'list', start: number, items: [numbered[2]] });
					}
				} else {
					blocks.push({ type: 'paragraph', text: line });
				}
			}
		}
		return blocks;
	}
</script>

{#snippet navigation(position: string)}
	<nav class="submission-nav ui" data-sveltekit-noscroll aria-label="Submission navigation ({position})">
		{#if submission > 1}
			<a href={href(submission - 1)} rel="prev" aria-label="Previous submission">← Previous</a>
		{:else}
			<span class="nav-placeholder" aria-hidden="true">← Previous</span>
		{/if}
		<span class="position">Submission {submission} / {submissions.length}: <a href={current.journalUrl}>{current.journal}</a></span>
		{#if submission < submissions.length}
			<a href={href(submission + 1)} rel="next" aria-label="Next submission">Next →</a>
		{:else}
			<span class="nav-placeholder" aria-hidden="true">Next →</span>
		{/if}
	</nav>
{/snippet}

{#snippet inline(text: string)}
	{#each text.split(/(https?:\/\/[^\s)]+)/) as part}
		{#if /^https?:\/\//.test(part)}<a href={part}>{part}</a>{:else}{part}{/if}
	{/each}
{/snippet}

{#snippet passage(text: string)}
	{#each textBlocks(text) as block}
		{#if block.type === 'paragraph'}
			<p>{@render inline(block.text)}</p>
		{:else}
			<ol start={block.start}>
				{#each block.items as item}<li>{@render inline(item)}</li>{/each}
			</ol>
		{/if}
	{/each}
{/snippet}

<div class="referee-responses">
	<p id="b-0" class="intro ui">{introduction}</p>
	{@render navigation('top')}
	<section aria-label="Submission {submission}: {current.journal}">
		<section class="author-note" aria-labelledby="submitted-heading">
			<h2 id="submitted-heading" class="author-heading">
				<span>
					What we submitted
					{#if current.submissionDate}
						<span class="date">(<time datetime={current.submissionDate}>{formatDate(current.submissionDate)}</time>)</span>
					{/if}
				</span>
				<span class="manuscript">
					{#if current.manuscriptUrl}
						<a href={current.manuscriptUrl}>Manuscript ↗</a>
					{:else}
						<span role="link" aria-disabled="true" title="Manuscript link to be added">Manuscript ↗</span>
					{/if}
				</span>
			</h2>
			<div class="author-text preamble">{@render passage(current.preamble)}</div>
		</section>
		<section aria-labelledby="editor-heading">
			<div class="editor-heading">
				<h2 id="editor-heading">
					Editor's comments
					{#if current.responseDate}
						<span class="date">({#if current.editorName}{current.editorName},{' '}{/if}<time datetime={current.responseDate}>{formatDate(current.responseDate)}</time>)</span>
					{/if}
				</h2>
				{#if current.referees.length}
					<ul class="votes ui" aria-label="Referee votes">
						{#each current.referees as referee}
							<li>{referee.name}: {referee.vote}</li>
						{/each}
					</ul>
				{/if}
			</div>
			<blockquote>{@render passage(current.editor)}</blockquote>
		</section>
		{#if current.response.trim()}
			<section class="author-note" aria-labelledby="response-heading">
				<h2 id="response-heading" class="author-heading">How we changed the paper</h2>
				<div class="author-text">{@render passage(current.response)}</div>
			</section>
		{/if}
	</section>
	{@render navigation('bottom')}
</div>

<style>
	.referee-responses {
		overflow-wrap: anywhere;
	}

	.intro {
		font-size: 0.85rem;
		line-height: 1.5;
		color: var(--muted);
	}

	.submission-nav {
		display: grid;
		grid-template-columns: max-content minmax(0, 1fr) max-content;
		align-items: center;
		gap: 0.75rem;
		padding: 0.6rem 0;
		border-block: 1px solid var(--rule);
		font-size: 0.85rem;
		font-weight: 500;
	}

	.position {
		text-align: center;
		font-variant-numeric: tabular-nums;
		color: var(--ink-soft);
	}

	.nav-placeholder {
		visibility: hidden;
	}

	.manuscript [aria-disabled] {
		color: var(--muted);
	}

	h2 {
		margin: 0;
		font: 600 0.85rem/1.5 var(--font-ui);
	}

	.author-note {
		margin: 1rem 0;
		padding: 0.9rem 1rem;
		border: 1px solid var(--rule);
		border-radius: var(--ddl-border-radius, 4px);
		background: var(--bg-panel);
		font-size: 0.95rem;
		line-height: 1.6;
	}

	.author-heading {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		gap: 0.25rem 0.75rem;
		margin-bottom: 0.6rem;
	}

	.author-text {
		font-style: italic;
	}

	.author-text > :last-child {
		margin-bottom: 0;
	}

	.editor-heading {
		display: flex;
		align-items: baseline;
		flex-wrap: wrap;
		gap: 0.25rem 0.75rem;
		margin: 1.25rem 0 0.65rem;
	}

	.votes {
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem 0.75rem;
		list-style: none;
		margin: 0;
		padding: 0;
		color: var(--ink-soft);
		font-size: 0.75rem;
		line-height: 1.5;
	}

	.votes li {
		margin: 0;
		padding: 0;
	}

	p,
	ol {
		margin: 0 0 1rem;
	}

	ol {
		padding-left: 1.5rem;
	}

	li {
		padding-left: 0.2rem;
	}

	li + li {
		margin-top: 0.5rem;
	}

	.manuscript,
	.date {
		font-weight: 400;
	}

	blockquote {
		font-size: 0.95rem;
		line-height: 1.6;
		margin: 0;
		padding-left: 1rem;
		border-left: 2px solid var(--rule-strong);
		color: var(--ink-soft);
	}

	a:focus-visible {
		outline: 2px solid var(--accent);
		outline-offset: 3px;
	}
</style>
