/** Configure the independent Nobel teaching excerpt; depends on its content and exhibits. */
import type { PaperConfig } from '$lib/reading/paper';
const config: PaperConfig = {
  siteUrl: '',
  credit: 'Design by Development Data Lab',
  exampleNotice: 'Teaching excerpt: selected original content and illustrative placeholders. The complete Nobel publication is maintained separately at nobel-prizes.devdatalab.org.',
  tour: true,
  extras: [
    { id: 'data-explorer', number: '', title: 'Raw Data Explorer' },
    { id: 'occupation-rank-explorer', number: '', title: 'Occupation Explorer' },
    { id: 'extended-results', number: '', title: 'Extended Results' },
    { id: 'replication', number: '', title: 'Replicate or remix' }
  ]
};
export default config;
