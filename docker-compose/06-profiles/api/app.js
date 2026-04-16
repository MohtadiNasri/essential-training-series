const http = require("http");
const env = process.env.NODE_ENV || "development";
http.createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end(`Hello from API — env: ${env}\n`);
}).listen(3000);
console.log(`API running on port 3000 [${env}]`);
