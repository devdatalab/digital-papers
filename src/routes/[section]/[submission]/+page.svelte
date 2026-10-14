<!--
	Numbered referee-submission pages reuse the existing section page so the reading
	shell, heading, and neighbouring-section links stay identical. Data comes from
	this route's guarded loader; only the displayed submission changes.
-->
<script lang="ts">
	import SectionPage from '../+page.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
</script>

<SectionPage {data} submission={data.submission} />
