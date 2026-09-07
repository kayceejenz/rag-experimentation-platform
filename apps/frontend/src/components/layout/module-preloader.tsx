export function ModulePreloader() {
	return (
		<div
			className='module-preloader'
			role='status'
			aria-label='Loading module'>
			<div className='preloader-heading'>
				<span />
				<span />
			</div>
			<div className='preloader-grid'>
				<span />
				<span />
				<span />
			</div>
			<div className='preloader-table'>
				<span />
				<span />
				<span />
				<span />
			</div>
			<span className='sr-only'>Loading…</span>
		</div>
	);
}
