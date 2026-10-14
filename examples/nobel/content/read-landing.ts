/** Read Nobel-specific scrollytelling copy and chart states; depends on landing.json. */
import landingJson from './landing.json';

/** What the title-page scatter shows while a scrollytelling step is active.
 *  Consumed by LandingScrolly, which maps it onto NobelRankScatter's props. */
export interface LandingChartState {
	/** Rank metric key (see nobelists.json `metrics`). Omitted = keep whatever the
	 *  reader last picked, so the free-explore step doesn't override their choice. */
	metric?: string;
	/** 'none' = uniform grey dots; 'category' = coloured by prize field. */
	color: 'none' | 'category';
	/** Row id of one laureate to spotlight and label, or null. */
	focus: number | null;
	/** Open the focused laureate's card (portrait + Wikipedia link) in place of
	 *  the label, to show what clicking a dot does. Default false. */
	card?: boolean;
	/** Shade the rank range from this threshold to 100 during this step. */
	highlightFrom?: number;
	/** Toolbar state: hidden; interactive legend and points; those plus
	 *  scroll-driven metric pills; or all controls reader-operable. */
	controls: 'hidden' | 'legend' | 'display' | 'interactive';
}

export interface LandingStep {
	id: string;
	text: string;
	chart: LandingChartState;
}

export interface LandingContent {
	scrollCue: string;
	/** Metric keys offered by the pill selector, in display order. The other
	 *  metrics (education, prestige) stay in the dataset; add their keys here to
	 *  bring them back. */
	metrics: string[];
	/** Short pill labels keyed by metric key (the dataset labels are longer). */
	metricLabels: Record<string, string>;
	steps: LandingStep[];
	/** Label of the "Begin reading" button shown in the final step's card. */
	cta: string;
	/** Support acknowledgment at the bottom of the homepage. */
	acknowledgment: { text: string; href?: string }[];
}

export const landing = landingJson as LandingContent;

