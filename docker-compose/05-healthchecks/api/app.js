const http = require("http");
http.createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end("API healthy!\n");
}).listen(3000);
console.log("API running on port 3000");
