import type { ArtifactPreview } from '@/components/indexes/index-types';

function shortId(value: unknown) {
	const id = String(value ?? '—');
	return id.length > 14 ? `${id.slice(0, 8)}…${id.slice(-4)}` : id;
}

function vectorPreview(value: unknown) {
	const vector = String(value ?? '[]');
	const values = vector.slice(1, -1).split(',');
	return values.length > 8
		? `[${values.slice(0, 8).join(', ')}, …]`
		: vector;
}

function ElementRows({ records }: { records: ArtifactPreview['records'] }) {
	return records.map((record, position) => (
		<tr key={String(record.element_id ?? position)}>
			<td>
				{Number(record.sequence_number ?? position) + 1}
			</td>
			<td>
				<span className='artifact-type-value'>
					{String(record.category ?? 'Text')}
				</span>
			</td>
			<td className='artifact-content-cell'>
				{String(record.content ?? '—')}
			</td>
			<td>{String(record.page_number ?? '—')}</td>
			<td>
				<code>{shortId(record.element_id)}</code>
			</td>
		</tr>
	));
}

function ChunkRows({ records }: { records: ArtifactPreview['records'] }) {
	return records.map((record, position) => (
		<tr key={String(record.id ?? position)}>
			<td>{Number(record.position ?? position) + 1}</td>
			<td className='artifact-content-cell'>
				{String(record.content ?? '—')}
			</td>
			<td>
				{record.page_from == null
					? '—'
					: record.page_from === record.page_to
						? String(record.page_from)
						: `${String(record.page_from)}–${String(record.page_to)}`}
			</td>
			<td>
				<code>{shortId(record.id)}</code>
			</td>
		</tr>
	));
}

function EmbeddingRows({ records }: { records: ArtifactPreview['records'] }) {
	return records.map((record, position) => (
		<tr key={String(record.chunk_id ?? position)}>
			<td>{position + 1}</td>
			<td>
				<span className='artifact-model-value'>
					{String(record.provider ?? '—')} /{' '}
					{String(record.model_name ?? '—')}
				</span>
			</td>
			<td>{String(record.dimensions ?? '—')}</td>
			<td className='artifact-vector-cell'>
				<code title={String(record.embedding ?? '')}>
					{vectorPreview(record.embedding)}
				</code>
			</td>
			<td>
				<code>{shortId(record.chunk_id)}</code>
			</td>
		</tr>
	));
}

export function IndexArtifactPreview({
	preview,
}: {
	preview: ArtifactPreview;
}) {
	if (!preview.records.length) {
		return (
			<p className='artifact-preview-empty'>
				This output contains no records.
			</p>
		);
	}

	if (preview.artifact.kind === 'element_dataset') {
		return (
			<table>
				<thead>
					<tr>
						<th>#</th>
						<th>Category</th>
						<th>Content</th>
						<th>Page</th>
						<th>Element ID</th>
					</tr>
				</thead>
				<tbody>
					<ElementRows
						records={preview.records}
					/>
				</tbody>
			</table>
		);
	}

	if (preview.artifact.kind === 'chunk_dataset') {
		return (
			<table>
				<thead>
					<tr>
						<th>#</th>
						<th>Content</th>
						<th>Pages</th>
						<th>Chunk ID</th>
					</tr>
				</thead>
				<tbody>
					<ChunkRows records={preview.records} />
				</tbody>
			</table>
		);
	}

	return (
		<table>
			<thead>
				<tr>
					<th>#</th>
					<th>Model</th>
					<th>Dimensions</th>
					<th>Vector preview</th>
					<th>Chunk ID</th>
				</tr>
			</thead>
			<tbody>
				<EmbeddingRows records={preview.records} />
			</tbody>
		</table>
	);
}
