<!-- Reproducible fictional figure with metric tabs and hover values; depends on ddl-charts and results.json. -->
<script lang="ts">
  import { select } from 'd3';
  import { onMount } from 'svelte';
  import { createContainer, createLinearScale } from '@devdatalab/ddl-charts';
  import results from '../reproduction/results.json';
  import { base } from '$app/paths';
  let { number = '1', caption = 'Group means in the fictional sample.' }: { number?: string; caption?: string | null } = $props();
  let metric = $state<'outcome' | 'hours'>('outcome');
  let host: HTMLDivElement;
  let mounted = $state(false);
  let plotWidth = $state(280);
  onMount(() => {
    const observer = new ResizeObserver(() => { plotWidth = Math.max(host.clientWidth, 280); });
    observer.observe(host);
    mounted = true;
    return () => observer.disconnect();
  });
  $effect(() => {
    const selected = metric;
    if (!mounted || !host) return;
    host.replaceChildren();
    const width = plotWidth;
    const chart = createContainer(select(host), { width, height: 260, responsive: false, margin: { top: 20, right: 25, bottom: 45, left: 45 } });
    const x = createLinearScale({ domain: [0, 3], range: [0, chart.dimensions.innerWidth] });
    const max = Math.max(...results.groups.map((group) => group[selected])) * 1.2;
    const y = createLinearScale({ domain: [0, max], range: [chart.dimensions.innerHeight, 0] });
    chart.chartArea.append('line').attr('x2', chart.dimensions.innerWidth).attr('y1', y(0)).attr('y2', y(0)).attr('stroke', 'currentColor');
    results.groups.forEach((group, i) => {
      chart.chartArea.append('rect').attr('x', x(i + 0.5)).attr('y', y(group[selected])).attr('width', x(0.7)).attr('height', y(0) - y(group[selected])).attr('fill', 'var(--accent)').append('title').text(`${group.name}: ${group[selected]}`);
      chart.chartArea.append('text').attr('x', x(i + 0.85)).attr('y', chart.dimensions.innerHeight + 25).attr('text-anchor', 'middle').attr('fill', 'currentColor').text(group.name);
      chart.chartArea.append('text').attr('x', x(i + 0.85)).attr('y', y(group[selected]) - 7).attr('text-anchor', 'middle').attr('fill', 'currentColor').text(group[selected]);
    });
  });
</script>
<figure>
  <figcaption><strong>Figure {number}.</strong> {caption}</figcaption>
  <div class="controls ui" aria-label="Displayed measure">
    <button class:active={metric === 'outcome'} aria-pressed={metric === 'outcome'} onclick={() => metric = 'outcome'}>Outcome</button>
    <button class:active={metric === 'hours'} aria-pressed={metric === 'hours'} onclick={() => metric = 'hours'}>Study hours</button>
  </div>
  <div bind:this={host} class="chart" role="img" aria-label="Group means: {results.groups.map(g => `${g.name} ${g[metric]}`).join(', ')}"></div>
  <p class="note ui">Notes: fictional observations; arithmetic means within each group. Hover over a bar to inspect its value. Source: <a href="{base}/replication#code-make_all">make_all.py</a>.</p>
</figure>
<style>
  figure { margin: 1.5rem 0; }
  .chart { width: 100%; min-height: 260px; }
  .controls { display: flex; gap: 0.5rem; margin: 1rem 0; }
  button { padding: 0.35rem 0.7rem; border: 1px solid var(--rule); border-radius: 4px; background: var(--bg); color: var(--ink); cursor: pointer; }
  button.active { background: var(--accent); color: white; }
  .note { color: var(--muted); font-size: 0.8rem; }
</style>
