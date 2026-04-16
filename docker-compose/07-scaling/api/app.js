const http = require("http");
const os = require("os");
http.createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end(`Hello from ${os.hostname()}\n`);
}).listen(3000);
console.log("API running on port 3000");
