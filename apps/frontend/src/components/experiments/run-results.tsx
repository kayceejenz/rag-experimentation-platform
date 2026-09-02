type MetricValue = number | { score: number | null; reason: string };
type Props = {
	detail: {
		run: { status: string; error_message: string | null };
		variants: Array<{
			id: string;
			name: string;
			status: string;
			aggregate_metrics: Record<string, number>;
			error_message: string | null;
		}>;
		cases: Array<{
			id: string;
			variant_run_id: string;
			position: number;
			question: string;
			generated_answer: string | null;
			metrics: Record<string, MetricValue>;
		}>;
	};
	metrics: string[];
};
const label = (value: string) => value.replaceAll('_', ' ');
export function RunResults({ detail, metrics }: Props) {
	return <section className='experiment-results'>
		<header><div><h3>Run results</h3><p>Variant comparison and case-level outputs.</p></div><span className={`catalog-state ${detail.run.status}`}>{detail.run.status}</span></header>
		{detail.run.error_message && <div className='workspace-error'>{detail.run.error_message}</div>}
		<div className='experiment-comparison'><table><thead><tr><th>Variant</th>{metrics.map(metric=><th key={metric}>{label(metric)}</th>)}</tr></thead><tbody>{detail.variants.map(variant=><tr key={variant.id}><td><strong>{variant.name}</strong><small>{variant.status}</small></td>{metrics.map(metric=><td key={metric}>{format(variant.aggregate_metrics?.[metric])}</td>)}</tr>)}</tbody></table></div>
		<div className='experiment-case-results'>{detail.variants.map(variant=><section key={variant.id}><h4>{variant.name}</h4>{detail.cases.filter(item=>item.variant_run_id===variant.id).map(item=><article key={item.id}><header><strong>Case {item.position+1}</strong><span>{item.question}</span></header><p>{item.generated_answer||'No answer generated.'}</p><div className='case-metrics-table'><table><thead><tr><th>Metric</th><th>Score</th><th>Notes</th></tr></thead><tbody>{Object.entries(item.metrics).map(([metric,value])=><tr key={metric}><td>{label(metric)}</td><td><strong>{format(typeof value==='object'?value.score:value)}</strong></td><td>{typeof value==='object'?(value.reason||'—'):'—'}</td></tr>)}</tbody></table></div></article>)}</section>)}</div>
	</section>;
}
function format(value: number | null | undefined) {
	if (value == null) return '—';
	return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(3);
}
