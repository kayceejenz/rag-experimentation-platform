import type { FormEvent } from 'react';
import { X } from 'lucide-react';
import type { IndexCatalog } from '@/components/indexes/index-types';
import type { KnowledgeBase, KnowledgeFolder, Source } from '@/types/workspace';

function folderPaths(folders: KnowledgeFolder[]) {
	const byId = new Map(folders.map(folder => [folder.id, folder]));
	const label = (folder: KnowledgeFolder) => {
		const names = [folder.name];
		let parentId = folder.parent_id;
		while (parentId) {
			const parent = byId.get(parentId);
			if (!parent) break;
			names.unshift(parent.name);
			parentId = parent.parent_id;
		}
		return names.join(' / ');
	};
	return {
		label,
		ordered: [...folders].sort((a, b) =>
			label(a).localeCompare(label(b)),
		),
	};
}

export function CreateIndexDialog({
	knowledgeBase,
	folders,
	sources,
	catalog,
	selectedFolderIds,
	busy,
	onSelectedFolderIdsChange,
	onClose,
	onSubmit,
}: {
	knowledgeBase: KnowledgeBase;
	folders: KnowledgeFolder[];
	sources: Source[];
	catalog: IndexCatalog;
	selectedFolderIds: string[];
	busy: boolean;
	onSelectedFolderIdsChange: (ids: string[]) => void;
	onClose: () => void;
	onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
	const { label: folderLabel, ordered: orderedFolders } =
		folderPaths(folders);
	const toggleFolder = (folderId: string) => {
		onSelectedFolderIdsChange(
			selectedFolderIds.includes(folderId)
				? selectedFolderIds.filter(
						id => id !== folderId,
					)
				: [...selectedFolderIds, folderId],
		);
	};

	return (
		<div
			className='modal-backdrop'
			role='dialog'
			aria-modal='true'
			aria-labelledby='create-index-title'>
			<form
				className='workspace-modal index-create-modal'
				onSubmit={onSubmit}>
				<div className='modal-title'>
					<div>
						<h2 id='create-index-title'>
							Create index
						</h2>
						<p>
							The configuration is
							saved as an immutable
							specification.
						</p>
					</div>
					<button
						type='button'
						className='icon-action'
						onClick={onClose}
						aria-label='Close'>
						<X size={18} />
					</button>
				</div>
				<div className='project-form-fields'>
					<label>
						Index name
						<input
							name='name'
							required
							minLength={2}
							maxLength={160}
							autoFocus
						/>
					</label>
					<label>
						Knowledge Base
						<input
							value={
								knowledgeBase.name
							}
							disabled
						/>
					</label>
					<fieldset className='index-folder-selector'>
						<legend>
							Knowledge folders
						</legend>
						<p>
							Select Root for every
							file, or choose the
							folders this index
							should contain.
						</p>
						<label className='index-folder-option root'>
							<input
								type='checkbox'
								checked={
									!selectedFolderIds.length
								}
								onChange={() =>
									onSelectedFolderIdsChange(
										[],
									)
								}
							/>
							<span>
								<strong>
									Root
								</strong>
								<small>
									{
										sources.length
									}{' '}
									files
									across
									the
									Knowledge
									Base
								</small>
							</span>
						</label>
						<div className='index-folder-options'>
							{orderedFolders.map(
								folder => {
									const fileCount =
										sources.filter(
											source =>
												source.folder_id ===
												folder.id,
										).length;
									return (
										<label
											className='index-folder-option'
											key={
												folder.id
											}>
											<input
												type='checkbox'
												checked={selectedFolderIds.includes(
													folder.id,
												)}
												onChange={() =>
													toggleFolder(
														folder.id,
													)
												}
											/>
											<span>
												<strong>
													{folderLabel(
														folder,
													)}
												</strong>
												<small>
													{
														fileCount
													}{' '}
													direct
													file
													{fileCount ===
													1
														? ''
														: 's'}{' '}
													·
													includes
													subfolders
												</small>
											</span>
										</label>
									);
								},
							)}
							{!orderedFolders.length && (
								<p className='artifact-preview-empty'>
									No
									folders
									yet.
									Root
									will
									index
									the full
									Knowledge
									Base.
								</p>
							)}
						</div>
					</fieldset>
					<label>
						Embedding model
						<select
							name='embedding_model_id'
							required>
							{catalog.embedding_models.map(
								model => (
									<option
										key={
											model.id
										}
										value={
											model.id
										}>
										{
											model.model_name
										}{' '}
										·{' '}
										{
											model.dimensions
										}{' '}
										dimensions
										·{' '}
										{
											model.distance_metric
										}
									</option>
								),
							)}
						</select>
					</label>
					<label>
						Chunking strategy
						<select
							name='chunking_strategy'
							required
							defaultValue='by_title'>
							{catalog.chunking_strategies.map(
								strategy => (
									<option
										key={
											strategy.id
										}
										value={
											strategy.id
										}>
										{
											strategy.provider
										}{' '}
										/{' '}
										{
											strategy.name
										}
									</option>
								),
							)}
						</select>
					</label>
				</div>
				<div className='index-spec-summary'>
					<strong>Build flow</strong>
					<span>
						{selectedFolderIds.length
							? `${selectedFolderIds.length} selected folder${selectedFolderIds.length === 1 ? '' : 's'}`
							: 'Knowledge Base Root'}{' '}
						→ Unstructured chunking →
						Embeddings → Vector index
					</span>
				</div>
				<div className='project-form-actions'>
					<button
						type='button'
						className='secondary-action'
						onClick={onClose}>
						Cancel
					</button>
					<button
						className='primary-action'
						disabled={busy}>
						{busy
							? 'Starting…'
							: 'Create and build'}
					</button>
				</div>
			</form>
		</div>
	);
}
