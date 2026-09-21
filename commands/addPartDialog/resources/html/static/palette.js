function setStatus(message) {
    document.getElementById('status').innerHTML = message;
}

let _allResults = [];
let _currentPage = 1;
const PAGE_SIZE = 8;

function renderResults(data) {
    _allResults = data.results;
    _currentPage = 1;
    renderPage();
}

function renderPage() {
    const container = document.getElementById('results');
    const status = document.getElementById('status');
    container.innerHTML = '';

    const total = _allResults.length;
    if (total === 0) {
        status.innerHTML = 'No results found.';
        const empty = document.createElement('div');
        empty.className = 'empty';
        empty.textContent = 'No results found.';
        container.appendChild(empty);
        return;
    }

    const pageCount = Math.ceil(total / PAGE_SIZE);
    status.innerHTML = `Found ${total} result(s) — Page ${_currentPage} of ${pageCount}`;

    const start = (_currentPage - 1) * PAGE_SIZE;
    const slice = _allResults.slice(start, start + PAGE_SIZE);

    slice.forEach((item, idx) => {
        try {
        const card = document.createElement('div');
        card.className = 'card';

        const imgbox = document.createElement('div');
        imgbox.className = 'imgbox';

        if (item.image && item.image.toLowerCase().indexOf('missing_card') === -1) {
            const img = document.createElement('img');
            img.src = item.image;
            img.loading = 'lazy';
            img.referrerPolicy = 'no-referrer';
            img.addEventListener('error', () => {
                img.remove();
                const ph = document.createElement('div');
                ph.className = 'noimg';
                imgbox.appendChild(ph);
            });
            imgbox.appendChild(img);
        } else {
            const ph = document.createElement('div');
            ph.className = 'noimg';
            imgbox.appendChild(ph);
        }

        const info = document.createElement('div');
        info.className = 'info';

        const name = document.createElement('div');
        name.className = 'name';
        name.textContent = item.name;

        const author = document.createElement('div');
        author.className = 'author';
        author.textContent = item.author ? `by ${item.author}` : '';

        const filesBox = document.createElement('div');
        filesBox.className = 'files';

        item.files.forEach((f) => {
            const btn = document.createElement('button');
            btn.className = 'dl';
            btn.textContent = f.type ? `Download ${String(f.type).toUpperCase()}` : 'Download';
            btn.title = f.name;
            btn.addEventListener('click', () => {
                downloadFile(f.download_url || f.downloadUrl, f.name);
            });
            filesBox.appendChild(btn);
        });

        info.appendChild(name);
        info.appendChild(author);
        info.appendChild(filesBox);

        card.appendChild(imgbox);
        card.appendChild(info);
        container.appendChild(card);
        } catch (err) {
            console.warn('Card render skipped:', err);
        }
    });

    if (pageCount > 1) {
        const pager = document.createElement('div');
        pager.className = 'pager';

        const prev = document.createElement('button');
        prev.className = 'pg';
        prev.textContent = '‹ Prev';
        prev.disabled = _currentPage <= 1;
        prev.addEventListener('click', () => {
            if (_currentPage > 1) { _currentPage--; renderPage(); }
        });

        const next = document.createElement('button');
        next.className = 'pg';
        next.textContent = 'Next ›';
        next.disabled = _currentPage >= pageCount;
        next.addEventListener('click', () => {
            if (_currentPage < pageCount) { _currentPage++; renderPage(); }
        });

        const pageLabel = document.createElement('span');
        pageLabel.className = 'pglabel';
        pageLabel.textContent = `${_currentPage} / ${pageCount}`;

        pager.appendChild(prev);
        pager.appendChild(pageLabel);
        pager.appendChild(next);
        container.appendChild(pager);
    }
}

function showError(message) {
    const container = document.getElementById('results');
    container.innerHTML = '';
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = message;
    container.appendChild(empty);
}

function downloadFile(url, filename) {
    const args = JSON.stringify({ url: url, filename: filename });
    setStatus(`Requesting download of ${filename}...`);
    adsk.fusionSendData('downloadFile', args).then((result) => {
        document.getElementById('status').innerHTML = result;
    }).catch((err) => {
        setStatus(`Download failed: ${err}`);
    });
}

window.fusionJavaScriptHandler = {
    handle: function (action, data) {
        try {
            if (action === 'searchResults') {
                renderResults(JSON.parse(data));
            } else if (action === 'searchError') {
                showError(data);
            } else if (action === 'status') {
                setStatus(data);
            } else {
                return `Unexpected command type: ${action}`;
            }
        } catch (e) {
            console.log(e);
            console.log(`Exception caught with command: ${action}, data: ${data}`);
        }
        return 'OK';
    },
};