/**
 * Keep ddl-charts figures fitted when the reading shell changes their width.
 * The package's createContainer currently observes window resize only, missing
 * hydration and aside-panel changes. This adapter updates its shared dimensions
 * and SVG before redrawing; callers disconnect it on unmount.
 * Upstream dependency: the createContainer return contract in ddl-charts.
 * This behavior belongs in createContainer upstream once the package supports it.
 */
export function observeChartWidth(
	parent: HTMLElement,
	svg: { attr: (name: string, value: number) => unknown },
	dimensions: { width: number; innerWidth: number; margin: { left: number; right: number } },
	redraw: () => void
) {
	const observer = new ResizeObserver(() => {
		const width = parent.getBoundingClientRect().width;
		if (width <= 0 || width === dimensions.width) return;
		dimensions.width = width;
		dimensions.innerWidth = Math.max(0, width - dimensions.margin.left - dimensions.margin.right);
		svg.attr('width', width);
		redraw();
	});
	observer.observe(parent);
	return () => observer.disconnect();
}
