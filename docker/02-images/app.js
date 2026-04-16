const http = require("http");
http.createServer((req, res) => {
  res.end("Hello from Docker v29!\n");
}).listen(3000);
