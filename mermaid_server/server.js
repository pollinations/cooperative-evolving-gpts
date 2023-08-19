const express = require('express');
const app = express();
const PORT = 3000;

let clients = [];
let accumulatedDiagram = '';

// Middleware for serving the static HTML file
app.get('/', (req, res) => {
    res.sendFile(__dirname + '/index.html');
});

// Server-Sent Event setup
app.get('/events', (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.flushHeaders();

    clients.push(res);
    sendToClients(accumulatedDiagram);
    // Remove clients when they disconnect
    req.on('close', () => {
        clients = clients.filter(client => client !== res);
    });
});

// Listen for standard input and accumulate diagram line by line
process.stdin.on('data', (data) => {
    accumulatedDiagram += data.toString();
    sendToClients(accumulatedDiagram);
});

function sendToClients(data) {
    // Split the data by lines and prefix each line with `data: `
    const formattedData = data.split('\n').map(line => `data: ${line}`).join('\n');
    
    clients.forEach(client => {
        console.log(`Sending to client: ${formattedData}`);
        client.write(`${formattedData}\n\n`);  // Double newline to indicate end of the message
    });
}

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}/`);
});
