import packageJson from '../../../package.json';

function version(): string {
	const configured = process.env.APP_VERSION?.trim();
	return (configured || packageJson.version).replace(/^v/i, '');
}

export function AppVersion() {
	return (
		<small className='app-version' aria-label={`Application version ${version()}`}>
			Version {version()}
		</small>
	);
}
