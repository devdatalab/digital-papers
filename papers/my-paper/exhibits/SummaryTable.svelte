<!-- Show the same computed means as the chart; depends on the reproducible results export. -->
<script lang="ts">
  import results from '../reproduction/results.json';
  let { number = '1', caption = 'Summary of the fictional sample.' }: { number?: string; caption?: string | null } = $props();
</script>
<figure>
  <figcaption><strong>Table {number}.</strong> {caption}</figcaption>
  <table><thead><tr><th>Group</th><th>Observations</th><th>Mean outcome</th><th>Mean hours</th></tr></thead>
    <tbody>{#each results.groups as group}<tr><th>{group.name}</th><td>{group.n}</td><td>{group.outcome}</td><td>{group.hours}</td></tr>{/each}</tbody>
  </table>
  <p class="ui">Notes: fictional observations; arithmetic means within each group.</p>
</figure>
<style>figure { margin: 1.5rem 0; } table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; } th, td { text-align: right; padding: 0.6rem; border-bottom: 1px solid var(--rule); } th:first-child { text-align: left; } p { font-size: 0.8rem; color: var(--muted); }</style>
