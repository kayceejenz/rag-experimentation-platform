'use client';

import { FormEvent, useState } from 'react';
import { ChevronRight, Eye, FlaskConical, Play, Plus, RefreshCw, Trash2, X } from 'lucide-react';
import { formatDateTime } from '@/lib/format';
import type { Experiment, Project } from '@/types/workspace';
import { RunResults } from './run-results';

type Dataset = { id: string; name: string; version: number; example_count: number };
type Index = { id: string; configuration: { name: string }; completed_jobs: number; job_count: number };
type Prompt = { name: string; purpose: string | null; prompt_type: string; version_id: string; version: number };
export type ExperimentCatalog = { experiments: Experiment[]; datasets: Dataset[]; indexes: Index[]; prompts: Prompt[]; generation_models: string[] };
type Variant = { id: string; name: string; index_configuration: { name: string }; system_prompt_name: string; system_prompt_version: number; rag_prompt_name: string; rag_prompt_version: number; evaluator_prompt_versions: Record<string, string>; retrieval_configuration: { top_k: number; min_score: number }; generation_configuration: { model: string; temperature: number; max_output_tokens: number }; configuration_hash: string };
type Run = { id: string; variant_id: string; variant_run_id: string; status: string; run_status: string; created_at: string; error_message: string | null };
export type ExperimentRunDetail = { run: { status: string; error_message: string | null }; variants: Array<{ id: string; name: string; status: string; aggregate_metrics: Record<string, number>; error_message: string | null }>; cases: Array<{ id: string; variant_run_id: string; position: number; question: string; generated_answer: string | null; metrics: Record<string, unknown> }> };
export type ExperimentDetail = { experiment: Experiment; variants: Variant[]; runs: Run[] };
type PanelTab = 'variants' | 'runs' | 'results';

const METRICS = [['context_precision', 'Context precision'], ['context_recall', 'Context recall'], ['faithfulness', 'Faithfulness'], ['answer_relevance', 'Answer relevance'], ['hallucination_detection', 'Hallucination detection'], ['retrieval_latency', 'Retrieval latency'], ['total_latency', 'Total latency'], ['token_count', 'Token count'], ['estimated_cost', 'Estimated cost']] as const;
const metricLabel = (id: string) => METRICS.find(item => item[0] === id)?.[1] ?? id.replaceAll('_', ' ');

export function ExperimentManager({ project, initialCatalog, initialDetail = null, initialRunDetail = null }: { project: Project; initialCatalog: ExperimentCatalog; initialDetail?: ExperimentDetail | null; initialRunDetail?: ExperimentRunDetail | null }) {
	const [catalog, setCatalog] = useState(initialCatalog);
	const [detail, setDetail] = useState<ExperimentDetail | null>(initialDetail);
	const [selectedVariant, setSelectedVariant] = useState<Variant | null>(null);
	const [selectedForComparison, setSelectedForComparison] = useState<string[]>([]);
	const [runDetail, setRunDetail] = useState<ExperimentRunDetail | null>(initialRunDetail);
	const [viewingRunId, setViewingRunId] = useState<string | null>(null);
	const [activeTab, setActiveTab] = useState<PanelTab>(initialRunDetail ? 'results' : 'variants');
	const [createOpen, setCreateOpen] = useState(false);
	const [variantOpen, setVariantOpen] = useState(false);
	const [busy, setBusy] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const canManage = project.role === 'owner' || project.permissions?.experiments?.manage;

	async function refresh() {
		const response = await fetch(`/api/projects/${project.id}/experiments`);
		const body = await response.json();
		if (!response.ok) throw new Error(responseError(body, 'Could not load experiments.'));
		setCatalog(body);
	}
	async function inspect(id: string, resetTab = true) {
		setBusy(true);
		try {
			const response = await fetch(`/api/projects/${project.id}/experiments/${id}`);
			const body = await response.json();
			if (!response.ok) throw new Error(responseError(body, 'Could not load experiment.'));
			setDetail(body);
			if (resetTab) setActiveTab('variants');
			setSelectedForComparison(current => current.filter(variantId => body.variants.some((variant: Variant) => variant.id === variantId)));
			setError(null);
		} catch (caught) { setError(message(caught)); } finally { setBusy(false); }
	}
	async function inspectRun(runId: string) {
		if (!detail) return null;
		const response = await fetch(`/api/projects/${project.id}/experiments/${detail.experiment.id}/runs/${runId}`);
		const body = await response.json();
		if (!response.ok) throw new Error(responseError(body, 'Could not load run.'));
		return body as ExperimentRunDetail;
	}
	async function openRun(runId: string) {
		setBusy(true); setViewingRunId(runId); setError(null);
		try {
			const result = await inspectRun(runId);
			if (!result) throw new Error('Run details are unavailable.');
			setRunDetail(result);
			setActiveTab('results');
			setError(null);
		} catch (caught) { setError(message(caught)); } finally { setBusy(false); setViewingRunId(null); }
	}
	async function runVariant(variant: Variant) {
		if (!detail) return;
		setBusy(true); setError(null);
		try {
			const response = await fetch(`/api/projects/${project.id}/experiments/${detail.experiment.id}/runs`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ variant_ids: [variant.id] }) });
			const body = await response.json();
			if (!response.ok) throw new Error(responseError(body, 'Could not start variant run.'));
			await inspect(detail.experiment.id, false);
			setRunDetail(await inspectRun(body.id));
			setActiveTab('runs');
		} catch (caught) { setError(message(caught)); } finally { setBusy(false); }
	}
	function latestCompletedRun(variantId: string) { return detail?.runs.find(run => run.variant_id === variantId && run.status === 'completed'); }
	function runVersion(runId: string) {
		const runIds = [...new Set(detail?.runs.map(run => run.id) ?? [])].reverse();
		return runIds.indexOf(runId) + 1;
	}
	function toggleComparison(variantId: string) { setSelectedForComparison(current => current.includes(variantId) ? current.filter(id => id !== variantId) : [...current, variantId]); }
	async function compareSelected() {
		if (!detail || selectedForComparison.length < 2) return;
		setBusy(true);
		try {
			const runs = selectedForComparison.map(latestCompletedRun).filter((run): run is Run => Boolean(run));
			const results = (await Promise.all(runs.map(run => inspectRun(run.id)))).filter((result): result is ExperimentRunDetail => Boolean(result));
			setRunDetail({ run: { status: 'comparison', error_message: null }, variants: results.flatMap(result => result.variants), cases: results.flatMap(result => result.cases) });
			setActiveTab('results');
			setError(null);
		} catch (caught) { setError(message(caught)); } finally { setBusy(false); }
	}
	async function create(event: FormEvent<HTMLFormElement>) {
		event.preventDefault(); setBusy(true); const form = new FormData(event.currentTarget);
		try {
			const response = await fetch(`/api/projects/${project.id}/experiments`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name: form.get('name'), description: form.get('description'), hypothesis: form.get('hypothesis'), benchmark_dataset_id: form.get('benchmark_dataset_id'), metrics: form.getAll('metrics'), primary_metric: form.get('primary_metric') }) });
			const body = await response.json(); if (!response.ok) throw new Error(responseError(body, 'Could not create experiment.'));
			await refresh(); setCreateOpen(false); await inspect(body.id);
		} catch (caught) { setError(message(caught)); } finally { setBusy(false); }
	}
	async function addVariant(event: FormEvent<HTMLFormElement>) {
		event.preventDefault(); if (!detail) return; setBusy(true); const form = new FormData(event.currentTarget);
		try {
			const response = await fetch(`/api/projects/${project.id}/experiments/${detail.experiment.id}/variants`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ name: form.get('name'), index_specification_id: form.get('index'), system_prompt_version_id: form.get('system'), rag_prompt_version_id: form.get('rag'), retrieval: { top_k: Number(form.get('top_k')), min_score: Number(form.get('min_score')) }, generation: { model: form.get('model'), temperature: Number(form.get('temperature')), max_output_tokens: Number(form.get('tokens')) } }) });
			const body = await response.json(); if (!response.ok) throw new Error(responseError(body, 'Could not add variant.'));
			await refresh(); setVariantOpen(false); await inspect(detail.experiment.id);
		} catch (caught) { setError(message(caught)); } finally { setBusy(false); }
	}
	async function deleteVariant(variant: Variant) {
		if (!detail || !window.confirm(`Delete “${variant.name}”? This cannot be undone.`)) return;
		setBusy(true);
		try {
			const response = await fetch(`/api/projects/${project.id}/experiments/${detail.experiment.id}/variants/${variant.id}`, { method: 'DELETE' });
			if (!response.ok) { const body = await response.json(); throw new Error(responseError(body, 'Could not delete variant.')); }
			await refresh(); await inspect(detail.experiment.id);
		} catch (caught) { setError(message(caught)); } finally { setBusy(false); }
	}

	return <div className='experiment-page'>
		<header className='product-page-header'><div><span className='eyebrow'>Development</span><h1>Experiments</h1><p>Run and compare immutable retrieval and generation variants.</p></div>{canManage && <button className='primary-action' onClick={() => setCreateOpen(true)}><Plus size={15} />New experiment</button>}</header>
		{error && !detail && <div className='workspace-error' role='alert'>{error}</div>}
		<section className='catalog-table-panel'><header><div><h2>Experiment registry</h2><p>{catalog.experiments.length} experiments</p></div></header><div className='catalog-table-wrap'><table><caption className='sr-only'>Experiments in this project</caption><thead><tr><th scope='col'>Experiment</th><th scope='col'>Benchmark</th><th scope='col'>Primary metric</th><th scope='col'>Variants</th><th scope='col'>Status</th><th scope='col'><span className='sr-only'>Actions</span></th></tr></thead><tbody>{catalog.experiments.map(experiment => <tr key={experiment.id} onClick={() => inspect(experiment.id)}><td><span className='catalog-primary'><FlaskConical size={14} /><strong>{experiment.name}</strong></span></td><td>{experiment.benchmark_name} · v{experiment.benchmark_version}</td><td>{metricLabel(experiment.primary_metric)}</td><td>{experiment.variant_count}</td><td><span className={`catalog-state ${experiment.status}`}>{experiment.status}</span></td><td><button type='button' className='catalog-row-open' aria-label={`Open experiment ${experiment.name}`} onClick={event => { event.stopPropagation(); void inspect(experiment.id); }}><ChevronRight size={14} /></button></td></tr>)}</tbody></table>{!catalog.experiments.length && <div className='mock-empty'>No experiments created yet.</div>}</div></section>
		{createOpen && <ExperimentForm catalog={catalog} busy={busy} submit={create} close={() => setCreateOpen(false)} />}
		{detail && <div className='index-detail-backdrop'><section className='experiment-detail-panel' role='dialog' aria-modal='true' aria-labelledby='experiment-detail-title'>
			<header><div><span className='eyebrow'>Experiment</span><h2 id='experiment-detail-title'>{detail.experiment.name}</h2><p>{detail.experiment.description || 'No description'}</p></div><button aria-label='Close experiment' onClick={() => { setRunDetail(null); setSelectedVariant(null); setDetail(null); }}><X size={18} /></button></header>
			<div className='experiment-summary'><p>{detail.experiment.hypothesis}</p><div><span>{detail.experiment.benchmark_name} · v{detail.experiment.benchmark_version}</span><span>{detail.experiment.benchmark_cases} cases</span><span>{metricLabel(detail.experiment.primary_metric)}</span></div></div>
			<nav className='experiment-panel-tabs' aria-label='Experiment sections' role='tablist'>{(['variants', 'runs', 'results'] as PanelTab[]).map(tab => <button key={tab} type='button' role='tab' aria-selected={activeTab === tab} className={activeTab === tab ? 'active' : ''} onClick={() => setActiveTab(tab)} disabled={tab === 'results' && !runDetail}>{tab === 'variants' ? `Variants (${detail.variants.length})` : tab === 'runs' ? `Runs (${detail.runs.length})` : 'Results'}</button>)}</nav>
			{error && <div className='experiment-panel-error' role='alert'><strong>Unable to complete action</strong><span>{error}</span><button onClick={() => setError(null)} aria-label='Dismiss error'><X size={14} /></button></div>}
			{activeTab === 'variants' && <section className='experiment-table-section variant-run-section'><header><div><h3>Variants</h3><p>Immutable configurations you can run independently.</p></div>{canManage && <button className='primary-action' onClick={() => setVariantOpen(true)}><Plus size={14} />Add variant</button>}</header><div className='experiment-data-table'><table><thead><tr><th>Variant</th><th>Index</th><th>Model</th><th>Top K</th><th /></tr></thead><tbody>{detail.variants.map(variant => { const available = catalog.generation_models.includes(variant.generation_configuration.model); const hasRuns = detail.runs.some(run => run.variant_id === variant.id); return <tr key={variant.id}><td><strong>{variant.name}</strong></td><td>{variant.index_configuration.name}</td><td>{variant.generation_configuration.model}</td><td>{variant.retrieval_configuration.top_k}</td><td><div className='row-actions'><button title='Inspect configuration' aria-label={`Inspect ${variant.name}`} onClick={() => setSelectedVariant(variant)}><Eye size={14} /></button>{canManage && <button className='secondary-action variant-run-button' disabled={busy || !available} onClick={() => runVariant(variant)}><Play size={13} />Run</button>}{canManage && <button className='variant-delete' disabled={busy || hasRuns} title={hasRuns ? 'Variants with runs are retained for lineage' : 'Delete'} aria-label={`Delete ${variant.name}`} onClick={() => deleteVariant(variant)}><Trash2 size={14} /></button>}</div></td></tr>; })}</tbody></table></div></section>}
			{activeTab === 'runs' && <section className='experiment-table-section variant-run-section'><header><div><h3>Run history</h3><p>One row for every variant execution.</p></div><div className='experiment-actions'><button className='secondary-action' disabled={busy || selectedForComparison.length < 2} onClick={compareSelected}>Compare selected ({selectedForComparison.length})</button><button className='secondary-action' disabled={busy} onClick={() => inspect(detail.experiment.id, false)}><RefreshCw size={13} />Refresh</button></div></header><div className='experiment-data-table experiment-runs-table'><table><thead><tr><th aria-label='Select for comparison' /><th>Run</th><th>Variant</th><th>Started</th><th>Status</th><th /></tr></thead><tbody>{detail.runs.map(run => { const variant = detail.variants.find(item => item.id === run.variant_id); const latest = latestCompletedRun(run.variant_id); const selectable = latest?.variant_run_id === run.variant_run_id; return <tr key={run.variant_run_id}><td>{selectable ? <input type='checkbox' aria-label={`Compare ${variant?.name || 'variant'}`} checked={selectedForComparison.includes(run.variant_id)} onChange={() => toggleComparison(run.variant_id)} /> : <span className='run-not-selectable'>—</span>}</td><td><span className='run-version'>v{runVersion(run.id)}</span></td><td><strong>{variant?.name || 'Unknown variant'}</strong></td><td>{formatDateTime(run.created_at)}</td><td><span className={`catalog-state ${run.status}`}>{run.status}</span></td><td><button className='table-inspect' title='View run' aria-label={`View ${variant?.name || 'variant'} run`} disabled={busy} onClick={() => openRun(run.id)}><Eye size={14} />{viewingRunId === run.id ? 'Loading…' : 'View'}</button></td></tr>; })}</tbody></table>{!detail.runs.length && <div className='mock-empty'>No runs yet.</div>}</div></section>}
			{activeTab === 'results' && (runDetail ? <RunResults detail={runDetail} metrics={detail.experiment.metrics} primaryMetric={detail.experiment.primary_metric} expectedCases={detail.experiment.benchmark_cases} /> : <div className='mock-empty experiment-results-empty'>Select View on a run to inspect its results.</div>)}
			{selectedVariant && <VariantInspector variant={selectedVariant} available={catalog.generation_models.includes(selectedVariant.generation_configuration.model)} close={() => setSelectedVariant(null)} />}
		</section></div>}
		{variantOpen && <VariantForm catalog={catalog} busy={busy} submit={addVariant} close={() => setVariantOpen(false)} />}
	</div>;
}

function ExperimentForm({ catalog, busy, submit, close }: { catalog: ExperimentCatalog; busy: boolean; submit: (event: FormEvent<HTMLFormElement>) => void; close: () => void }) {
	const [selected, setSelected] = useState<string[]>(['context_precision', 'context_recall', 'faithfulness', 'answer_relevance', 'retrieval_latency']);
	return <Modal title='Create experiment' busy={busy} action='Create experiment' submit={submit} close={close}><label>Name<input name='name' required /></label><label>Description<textarea name='description' rows={2} /></label><label>Hypothesis<textarea name='hypothesis' rows={3} required placeholder='Changing X will improve Y because…' /></label><label>Benchmark version<select name='benchmark_dataset_id' required defaultValue=''><option value='' disabled>Select dataset</option>{catalog.datasets.map(dataset => <option key={dataset.id} value={dataset.id}>{dataset.name} · v{dataset.version} · {dataset.example_count} cases</option>)}</select></label><fieldset><legend>Metrics</legend><div className='experiment-metrics'>{METRICS.map(([id, name]) => <label key={id}><input type='checkbox' name='metrics' value={id} checked={selected.includes(id)} onChange={event => setSelected(current => event.target.checked ? [...current, id] : current.filter(value => value !== id))} />{name}</label>)}</div></fieldset><label>Primary metric<select name='primary_metric'>{selected.map(metric => <option key={metric} value={metric}>{metricLabel(metric)}</option>)}</select></label></Modal>;
}
function VariantInspector({ variant, available, close }: { variant: Variant; available: boolean; close: () => void }) {
	return <aside className='variant-inspector'><header><div><span className='eyebrow'>Variant configuration</span><h4>{variant.name}</h4></div><button aria-label='Close variant details' onClick={close}><X size={15} /></button></header><table><tbody><tr><th>Index</th><td>{variant.index_configuration.name}</td></tr><tr><th>Model</th><td>{variant.generation_configuration.model}{!available && <span className='variant-warning'>Unavailable</span>}</td></tr><tr><th>Retrieval</th><td>Top {variant.retrieval_configuration.top_k} · minimum score {variant.retrieval_configuration.min_score}</td></tr><tr><th>System prompt</th><td>{variant.system_prompt_name} · v{variant.system_prompt_version}</td></tr><tr><th>RAG prompt</th><td>{variant.rag_prompt_name} · v{variant.rag_prompt_version}</td></tr><tr><th>Generation</th><td>Temperature {variant.generation_configuration.temperature} · {variant.generation_configuration.max_output_tokens} max tokens</td></tr><tr><th>Configuration ID</th><td><code>{variant.configuration_hash.slice(0, 16)}</code></td></tr></tbody></table></aside>;
}
function VariantForm({ catalog, busy, submit, close }: { catalog: ExperimentCatalog; busy: boolean; submit: (event: FormEvent<HTMLFormElement>) => void; close: () => void }) {
	const systems = catalog.prompts.filter(prompt => prompt.prompt_type === 'system'); const rag = catalog.prompts.filter(prompt => prompt.prompt_type === 'rag_answer');
	return <Modal title='Add immutable variant' busy={busy} action='Add variant' submit={submit} close={close}><label>Name<input name='name' required placeholder='Baseline' /></label><label>Index<select name='index' required>{catalog.indexes.map(index => <option key={index.id} value={index.id}>{index.configuration.name}</option>)}</select></label><div className='experiment-form-grid'><label>System prompt<select name='system'>{systems.map(prompt => <option key={prompt.version_id} value={prompt.version_id}>{prompt.name} · v{prompt.version}</option>)}</select></label><label>RAG prompt<select name='rag'>{rag.map(prompt => <option key={prompt.version_id} value={prompt.version_id}>{prompt.name} · v{prompt.version}</option>)}</select></label><label>Top K<input name='top_k' type='number' min={1} max={100} defaultValue={5} /></label><label>Min score<input name='min_score' type='number' min={0} max={1} step='.01' defaultValue={0} /></label><label>Gemini model<select name='model' required>{catalog.generation_models.map(model => <option key={model} value={model}>{model}</option>)}</select></label><label>Temperature<input name='temperature' type='number' min={0} max={2} step='.1' defaultValue={0} /></label><label>Max tokens<input name='tokens' type='number' min={64} max={65536} defaultValue={2048} /></label></div></Modal>;
}
function Modal({ title, busy, action, submit, close, children }: { title: string; busy: boolean; action: string; submit: (event: FormEvent<HTMLFormElement>) => void; close: () => void; children: React.ReactNode }) {
	return <div className='modal-backdrop experiment-modal'><form className='workspace-modal experiment-form' onSubmit={submit}><div className='modal-title'><div><h2>{title}</h2><p className='modal-copy'>All references are pinned to exact versions.</p></div><button type='button' className='icon-action' onClick={close}><X size={18} /></button></div>{children}<div className='project-form-actions'><button type='button' className='secondary-action' onClick={close}>Cancel</button><button className='primary-action' disabled={busy}>{busy ? 'Saving…' : action}</button></div></form></div>;
}
function message(error: unknown) { return error instanceof Error ? error.message : 'Something went wrong.'; }
function responseError(body: unknown, fallback: string) {
	if (!body || typeof body !== 'object' || !('error' in body)) return fallback;
	const error = body.error;
	if (typeof error === 'string') return error;
	if (error && typeof error === 'object' && 'message' in error && typeof error.message === 'string') return error.message;
	return fallback;
}
