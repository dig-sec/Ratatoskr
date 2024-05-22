// UUID Generation 
function generateUUID() {
    return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

// Initial UUID Setting
function setUUID() {
    document.getElementById('session').value = generateUUID();
}

window.addEventListener('load', setUUID);
document.getElementById('reset-uuid-button').addEventListener('click', setUUID);

// ---- Chat Interface (Main Query) ----

let intervalId; // For polling query status

async function sendQuery() {
    const mode = document.getElementById('mode').value;

    if (mode === 'dialog') {
        document.getElementById('loading').style.display = 'block';
        const formData = {
            user: document.getElementById('user').value,
            session: document.getElementById('session').value,
            model: document.getElementById('model').value,
            query: document.getElementById('query').value,
            use_rag_database: document.getElementById('use_rag_database').checked,
        };

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            const query_id = data.query_id;

            intervalId = setInterval(() => fetchQueryStatus(query_id), 10000);

        } catch (error) {
            handleError('Error sending query:', error, 'response');
        }
    } else {
        const maxResults = parseInt(document.getElementById('max-results').value) || 10;
        const queryText = document.getElementById('query').value;

        try {
            const response = await fetch(`/api/${mode}_search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: queryText,
                    max_results: maxResults
                })
            });
            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            let responseText = '';
            if (mode === 'vector') {
                data.forEach(result => {
                    responseText += 'metadata_source: ' + result.metadata_source + '\n' + 'page_content: ' + result.page_content + '\n\n';
                });
            } else {
                responseText = JSON.stringify(data, null, 2);
            }
            updateResponseArea('response', responseText);

        } catch (error) {
            handleError('Error sending query:', error, 'response');
        }
    }
}

// ---- Clear Response Section ----
function clearResponse() {
    document.getElementById('response').innerHTML = '';
}

async function fetchQueryStatus(query_id) {
    try {
        const response = await fetch(`/api/query_status?query_id=${query_id}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        const { status, response: queryResponse } = data; // Rename 'response' to avoid shadowing

        if (status === "completed") {
            updateResponseArea('response', queryResponse);
            document.getElementById('loading').style.display = 'none';
            clearInterval(intervalId);
        }
    } catch (error) {
        handleError('Error fetching query status:', error, 'response');
    }
}

// ---- Common Functions ----
function updateResponseArea(elementId, text) {
    const responseElement = document.getElementById(elementId);
    const newText = document.createTextNode(text + '\n\n');
    responseElement.insertBefore(newText, responseElement.firstChild); // Add to top
}

function handleError(message, error, responseElementId) {
    console.error(message, error);
    document.getElementById('loading').style.display = 'none';
    updateResponseArea(responseElementId, `Error: ${error.message}`);
}

// ---- Summarize based on sources ----

async function summarizeSources() {
    const sources = document.getElementById('sources').value;

    try {
        const response = await fetch('/api/metadata_summary', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ sources }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.text();
        document.getElementById('text-summary').value = data;
    } catch (error) {
        handleError('Error summarizing sources:', error, 'text-summary'); // Updated error handling
    }
}

// ---- Link Submission Section ----

async function submitLink() {
    const link = document.getElementById('link').value;

    try {
        const response = await fetch('/api/submit_link', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ link }),
        });

        if (response.ok) {
            alert('Link submitted successfully!');
        } else {
            alert('Error submitting link.');
        }
    } catch (error) {
        console.error('Error submitting link:', error);
        alert('An error occurred while submitting the link.');
    }
}
