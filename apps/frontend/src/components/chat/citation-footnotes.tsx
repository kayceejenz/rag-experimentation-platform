'use client';

import { useState } from 'react';
import { FileText, ChevronDown } from 'lucide-react';
import type { Citation } from '@/types/workspace';

export function CitationFootnotes({ citations }: { citations: Citation[] }) {
	const [expanded, setExpanded] = useState<Set<number>>(new Set());

	if (citations.length === 0) return null;

	function toggle(index: number) {
		setExpanded(current => {
			const next = new Set(current);
			if (next.has(index)) {
				next.delete(index);
			} else {
				next.add(index);
			}
			return next;
		});
	}

	const hasExpanded = expanded.size > 0;

	return (
		<footer className='citation-footnotes'>
			<div className='citation-chips'>
				{citations.map((citation, index) => {
					const isActive = expanded.has(index);
					return (
						<button
							key={`${citation.chunk_id}-${index}`}
							type='button'
							className={`citation-chip ${isActive ? 'active' : ''}`}
							onClick={() =>
								toggle(index)
							}
							aria-expanded={isActive}
							aria-label={`Citation ${index + 1}: ${citation.source_filename}${citation.page_number != null ? ` page ${citation.page_number}` : ''}`}>
							<span className='cite-chip-index'>
								{index + 1}
							</span>
							<ChevronDown
								size={11}
								className={`cite-chip-chevron ${isActive ? 'rotated' : ''}`}
							/>
						</button>
					);
				})}
			</div>
			{hasExpanded && (
				<div className='citation-excerpts'>
					{citations.map((citation, index) => {
						if (!expanded.has(index))
							return null;
						return (
							<div
								className='citation-excerpt-inline'
								key={`excerpt-${citation.chunk_id}-${index}`}>
								<div className='excerpt-header'>
									<span className='excerpt-index'>
										{index +
											1}
									</span>
									<FileText
										size={
											11
										}
									/>
									<span className='excerpt-source'>
										{
											citation.source_filename
										}
									</span>
									{citation.page_number !=
										null && (
										<span className='excerpt-page'>
											Page{' '}
											{
												citation.page_number
											}
										</span>
									)}
								</div>
								<blockquote>
									{
										citation.excerpt
									}
								</blockquote>
							</div>
						);
					})}
				</div>
			)}
		</footer>
	);
}
