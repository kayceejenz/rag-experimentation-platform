'use client';

import { CircleCheck, CircleAlert, LoaderCircle } from 'lucide-react';
import type { ToolCall } from '@/types/workspace';

export function ToolCallStep({ step }: { step: ToolCall }) {
	const isRunning = step.status === 'running';
	const isFailed = step.status === 'failed';

	return (
		<details
			className={`tool-step ${step.status}`}
			open={isRunning}>
			<summary>
				{isRunning ? (
					<LoaderCircle
						size={14}
						className='spin'
					/>
				) : isFailed ? (
					<CircleAlert size={14} />
				) : (
					<CircleCheck size={14} />
				)}
				<span className='tool-step-label'>
					{step.label}
				</span>
			</summary>
			<div className='tool-step-body'>
				{step.input != null && (
					<div className='tool-step-section'>
						<strong>Input</strong>
						<pre>
							{typeof step.input ===
							'string'
								? step.input
								: JSON.stringify(
										step.input,
										null,
										2,
									)}
						</pre>
					</div>
				)}
				{step.output != null && (
					<div className='tool-step-section'>
						<strong>Output</strong>
						<pre>
							{typeof step.output ===
							'string'
								? step.output
								: JSON.stringify(
										step.output,
										null,
										2,
									)}
						</pre>
					</div>
				)}
				{step.input == null &&
					step.output == null &&
					!isRunning && (
						<div className='tool-step-empty'>
							Step completed
							{isFailed
								? ' with error'
								: ''}
							.
						</div>
					)}
			</div>
		</details>
	);
}

export function ToolCallSteps({ steps }: { steps: ToolCall[] }) {
	if (!steps || steps.length === 0) return null;

	return (
		<div className='tool-steps'>
			{steps.map(step => (
				<ToolCallStep key={step.id} step={step} />
			))}
		</div>
	);
}
