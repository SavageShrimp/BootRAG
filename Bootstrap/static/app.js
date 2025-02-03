

function generateRandomString(length) {
    let randomString = Math.random().toString(36).substring(2, length + 2);
    while (randomString.length < length) {
        randomString += Math.random().toString(36).substring(2, length + 2);
    }
    return randomString.substring(0, length);
}

console.log(generateRandomString(7)); // Outputs a random 7-character string


function processFile() {
    const fileInput = document.getElementById('file-upload');
    const textInput = document.getElementById('text-input');

    if (!fileInput.files || fileInput.files.length === 0) {
        alert('Please select a file');
        return;
    }

    const file = fileInput.files[0];
    if (!file.type.includes('text')) {
        alert('Only text files (.txt, .html) are allowed');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        const text = e.target.result;
        textInput.value = text;
        processText(textInput.value); // Pass the text from the textarea
    };
    reader.readAsText(file);
}

function processText(doctext = undefined) {
    // If no argument is provided, get the text from the textarea
    if (doctext === undefined) {
        const textInput = document.getElementById('text-input');
        doctext = textInput.value.trim();
        if (doctext === '') {
            alert('Please enter some text or upload a file.');
            return;
        }
    }

    const data = {
        text: doctext,
        name: "text-input"
    };

    //console.log('Processing text:', doctext);

    fetch('/process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        console.log('API Response:', data);
        if (data.error) {
            addResponse('Error:', data.error, 'error');
        } else {
            const decodedText = '<pre><code>' + doctext + '</code></pre>';
            addResponse('Processed Text:', decodedText);
        }
    })
    .catch(error => {
        console.error('Error processing text:', error);
        addResponse('Error:', error.message, 'error');
    });
}


let chatMessages = [];
var response;
let abortController = null;

function startRequest() {
    abortController = new AbortController();

    fetch('/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prompt: '...' }),
        signal: abortController.signal
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network error');
        }
        return response.json();
    })
    .then(data => {
        console.log(data);
        // Handle the response
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Update the CancelGenerate function
function CancelGenerate() {
    if (abortController) {
        try {
            abortController.abort('User canceled the request');
            console.log('Request aborted successfully');

            // Perform cleanup only if the response was aborted
            if (response && response.aborted) {
                performCleanup();
            }
        } catch (error) {
            console.error('Error aborting request:', error);
        } finally {
            // Reset the abortController
            abortController = null;
        }
    }
}

// Update performCleanup to handle stream errors
function performCleanup() {
    // Add error handling for the cleanup request
    fetch('/close', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ /* any data needed */ })
    })
    .then(response => {
        if (!response.ok) {
            console.warn('Close request failed:', response.statusText);
            return;
        }
        console.log('Cleanup completed successfully');
    })
    .catch(error => {
        console.error('Error in cleanup:', error);
    });
}

async function generateResponse() {
    try {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }

        abortController = new AbortController();
        const queryInput = document.getElementById('query-input');
        const responseList = document.getElementById('response-list');

        // Create a new response item using setupResponseDiv
        const elements = setupResponseDiv(responseList);
        const { responseDiv, promptDiv, messageDiv } = elements;

        promptDiv.innerHTML = `<div>${queryInput.value.trim().replace(/\n/g, '<br>')}</div>`;
        promptDiv.style.backgroundColor = '#e6e6fa'; // Light purple

        if (!queryInput.value.trim()) {
            showMessage(messageDiv, 'Please enter a question or prompt.');
            if (loadingElement) {
                loadingElement.style.display = 'none';
            }
            return;
        }

        messageDiv.textContent = '';
        console.log('Cleared message div');

        response = await fetch('/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: queryInput.value }),
            stream: true,
            signal: abortController.signal
        });

        // Check if request was aborted
        if (response.aborted) {
            showMessage(messageDiv, 'Request was canceled.');
            if (loadingElement) {
                loadingElement.style.display = 'none';
            }
            performCleanup();
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        await processStream(response.body, messageDiv);
    } catch (error) {
        console.error('Error in generateResponse:', error);
        showMessage(messageDiv, 'Error generating response.');
        performCleanup();
    } finally {
        document.getElementById('generate-btn').disabled = false;
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }
}


function createResponseElements(container) {
    if (container.querySelector('.prompt') && container.querySelector('.message')) {
        return {
            promptDiv: container.querySelector('.prompt'),
            messageDiv: container.querySelector('.message')
        };
    }

    const promptDiv = document.createElement('div');
    promptDiv.className = 'prompt';
    promptDiv.textContent = 'Your prompt goes here...';

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.textContent = 'Response will appear here...';

    container.appendChild(promptDiv);
    container.appendChild(messageDiv);0

    return { promptDiv, messageDiv };
}

async function processStream(body, messageDiv) {
    // Early check for aborted response
    if (!body) {
        showMessage(messageDiv, 'Request was canceled.');
        return;
    }

    const reader = await body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullText = '';

    try {
        while (true) {
            const { done, value } = await reader.read();

            if (done) {
                if (fullText !== '') {
                    showMessage(messageDiv, fullText);
                }
                reader.releaseLock();
                break;
            }

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;

            if (chunk[0] == '{') {
                obj = JSON.parse(chunk);
                fullText = obj.content || '';
            } else {
                fullText = chunk || '';
            }

            //showMessage(messageDiv, "<pre><code>"+fullText+"</pre></code>");
            showMessage(messageDiv, fullText);

        }
    } catch (error) {
        if (error.name === 'AbortError') {
            showMessage(messageDiv, 'Request was canceled.');
            return;
        }
        console.error('Error processing stream:', error);
        if (fullText !== '') {
            showMessage(messageDiv, 'Error generating response.');
        }
    }
}

sp = new StringProcessor()



function setupResponseDiv(container) {
    const responseDiv = document.createElement('div');
    responseDiv.className = 'response-item';
    responseDiv.style.whiteSpace = 'normal'; // Add this line to enable word wrap

    const timestampDiv = document.createElement('div');
    timestampDiv.className = 'timestamp';
    timestampDiv.textContent = new Date().toLocaleString();

    const promptDiv = document.createElement('div');
    promptDiv.className = 'prompt';
    promptDiv.textContent = 'Your prompt goes here...';

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';
    messageDiv.textContent = 'Response will appear here...';

    responseDiv.appendChild(timestampDiv);
    responseDiv.appendChild(promptDiv);
    responseDiv.appendChild(messageDiv);

    container.appendChild(responseDiv);

    return {
        responseDiv,
        timestampDiv,
        promptDiv,
        messageDiv
    };
}

function showMessage(element, text) {
    // Use the StringProcessor to accumulate and process the text
    console.log(text)
    sp.appendString(text);
    sp.updateState();
    //console.log(text)

    // Retrieve the processed text from StringProcessor
    const processedText = sp.getText();

    // console.log(processedText)

    // Set the element's innerHTML to the processed text
    element.innerHTML = processedText;
}

function addResponse(prompt, responseText, type = 'info') {
    const responseList = document.getElementById('response-list');
    const responseDiv = document.createElement('div');
    responseDiv.className = 'response-item';
    responseDiv.innerHTML = `
        <div class="timestamp">${new Date().toLocaleTimeString()}</div>
        <div class="prompt">${prompt}</div>
        <div class="message">${responseText}</div>
    `;
    if (type === 'error') {
        responseDiv.classList.add('error');
    }
    responseList.appendChild(responseDiv);
}

