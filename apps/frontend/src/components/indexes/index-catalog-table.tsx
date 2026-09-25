import { Eye, Layers3 } from 'lucide-react';
import type { IndexBuild } from '@/components/indexes/index-types';
import { formatDateTime } from '@/lib/format';

function buildStatus(build: IndexBuild) {
	if (build.failed_jobs) return 'Failed';
	if (build.active_jobs) return 'Building';
	if (build.job_count && build.completed_jobs === build.job_count)
		return 'Ready';
	return 'Pending';
}

export function IndexCatalogTable({
	indexes,
	busy,
	onInspect,
}: {
	indexes: IndexBuild[];
	busy: boolean;
	onInspect: (indexId: string) => void;
}) {
	return (
		<section className='catalog-table-panel'>
			<header>
				<div>
					<h2>Vector indexes</h2>
					<p>{indexes.length} configured</p>
				</div>
			</header>
			<div className='catalog-table-wrap'>
				<table>
					<thead>
						<tr>
							<th>Name</th>
							<th>Embedding model</th>
							<th>Dimensions</th>
							<th>Chunking</th>
							<th>Jobs</th>
							<th>Status</th>
							<th>Created</th>
							<th aria-label='Actions' />
						</tr>
					</thead>
					<tbody>
						{indexes.map(index => {
							const status =
								buildStatus(
									index,
								);
							return (
								<tr
									key={
										index.id
									}>
									<td>
										<span className='catalog-primary'>
											<Layers3
												size={
													14
												}
											/>
											<strong>
												{
													index
														.configuration
														.name
												}
											</strong>
										</span>
									</td>
									<td>
										{
											index
												.configuration
												.embedding
												.model
										}
									</td>
									<td>
										{
											index
												.configuration
												.embedding
												.dimensions
										}
									</td>
									<td>
										Unstructured
										/{' '}
										{
											index
												.configuration
												.chunking
												.strategy
										}
									</td>
									<td>
										{
											index.completed_jobs
										}{' '}
										/{' '}
										{
											index.job_count
										}
									</td>
									<td>
										<span
											className={`catalog-state ${status.toLowerCase()}`}>
											{
												status
											}
										</span>
									</td>
									<td>
										{formatDateTime(
											index.created_at,
										)}
									</td>
									<td className='catalog-open'>
										<button
											onClick={() =>
												onInspect(
													index.id,
												)
											}
											disabled={
												busy
											}
											aria-label={`Inspect ${index.configuration.name}`}>
											<Eye
												size={
													14
												}
											/>
										</button>
									</td>
								</tr>
							);
						})}
						{!indexes.length && (
							<tr>
								<td
									colSpan={
										8
									}
									className='mock-empty'>
									No
									indexes
									configured
									yet.
								</td>
							</tr>
						)}
					</tbody>
				</table>
			</div>
		</section>
	);
}
