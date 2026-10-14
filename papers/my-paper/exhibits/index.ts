/** Register the small paper's figure, table, and interactive context panel. */
import type { Component } from 'svelte';
import CompareGroups from './CompareGroups.svelte';
import SummaryTable from './SummaryTable.svelte';
export { default as Cover } from './Cover.svelte';
export const figures: Record<string, Component<any>> = { 'fig:groups': CompareGroups, 'tab:summary': SummaryTable };
export const panels: Record<string, Component<any>> = { CompareGroups };
export const pages: Record<string, Component<any>> = {};
