'use client';

import { useState } from 'react';
import { formatNumber } from '@/lib/format';

type ScoredMetric = { score: number | null; reason?: string };
type VariantResult = { id: string; name: string; status: string; aggregate_metrics: Record<string, number>; error_message: string | null };
type CaseResult = { id: string; variant_run_id: string; position: number; question: string; generated_answer: string | null; metrics: Record<string, unknown>; error_message?: string | null };
type Props = {
	detail: { run: { status: string; error_message: string | null }; variants: VariantResult[]; cases: CaseResult[] };
	metrics: string[];
	primaryMetric: string;
	expectedCases: number;
};

type MetricKind = 'quality' | 'latency' | 'tokens' | 'cost' | 'boolean' | 'number';
type MetricDefinition = { label: string; kind: MetricKind; unit: string };

const METRICS: Record<string, MetricDefinition> = {
	context_precision: { label: 'Context precision', kind: 'quality', unit: '%' },
	context_recall: { label: 'Context recall', kind: 'quality', unit: '%' },
	faithfulness: { label: 'Faithfulness', kind: 'quality', unit: '%' },
	answer_relevance: { label: 'Answer relevance', kind: 'quality', unit: '%' },
	hallucination_detection: { label: 'Groundedness', kind: 'quality', unit: '%' },
	embedding_latency: { label: 'Query embedding', kind: 'latency', unit: 'ms' },
	vector_search_latency: { label: 'Vector search', kind: 'latency', unit: 'ms' },
	retrieval_latency: { label: 'Retrieval latency', kind: 'latency', unit: 'ms' },
	context_assembly_latency: { label: 'Context assembly', kind: 'latency', unit: 'ms' },
	generation_latency: { label: 'Generation latency', kind: 'latency', unit: 'ms' },
	evaluation_latency: { label: 'Evaluation latency', kind: 'latency', unit: 'ms' },
	provider_queue_latency: { label: 'Provider wait', kind: 'latency', unit: 'ms' },
	total_latency: { label: 'Total latency', kind: 'latency', unit: 'ms' },
	token_count: { label: 'Token usage', kind: 'tokens', unit: 'tokens' },
	estimated_cost: { label: 'Estimated cost', kind: 'cost', unit: 'USD' },
	embedding_cache_hit: { label: 'Embedding cache', kind: 'boolean', unit: '—' },
};

export function RunResults({ detail, metrics, primaryMetric, expectedCases }: Props) {
	const [chosenVariantId, setChosenVariantId] = useState(detail.variants[0]?.id ?? '');
	const selectedVariant = detail.variants.find(item => item.id === chosenVariantId) ?? detail.variants[0];
	const variantCases = detail.cases.filter(item => item.variant_run_id === selectedVariant?.id);
	const [chosenCaseId, setChosenCaseId] = useState(variantCases[0]?.id ?? '');
	const selectedCase = variantCases.find(item => item.id === chosenCaseId) ?? variantCases[0];
	const expectedTotal = expectedCases * Math.max(detail.variants.length, 1);
	const failedCount = Math.max(expectedTotal - detail.cases.length, 0);
	const isComparison = detail.run.status === 'comparison' || detail.variants.length > 1;
	const errors = [...new Set([detail.run.error_message, ...detail.variants.map(variant => variant.error_message)].filter((value): value is string => Boolean(value)))];

	return <section className='experiment-results' aria-label='Experiment run results'>
		<header className='results-header'><div><h3>{isComparison ? 'Variant comparison' : `${detail.variants[0]?.name ?? 'Run'} results`}</h3><p>{isComparison ? 'The same benchmark measured across selected variants.' : 'Benchmark outcome and individual case evidence.'}</p></div>{!isComparison && <span className={`catalog-state ${detail.run.status}`}>{detail.run.status}</span>}</header>
		<div className='run-outcome-grid'>
			<Summary label='Variants' value={String(detail.variants.length)} />
			<Summary label='Cases completed' value={`${detail.cases.length} / ${expectedTotal}`} tone={failedCount ? 'warning' : 'positive'} />
			<Summary label='Cases incomplete' value={String(failedCount)} tone={failedCount ? 'danger' : 'neutral'} />
			<Summary label='Primary metric' value={definition(primaryMetric).label} />
		</div>
		{errors.length > 0 && <details className='run-error-summary'><summary>{errors.length} execution {errors.length === 1 ? 'error' : 'errors'}</summary><ul>{errors.map((error, index) => <li key={`${index}-${error}`}>{cleanProviderError(error)}</li>)}</ul></details>}

		<section className='results-section'>
			<header><div><h4>{isComparison ? 'Metric comparison' : 'Metric summary'}</h4><p>{isComparison ? 'Best values are highlighted. Quality is higher-is-better; latency, tokens, and cost are lower-is-better.' : 'Aggregate scores across completed cases.'}</p></div></header>
			<div className='experiment-comparison'><table><caption className='sr-only'>Aggregate metric results by experiment variant</caption><thead><tr><th scope='col'>Metric</th>{detail.variants.map(variant => <th scope='col' key={variant.id}>{variant.name}<small>{variant.status}</small></th>)}</tr></thead><tbody>{metrics.map(metric => {
				const best = bestValue(metric, detail.variants);
				return <tr key={metric}><th scope='row'>{definition(metric).label}{metric === primaryMetric && <span className='primary-metric-label'>Primary</span>}</th>{detail.variants.map(variant => {
					const value = variant.aggregate_metrics?.[metric];
					return <td key={variant.id} className={isComparison && value === best ? 'metric-winner' : ''}><MetricValue metric={metric} value={value} />{isComparison && value === best && value != null && <small className='best-label'>Best</small>}</td>;
				})}</tr>;
			})}</tbody></table></div>
		</section>

		<section className='results-section case-explorer'>
			<header><div><h4>Benchmark cases</h4><p>Select a case to inspect its answer, scores, and evaluator notes.</p></div></header>
			{detail.variants.length > 1 && <div className='result-variant-tabs' role='tablist' aria-label='Result variants'>{detail.variants.map(variant => <button type='button' role='tab' aria-selected={variant.id === selectedVariant?.id} key={variant.id} className={variant.id === selectedVariant?.id ? 'active' : ''} onClick={() => { setChosenVariantId(variant.id); setChosenCaseId(''); }}>{variant.name}<span>{detail.cases.filter(item => item.variant_run_id === variant.id).length}/{expectedCases}</span></button>)}</div>}
			<div className='case-browser'>
				<div className='case-list-table'><table><caption className='sr-only'>Benchmark cases for {selectedVariant?.name}</caption><thead><tr><th scope='col'>Case</th><th scope='col'>Question</th><th scope='col'>{definition(primaryMetric).label}</th><th scope='col'>Total time</th><th scope='col'><span className='sr-only'>Actions</span></th></tr></thead><tbody>{variantCases.map(item => <tr key={item.id} className={item.id === selectedCase?.id ? 'selected' : ''}><td>{item.position + 1}</td><td>{item.question}</td><td><MetricValue metric={primaryMetric} value={scoreValue(item.metrics[primaryMetric])} /></td><td><MetricValue metric='total_latency' value={item.metrics.total_latency} /></td><td><button type='button' aria-pressed={item.id === selectedCase?.id} aria-label={`Inspect benchmark case ${item.position + 1}`} onClick={() => setChosenCaseId(item.id)}>Inspect</button></td></tr>)}</tbody></table>{variantCases.length === 0 && <div className='mock-empty'>No completed cases were recorded for this variant.</div>}</div>
				{selectedCase && <CaseInspection result={selectedCase} />}
			</div>
		</section>
	</section>;
}

function Summary({ label, value, tone = 'neutral' }: { label: string; value: string; tone?: string }) {
	return <div className={`run-outcome ${tone}`}><span>{label}</span><strong>{value}</strong></div>;
}

function CaseInspection({ result }: { result: CaseResult }) {
	return <article className='case-inspection'>
		<header><span>Case {result.position + 1}</span><h5>{result.question}</h5></header>
		<section><h6>Generated answer</h6><p>{result.generated_answer || 'No answer was generated.'}</p></section>
		<div className='case-metrics-table'><table><caption className='sr-only'>Metrics for benchmark case {result.position + 1}</caption><thead><tr><th scope='col'>Metric</th><th scope='col'>Result</th><th scope='col'>Rating</th><th scope='col'>Evaluator notes</th></tr></thead><tbody>{Object.entries(result.metrics).map(([metric, value]) => {
			const scored = isScoredMetric(value);
			const display = metricDisplay(metric, scored ? value.score : value);
			return <tr key={metric}><th scope='row'>{definition(metric).label}</th><td>{display.value} {display.unit !== '—' ? display.unit : ''}</td><td><span className={`metric-rating ${display.tone}`}>{display.rating}</span></td><td>{scored ? (value.reason || '—') : '—'}</td></tr>;
		})}</tbody></table></div>
	</article>;
}

function MetricValue({ metric, value }: { metric: string; value: unknown }) {
	const display = metricDisplay(metric, value);
	return <span className='aggregate-metric-value'><strong>{display.value}</strong><small>{display.unit}</small><span className={`metric-rating ${display.tone}`}>{display.rating}</span></span>;
}

function bestValue(metric: string, variants: VariantResult[]) {
	const values = variants.map(variant => variant.aggregate_metrics?.[metric]).filter((value): value is number => typeof value === 'number' && Number.isFinite(value));
	if (!values.length) return undefined;
	return ['latency', 'tokens', 'cost'].includes(definition(metric).kind) ? Math.min(...values) : Math.max(...values);
}

function scoreValue(value: unknown) { return isScoredMetric(value) ? value.score : value; }
function isScoredMetric(value: unknown): value is ScoredMetric { return value !== null && typeof value === 'object' && 'score' in value; }
function definition(metric: string): MetricDefinition { return METRICS[metric] ?? { label: metric.replaceAll('_', ' '), kind: 'number', unit: '—' }; }
function cleanProviderError(error: string) {
	const withoutHelpLinks = error.replace(/For more information check:\s*https?:\/\/\S+/g, '');
	return [...new Set(withoutHelpLinks.split(';').map(part => part.trim()).filter(Boolean))].join('; ');
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
