# Search Tools

Use the interactive search and filters below to quickly find tools used by ProductHuntDB. This page performs client-side filtering so it works offline in the built docs.

---

<input id="tools-search-input" type="search" placeholder="Search tools (name, description, tags)..." style="width:100%; padding:0.5rem; margin:0.5rem 0 1rem 0; border-radius:6px; border:1px solid var(--sy-border-color, #ddd);">

<div id="tools-filters" style="margin-bottom:1rem; display:flex; gap:0.5rem; flex-wrap:wrap;">
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="build"> Build</label>
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="migrations"> Migrations</label>
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="api"> API</label>
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="validation"> Validation</label>
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="orm"> ORM</label>
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="database"> Database</label>
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="dataset"> Dataset</label>
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="data"> Data</label>
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="cli"> CLI</label>
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="logging"> Logging</label>
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="retry"> Retry</label>
  <label style="font-size:0.9rem;"><input type="checkbox" data-tag="progress"> Progress</label>
</div>

<div id="tools-list" style="display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:1rem; align-items:start;"></div>

<script>
(function(){
  const tools = [
    { id: 'uv', title: 'uv', url: 'uv', summary: 'Lightning-fast Python package manager', tags: ['build'] },
    { id: 'httpx', title: 'HTTPX', url: 'httpx', summary: 'Modern async HTTP client for Python', tags: ['api'] },
    { id: 'pydantic', title: 'Pydantic', url: 'pydantic', summary: 'Data validation using Python type hints', tags: ['validation'] },
    { id: 'sqlmodel', title: 'SQLModel', url: 'sqlmodel', summary: 'SQL databases with Python objects', tags: ['orm','database'] },
    { id: 'sqlite', title: 'SQLite', url: 'sqlite', summary: 'Self-contained SQL database engine', tags: ['database'] },
    { id: 'kaggle', title: 'Kaggle API', url: 'kaggle', summary: 'Automated dataset management and publishing', tags: ['dataset'] },
    { id: 'alembic', title: 'Alembic', url: 'alembic', summary: 'Database migration tool for SQLAlchemy', tags: ['migrations','build'] },
    { id: 'pandas', title: 'Pandas', url: 'pandas', summary: 'Powerful data analysis library', tags: ['data','dataset'] },
    { id: 'typer', title: 'Typer', url: 'typer', summary: 'Modern CLI framework with type hints', tags: ['cli'] },
    { id: 'loguru', title: 'Loguru', url: 'loguru', summary: 'Simple and elegant logging', tags: ['logging'] },
    { id: 'tenacity', title: 'Tenacity', url: 'tenacity', summary: 'General-purpose retrying library', tags: ['retry','api'] },
    { id: 'tqdm', title: 'tqdm', url: 'tqdm', summary: 'Fast, extensible progress bar', tags: ['progress','cli'] }
  ];

  const listEl = document.getElementById('tools-list');
  const inputEl = document.getElementById('tools-search-input');
  const filtersEl = document.getElementById('tools-filters');

  function render(filtered){
    listEl.innerHTML = '';
    if(filtered.length === 0){
      listEl.innerHTML = '<div class="note admonition warning">No tools match your search/filters.</div>';
      return;
    }
    for(const t of filtered){
      const a = document.createElement('a');
      a.href = t.url; // Sphinx will resolve to correct page
      a.className = 'ph-tool-card';
      a.style.display = 'block';
      a.style.padding = '1rem';
      a.style.border = '1px solid var(--sy-border-color, #ddd)';
      a.style.borderRadius = '8px';
      a.style.background = 'var(--sy-card-bg, var(--sy-bg, #fff))';
      a.style.color = 'inherit';
      a.style.textDecoration = 'none';
      a.style.boxShadow = 'var(--sy-elevation-1, none)';
      a.innerHTML = `
        <strong style="display:block; margin-bottom:0.25rem; font-size:1rem;">${t.title}</strong>
        <div style="font-size:0.9rem; margin-bottom:0.5rem; color:var(--ph-muted, #666)">${t.summary}</div>
        <div style="font-size:0.8rem; color:var(--ph-accent-primary, #da532c)">${t.tags.join(', ')}</div>
      `;
      listEl.appendChild(a);
    }
  }

  function getActiveTags(){
    const checked = Array.from(filtersEl.querySelectorAll('input[type=checkbox]:checked'));
    return checked.map(n => n.dataset.tag);
  }

  function filterTools(){
    const q = inputEl.value.trim().toLowerCase();
    const tags = getActiveTags();
    let filtered = tools.filter(t => {
      const hay = [t.title, t.summary, t.tags.join(' ')].join(' ').toLowerCase();
      if(q && hay.indexOf(q) === -1) return false;
      if(tags.length>0){
        return tags.every(tag => t.tags.includes(tag));
      }
      return true;
    });
    render(filtered);
  }

  inputEl.addEventListener('input', filterTools);
  filtersEl.addEventListener('change', filterTools);

  // keyboard shortcut: focus search with "/"
  document.addEventListener('keydown', (e) => {
    if(e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA'){
      e.preventDefault();
      inputEl.focus();
    }
  });

  // initial render
  render(tools);
})();
</script>
