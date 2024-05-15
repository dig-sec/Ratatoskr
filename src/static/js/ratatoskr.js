function generateUUID() {
    let d = new Date().getTime();
    let uuid = 'xxxxxxxx-xxxx-xxxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        let r = (d + Math.random() * 16) % 16 | 0;
        d = Math.floor(d / 16);
        return (c == 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
    return uuid;
}

function setUUID() {
    let uuid = generateUUID();
    document.getElementById('session').value = uuid;
}

window.onload = setUUID;

document.getElementById('reset-uuid-button').addEventListener('click', setUUID);

let intervalId;

function fetchQueryStatus(query_id) {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', `/api/query_status?query_id=${query_id}`);
    xhr.onload = () => {
        if (xhr.status === 200) {
            const data = JSON.parse(xhr.responseText);
            const status = data.status;
            const response = data.response;
            if (status === "completed") {
                const responseElement = document.getElementById('response');
                const newText = document.createTextNode(response + '\n\n');
                responseElement.insertBefore(newText, responseElement.firstChild);
                document.getElementById('loading').style.display = 'none';
                clearInterval(intervalId);
            }
        }
    };
    xhr.send();
}

function sendQuery() {
    document.getElementById('loading').style.display = 'block';

    const formData = {
        user: document.getElementById('user').value,
        session: document.getElementById('session').value,
        model: document.getElementById('model').value,
        query: document.getElementById('query').value,
        // wikipedia: document.getElementById('wikipedia').checked,
        use_rag_database: document.getElementById('use_rag_database').checked,
        // internet: document.getElementById('internet').checked,
    };

    fetch('/api/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        const query_id = data.query_id;

        intervalId = setInterval(() => {
            fetchQueryStatus(query_id);
        }, 10000);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('loading').style.display = 'none';
    });
}

function sendQueryRAG() {
    const query = document.getElementById('query-rag').value;

    fetch('/api/query_rag', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {

        for (let i = 0; i < data.length; i++) {
            const pageContent = data[i].page_content;
            const metadataSource = data[i].metadata_source;
            document.getElementById('response-rag').value += '\nPage Content: ' + pageContent;
            document.getElementById('response-rag').value += '\nMetadata Source: ' + metadataSource;
            document.getElementById('response-rag').value += '\n\n';
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function summarizeSources() {
    const sources = document.getElementById('sources').value;

    fetch('/api/metadata_summary', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sources }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.text();
    })
    .then(data => {
        document.getElementById('text-summary').value = data;
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// function submitLink() {
//     const link = document.getElementById('link').value;

//     fetch('/api/process_url', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({ url: link }),
//     })
//     .then(response => {
//         if (!response.ok) {
//             throw new Error('Network response was not ok');
//         }
//         return response.json();
//     })
//     .then(data => {
//         console.log('URL processed successfully');
//     })
//     .catch(error => {
//         console.error('Error:', error);
//     });
// }