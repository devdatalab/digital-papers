/** Public paper configuration; the shared shell consumes this small interface. */
export interface PaperConfig {
  siteUrl: string;
  credit: string;
  logo?: string;
  exampleNotice?: string;
  extras: { id: string; number: string; title: string }[];
  tour: boolean;
}
