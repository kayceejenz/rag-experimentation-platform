'use client';

import { Dispatch, FormEvent, ChangeEvent, SetStateAction } from 'react';
import {
	LoaderCircle,
	Paperclip,
	ScanEye,
	Trash,
	Upload,
	X,
	FileText,
} from 'lucide-react';
import type { Source } from '@/types/workspace';
import { formatBytes } from '@/lib/format';

const activeStatuses = new Set(['uploaded', 'queued', 'processing']);

export function SourcesPanel({
	sources,
	selectedUploadFiles,
	uploading,
	onChooseFiles,
	onRemoveFile,
	onClearSelected,
	onUpload,
	onInspect,
	setSourceToDelete,
}: {
	sources: Source[];
	selectedUploadFiles: File[];
	uploading: boolean;
	onChooseFiles: (event: ChangeEvent<HTMLInputElement>) => void;
	onRemoveFile: (index: number) => void;
	onClearSelected: () => void;
	onUpload: (event: FormEvent<HTMLFormElement>) => void;
	onInspect: (source: Source) => void;
	setSourceToDelete: Dispatch<SetStateAction<Source | null>>;
}) {
	const hasFiles = selectedUploadFiles.length > 0;
	const canAddMore = selectedUploadFiles.length < 5;

	return (
		<aside className='sources-drawer-content'>
			<div className='sources-heading'>
				<div className='sources-title'>
					<h2>Knowledge Base</h2>
				</div>
				<span className='sources-count-badge'>
					{sources.length}
				</span>
			</div>
			<form className='source-upload' onSubmit={onUpload}>
				<input
					id='source-file'
					name='file'
					type='file'
					multiple
					accept='.pdf,.doc,.docx,.txt,.csv,.md,.json,.xlsx,.xls'
					onChange={onChooseFiles}
					style={{
						position: 'absolute',
						width: 1,
						height: 1,
						overflow: 'hidden',
						opacity: 0,
					}}
				/>
				{hasFiles && (
					<div className='selected-files-list'>
						{selectedUploadFiles.map(
							(file, i) => (
								<div
									key={`${file.name}-${i}`}
									className='selected-file-row'>
									<FileText
										size={
											14
										}
										className='file-row-icon'
									/>
									<span className='file-row-name'>
										{
											file.name
										}
									</span>
									<span className='file-row-size'>
										{formatBytes(
											file.size,
										)}
									</span>
									<button
										type='button'
										className='file-row-remove'
										onClick={() =>
											onRemoveFile(
												i,
											)
										}
										aria-label={`Remove ${file.name}`}>
										<X
											size={
												13
											}
										/>
									</button>
								</div>
							),
						)}
					</div>
				)}
				{canAddMore && (
					<div className='source-file-picker'>
						<label
							className='file-browse-label'
							htmlFor='source-file'>
							<Upload size={18} />
							<span>
								{hasFiles
									? `Add more (${selectedUploadFiles.length}/5)`
									: 'Browse files (max 5)'}
							</span>
						</label>
					</div>
				)}
				{hasFiles && (
					<div className='upload-actions-row'>
						<button
							type='button'
							className='secondary-action'
							onClick={
								onClearSelected
							}>
							Clear all
						</button>
						<button
							className='primary-action'
							disabled={uploading}>
							{uploading ? (
								<LoaderCircle
									className='spin'
									size={
										15
									}
								/>
							) : (
								<Paperclip
									size={
										15
									}
								/>
							)}{' '}
							{uploading
								? 'Uploading…'
								: `Upload ${selectedUploadFiles.length} file${selectedUploadFiles.length > 1 ? 's' : ''}`}
						</button>
					</div>
				)}
			</form>
			<div className='source-list'>
				{sources.map(source => (
					<article
						className='source-item'
						key={source.id}>
						<div className='source-info'>
							<div className='source-name'>
								{
									source.filename
								}
							</div>
							<div className='source-meta'>
								<span className='source-version'>
									Version{' '}
									{
										source.version
									}
								</span>
								<span className='source-meta-dot' />
								{activeStatuses.has(
									source.status,
								) ? (
									<span className='source-status-active'>
										<LoaderCircle
											size={
												11
											}
											className='spin'
										/>{' '}
										Processing
									</span>
								) : source.status ===
								  'failed' ? (
									<span className='source-status-error'>
										Failed
									</span>
								) : source.status ===
								  'ready' ? (
									<span className='source-status-ready'>
										Ready
									</span>
								) : (
									<span>
										{
											source.status
										}
									</span>
								)}
							</div>
						</div>
						<div className='source-actions'>
							{source.status ===
								'ready' && (
								<button
									className='icon-action'
									onClick={() =>
										onInspect(
											source,
										)
									}
									aria-label='Inspect source'>
									<ScanEye
										size={
											15
										}
									/>
								</button>
							)}
							<button
								className='icon-action danger'
								onClick={() =>
									setSourceToDelete(
										source,
									)
								}
								aria-label='Delete source'>
								<Trash
									size={
										15
									}
								/>
							</button>
						</div>
					</article>
				))}
				{sources.length === 0 && (
					<div className='sources-empty'>
						No sources uploaded yet.
					</div>
				)}
			</div>
		</aside>
	);
}
