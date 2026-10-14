/** Neutral defaults for an instructional paper; depends on content and registered exhibits. */
import type { PaperConfig } from '$lib/reading/paper';
const config: PaperConfig = {
  siteUrl: '',
  credit: 'Design by Development Data Lab',
  exampleNotice: 'Instructional example using fictional observations. Adapt this paper with your local coding agent.',
  tour: false,
  extras: [{ id: 'replication', number: '', title: 'Replicate or remix' }]
};
export default config;
