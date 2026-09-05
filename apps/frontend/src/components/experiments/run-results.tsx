import { formatNumber } from '@/lib/format';

type ScoredMetric = { score: number | null; reason?: string };
type Props = {
	detail: {
		run: { status: string; error_message: string | null };
		variants: Array<{ id: string; name: string; status: string; aggregate_metrics: Record<string, number>; error_message: string | null }>;
		cases: Array<{ id: string; variant_run_id: string; position: number; question: string; generated_answer: string | null; metrics: Record<string, unknown> }>;
	};
	metrics: string[];
};

type MetricKind = 'quality' | 'latency' | 'tokens' | 'cost' | 'boolean' | 'number';
type MetricDefinition = { label: string; kind: MetricKind; unit: string };

const METRICS: Record<string, MetricDefinition> = {
	context_precision: { label: 'Context precision', kind: 'quality', unit: '%' },
	context_recall: { label: 'Context recall', kind: 'quality', unit: '%' },
	faithfulness: { label: 'Faithfulness', kind: 'quality', unit: '%' },
	answer_relevance: { label: 'Answer relevance', kind: 'quality', unit: '%' },
	hallucination_detection: { label: 'Groundedness', kind: 'quality', unit: '%' },
	embedding_latency: { label: 'Query embedding latency', kind: 'latency', unit: 'ms' },
	vector_search_latency: { label: 'Vector search latency', kind: 'latency', unit: 'ms' },
	retrieval_latency: { label: 'Retrieval latency', kind: 'latency', unit: 'ms' },
	context_assembly_latency: { label: 'Context assembly latency', kind: 'latency', unit: 'ms' },
	generation_latency: { label: 'Generation latency', kind: 'latency', unit: 'ms' },
	evaluation_latency: { label: 'Evaluation latency', kind: 'latency', unit: 'ms' },
	provider_queue_latency: { label: 'Provider queue latency', kind: 'latency', unit: 'ms' },
	total_latency: { label: 'Total latency', kind: 'latency', unit: 'ms' },
	token_count: { label: 'Token usage', kind: 'tokens', unit: 'tokens' },
	estimated_cost: { label: 'Estimated cost', kind: 'cost', unit: 'USD' },
	embedding_cache_hit: { label: 'Embedding cache', kind: 'boolean', unit: '—' },
};

export function RunResults({ detail, metrics }: Props) {
	const failedVariants = detail.variants.filter(variant => variant.error_message);
	return <section className='experiment-results'>
		<header><div><h3>Run results</h3><p>Variant comparison and case-level outputs.</p></div><span className={`catalog-state ${detail.run.status}`}>{detail.run.status}</span></header>
		{detail.run.error_message && <div className='workspace-error' role='alert'><strong>Run failed</strong><span>{detail.run.error_message}</span></div>}
		{failedVariants.map(variant => <div key={variant.id} className='workspace-error' role='alert'><strong>{variant.name} failed</strong><span>{variant.error_message}</span></div>)}
		<div className='metric-rating-guide' aria-label='Metric rating guide'><strong>Rating guide</strong><span>Quality: Excellent ≥90%, Good ≥75%, Fair ≥50%, Poor &lt;50%</span><span>Latency: Excellent ≤250 ms, Good ≤750 ms, Fair ≤2 s, Poor &gt;2 s</span></div>
		<div className='experiment-comparison'><table><thead><tr><th>Variant</th>{metrics.map(metric => <th key={metric}>{definition(metric).label}</th>)}</tr></thead><tbody>{detail.variants.map(variant => <tr key={variant.id}><td><strong>{variant.name}</strong><small>{variant.status}</small></td>{metrics.map(metric => <td key={metric}><MetricValue metric={metric} value={variant.aggregate_metrics?.[metric]} /></td>)}</tr>)}</tbody></table></div>
		<div className='experiment-case-results'>{detail.variants.map(variant => <section key={variant.id}><h4>{variant.name}</h4>{detail.cases.filter(item => item.variant_run_id === variant.id).map(item => <article key={item.id}><header><strong>Case {item.position + 1}</strong><span>{item.question}</span></header><p>{item.generated_answer || 'No answer generated.'}</p><div className='case-metrics-table'><table><thead><tr><th>Metric</th><th>Result</th><th>Unit</th><th>Rating</th><th>Notes</th></tr></thead><tbody>{Object.entries(item.metrics).map(([metric, value]) => { const scored = isScoredMetric(value); const display = metricDisplay(metric, scored ? value.score : value); return <tr key={metric}><td><strong>{definition(metric).label}</strong></td><td>{display.value}</td><td>{display.unit}</td><td><span className={`metric-rating ${display.tone}`}>{display.rating}</span></td><td>{scored ? (value.reason || '—') : '—'}</td></tr>; })}</tbody></table></div></article>)}</section>)}</div>
	</section>;
}

function MetricValue({ metric, value }: { metric: string; value: unknown }) {
	const display = metricDisplay(metric, value);
	return <span className='aggregate-metric-value'><strong>{display.value}</strong><small>{display.unit}</small><span className={`metric-rating ${display.tone}`}>{display.rating}</span></span>;
}

function isScoredMetric(value: unknown): value is ScoredMetric {
	return value !== null && typeof value === 'object' && 'score' in value;
}

function definition(metric: string): MetricDefinition {
	return METRICS[metric] ?? { label: metric.replaceAll('_', ' '), kind: 'number', unit: '—' };
}

function metricDisplay(metric: string, value: unknown) {
	const config = definition(metric);
	if (value == null || (typeof value === 'number' && !Number.isFinite(value))) return { value: '—', unit: config.unit, rating: 'Not available', tone: 'neutral' };
	if (config.kind === 'boolean') return { value: value === true ? 'Hit' : 'Miss', unit: '—', rating: value === true ? 'Efficient' : 'Uncached', tone: value === true ? 'excellent' : 'neutral' };
	if (typeof value !== 'number') return { value: String(value), unit: config.unit, rating: 'Informational', tone: 'neutral' };
	if (config.kind === 'quality') {
		const percentage = value * 100;
		const rating = percentage >= 90 ? 'Excellent' : percentage >= 75 ? 'Good' : percentage >= 50 ? 'Fair' : 'Poor';
		return { value: percentage.toFixed(1), unit: '%', rating, tone: rating.toLowerCase() };
	}
	if (config.kind === 'latency') {
		const rating = value <= 250 ? 'Excellent' : value <= 750 ? 'Good' : value <= 2000 ? 'Fair' : 'Poor';
		return { value: value < 10 ? value.toFixed(2) : value.toFixed(0), unit: 'ms', rating, tone: rating.toLowerCase() };
	}
	if (config.kind === 'tokens') {
		const rating = value <= 1000 ? 'Efficient' : value <= 2500 ? 'Moderate' : value <= 5000 ? 'High' : 'Very high';
		return { value: formatNumber(value), unit: 'tokens', rating, tone: value <= 1000 ? 'excellent' : value <= 2500 ? 'good' : value <= 5000 ? 'fair' : 'poor' };
	}
	if (config.kind === 'cost') {
		const rating = value <= .001 ? 'Low' : value <= .01 ? 'Moderate' : value <= .05 ? 'High' : 'Very high';
		return { value: value.toFixed(4), unit: 'USD', rating, tone: value <= .001 ? 'excellent' : value <= .01 ? 'good' : value <= .05 ? 'fair' : 'poor' };
	}
	return { value: Number.isInteger(value) ? formatNumber(value) : value.toFixed(3), unit: config.unit, rating: 'Informational', tone: 'neutral' };
}
