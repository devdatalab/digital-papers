/**
 * Ambient module declaration for @devdatalab/ddl-charts.
 *
 * Why this file exists: the ddl-charts package is plain JS and ships no
 * TypeScript declarations, so importing it triggers "could not find a
 * declaration file" under noImplicitAny. We type it as `any` here; call sites in
 * our code annotate their own callback parameters where needed.
 */
declare module '@devdatalab/ddl-charts';
