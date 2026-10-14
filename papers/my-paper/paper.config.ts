/** Neutral defaults for an instructional paper; depends on content and registered exhibits. */
import type { PaperConfig } from '$lib/reading/paper';
const config: PaperConfig = {
  siteUrl: '',
  credit: 'Design by Development Data Lab',
  exampleNotice: 'Starting template using fictional observations. Replace these with your paper and reproducible exhibits.',
  tour: false,
  extras: [{ id: 'replication', number: '', title: 'Replicate or remix' }]
};
export default config;
