// A simple Node.js server to receive extracted data from the Chrome Extension
// Run this file in your VS Code terminal using: node local_server.js

const http = require('http');

const PORT = 3000;

const server = http.createServer((req, res) => {
    // Handle CORS (Cross-Origin Resource Sharing)
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'OPTIONS, POST');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    // Handle preflight requests
    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        res.end();
        return;
    }

    if (req.method === 'POST') {
        let body = '';
        req.on('data', chunk => {
            body += chunk.toString();
        });
        
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                console.log('\n=======================================');
                console.log('📄 NEW PAGE EXTRACTED');
                console.log('=======================================');
                console.log(`Title: ${data.title}`);
                console.log(`URL:   ${data.url}`);
                console.log(`Time:  ${data.timestamp}`);
                console.log('\nExtracted Content:\n');
                console.log(data.content);
                console.log('\n=======================================\n');
            } catch (err) {
                console.log('\n--- Received Raw Data ---');
                console.log(body);
            }
            
            res.writeHead(200, { 'Content-Type': 'text/plain' });
            res.end('Data logged in terminal successfully!');
        });
    } else {
        res.writeHead(404);
        res.end();
    }
});

server.listen(PORT, () => {
    console.log(`\nLocal logging server is running!`);
    console.log(`Listening for Chrome Extension extractions on http://localhost:${PORT}`);
    console.log(`Waiting for data...\n`);
});
