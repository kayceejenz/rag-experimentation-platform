const dateTimeFormatter = new Intl.DateTimeFormat('en-GB', {
	year: 'numeric',
	month: 'short',
	day: '2-digit',
	hour: '2-digit',
	minute: '2-digit',
	hourCycle: 'h23',
	timeZone: 'UTC',
	timeZoneName: 'short',
});

const dateTimeWithSecondsFormatter = new Intl.DateTimeFormat('en-GB', {
	month: 'short',
	day: '2-digit',
	hour: '2-digit',
	minute: '2-digit',
	second: '2-digit',
	hourCycle: 'h23',
	timeZone: 'UTC',
	timeZoneName: 'short',
});

const timeFormatter = new Intl.DateTimeFormat('en-GB', {
	hour: '2-digit',
	minute: '2-digit',
	hourCycle: 'h23',
	timeZone: 'UTC',
});

const numberFormatter = new Intl.NumberFormat('en-GB');

export function formatDateTime(value: string | Date): string {
	return dateTimeFormatter.format(new Date(value));
}

export function formatDateTimeWithSeconds(value: string | Date): string {
	return dateTimeWithSecondsFormatter.format(new Date(value));
}

export function formatTime(value: string | Date): string {
	return timeFormatter.format(new Date(value));
}

export function formatNumber(value: number): string {
	return numberFormatter.format(value);
}

export function formatBytes(bytes: number): string {
	if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
	const units = ['B', 'KB', 'MB', 'GB'] as const;
	const unitIndex = Math.min(
		Math.floor(Math.log(bytes) / Math.log(1024)),
		units.length - 1,
	);
	const value = bytes / 1024 ** unitIndex;
	const precision = unitIndex === 0 || value >= 100 ? 0 : value >= 10 ? 1 : 2;
	return `${value.toFixed(precision)} ${units[unitIndex]}`;
}
