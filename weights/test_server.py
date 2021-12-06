import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger("test_web_server")
reply_payload = "default reply"


class RequestHandler(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        logger.info(
            "GET request,\nPath: %s\nHeaders:\n%s\n", str(self.path), str(self.headers)
        )
        self._set_response()
        self.wfile.write(reply_payload.encode("utf-8"))

    def do_POST(self):
        pass


class TestServer:
    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def run(
        self, reply, server_class=HTTPServer, handler_class=RequestHandler, port=8000
    ):
        global reply_payload
        reply_payload = reply
        server_address = ("", port)
        self.httpd = server_class(server_address, handler_class)
        self.httpd.timeout = 2
        logger.info("Starting httpd...\n")

        def serve_forever(httpd):
            with httpd:
                httpd.serve_forever()

        self.thread = Thread(target=serve_forever, args=(self.httpd,))
        self.thread.setDaemon(True)
        self.thread.start()


if __name__ == "__main__":
    from sys import argv

    TestServer().run()
