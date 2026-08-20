'use client';

import {
	FormEvent,
	KeyboardEvent,
	forwardRef,
	useEffect,
	useRef,
} from 'react';
import { ArrowUp, Square } from 'lucide-react';

export const MessageComposer = forwardRef<
	HTMLFormElement,
	{
		sending: boolean;
		placeholder: string;
		defaultValue?: string;
		onSubmit: (event: FormEvent<HTMLFormElement>) => void;
		onStop: () => void;
	}
>(function MessageComposer(
	{ sending, placeholder, defaultValue, onSubmit, onStop },
	ref,
) {
	const textareaRef = useRef<HTMLTextAreaElement>(null);

	useEffect(() => {
		const textarea = textareaRef.current;
		if (!textarea) return;
		textarea.style.height = 'auto';
		textarea.style.height = `${Math.min(textarea.scrollHeight, window.innerHeight * 0.5)}px`;
	}, [defaultValue]);

	function handleKeyDown(
		event: KeyboardEvent<HTMLTextAreaElement>,
	) {
		if (
			event.key === 'Enter' &&
			!event.shiftKey &&
			!event.nativeEvent.isComposing
		) {
			event.preventDefault();
			event.currentTarget.form?.requestSubmit();
		}
	}

	function handleInput() {
		const textarea = textareaRef.current;
		if (!textarea) return;
		textarea.style.height = 'auto';
		textarea.style.height = `${Math.min(textarea.scrollHeight, window.innerHeight * 0.5)}px`;
	}

	function handleSubmit(event: FormEvent<HTMLFormElement>) {
		onSubmit(event);
		requestAnimationFrame(() => {
			const textarea = textareaRef.current;
			if (textarea) {
				textarea.style.height = 'auto';
			}
		});
	}

	return (
		<form
			ref={ref}
			className='message-composer'
			onSubmit={handleSubmit}>
			<textarea
				ref={textareaRef}
				name='content'
				rows={1}
				maxLength={12000}
				required
				disabled={sending}
				defaultValue={defaultValue}
				onKeyDown={handleKeyDown}
				onInput={handleInput}
				placeholder={placeholder}
			/>
			{sending ? (
				<button
					type='button'
					onClick={onStop}
					aria-label='Stop generating'>
					<Square
						size={15}
						fill='currentColor'
					/>
				</button>
			) : (
				<button
					type='submit'
					aria-label='Send message'>
					<ArrowUp size={20} />
				</button>
			)}
		</form>
	);
});
