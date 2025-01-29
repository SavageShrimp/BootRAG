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

    console.log('Processing text:', doctext);

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
            const decodedText = data.text;
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
var abortController = new AbortController()

function CancelGenerate() {
    if (abortController) {
        abortController.abort();
        fetch('/close', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: ""
        })
    }
}


async function generateResponse() {
    try {
        const queryInput = document.getElementById('query-input');
        const responseDiv = document.getElementById('response-list');
        const elements = createResponseElements(responseDiv);
        const { promptDiv, messageDiv } = elements;

        promptDiv.textContent = queryInput.value.trim();

        if (!queryInput.value.trim()) {
            showMessage(messageDiv, 'Please enter a question or prompt.');
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

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        await processStream(response.body, messageDiv);
    } catch (error) {
        console.error('Error in generateResponse:', error);
        showMessage(messageDiv, 'Error generating response.');
    } finally {
        document.getElementById('generate-btn').disabled = false;
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
                // globalString += textToAdd; // Append the content with a line break
            } else {
                fullText = chunk || '';
            }

            // Replace "\n" with "<br>" before showing the message
            fullText = fullText.replace(/\n/g, '<br>');
            showMessage(messageDiv, fullText);

        }
    } catch (error) {
        console.error('Error processing stream:', error);
        if (fullText !== '') {
            showMessage(messageDiv, 'Error generating response.');
        }
    }
}

function setupResponseDiv(container) {
    const responseDiv = document.createElement('div');
    responseDiv.className = 'response-item';

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
    element.innerHTML += text
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
