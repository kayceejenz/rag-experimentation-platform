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
