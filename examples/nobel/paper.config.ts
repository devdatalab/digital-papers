/** Configure the independent Nobel teaching excerpt; depends on its content and exhibits. */
import type { PaperConfig } from '$lib/reading/paper';
const config: PaperConfig = {
  siteUrl: '',
  headerTitle: 'Access to Opportunity in the Sciences (example)',
  replicationIntro: 'The goal of this section is to make replication data totally comprehensible to an LLM, so that a reader can direct a local agent to this repo and it can download all the data and run any variant of the analysis with just a prompt.',
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
