const http = require("http");
http.createServer((req, res) => {
  res.end("Hello from bind mount!\n");
}).listen(3000);
