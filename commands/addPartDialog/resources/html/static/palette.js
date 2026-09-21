function setStatus(message) {
    document.getElementById('status').innerHTML = message;
}

function renderResults(data) {
    const container = document.getElementById('results');
    container.innerHTML = '';
    setStatus(`Found ${data.results.length} result(s)`);

    if (data.results.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'empty';
        empty.textContent = 'No results found.';
        container.appendChild(empty);
        return;
    }

    data.results.forEach((item, idx) => {
        const card = document.createElement('div');
        card.className = 'card';

        const imgbox = document.createElement('div');
        imgbox.className = 'imgbox';
        if (item.image) {
            const img = document.createElement('img');
            img.src = item.image;
            img.loading = 'lazy';
            imgbox.appendChild(img);
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

        if (data.vendor === 'GrabCAD') {
            item.files.forEach((f) => {
                const btn = document.createElement('button');
                btn.className = 'dl';
                btn.textContent = `${f.type.toUpperCase()}`;
                btn.title = f.name;
                btn.addEventListener('click', () => {
                    downloadFile(f.download_url, f.name);
                });
                filesBox.appendChild(btn);
            });
        } else {
            item.files.forEach((f) => {
                const btn = document.createElement('button');
                btn.className = 'dl';
                btn.textContent = `Download ${f.type.toUpperCase()}`;
                btn.title = f.name;
                btn.addEventListener('click', () => {
                    downloadFile(f.download_url, f.name);
                });
                filesBox.appendChild(btn);
            });
        }

        info.appendChild(name);
        info.appendChild(author);
        info.appendChild(filesBox);

        card.appendChild(imgbox);
        card.appendChild(info);
        container.appendChild(card);
    });
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