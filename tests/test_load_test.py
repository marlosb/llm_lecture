import contextlib
import io
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer

import test as load_test


class LoadTestTests(unittest.TestCase):
    def serve(
        self, responses: list[tuple[int, bytes]]
    ) -> tuple[str, list[dict[str, object]]]:
        received: list[dict[str, object]] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                body = self.rfile.read(int(self.headers["Content-Length"]))
                received.append(json.loads(body))
                status, content = responses.pop(0)
                self.send_response(status)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            def log_message(self, format: str, *args: object) -> None:
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()

        def cleanup() -> None:
            server.shutdown()
            thread.join()
            server.server_close()

        self.addCleanup(cleanup)
        return f"http://127.0.0.1:{server.server_port}", received

    def test_sends_long_requests_and_excludes_warmup_from_summary(self) -> None:
        content = json.dumps({"completion": "texto " * 1000}).encode("utf-8")
        base_url, received = self.serve([(200, content)] * 4)
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            status = load_test.main([
                "--base-url", base_url, "--requests", "3", "--concurrency", "2",
                "--max-new-tokens", "1500",
            ])

        self.assertEqual(status, 0)
        self.assertEqual(
            [body["max_new_tokens"] for body in received],
            [16, 1500, 1500, 1500],
        )
        self.assertEqual(len({body["text"] for body in received}), 3)
        self.assertIn("Succeeded: 3/3; failed: 0", output.getvalue())
        self.assertIn("completion characters/s", output.getvalue())

    def test_reports_http_and_invalid_response_failures(self) -> None:
        base_url, received = self.serve([
            (200, b'{"completion": "warmup"}'),
            (422, b'{"detail": "Context limit exceeded"}'),
            (200, b'{"completion": 123}'),
            (200, b'not json'),
        ])
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            status = load_test.main([
                "--base-url", base_url, "--requests", "3",
            ])

        self.assertEqual(status, 1)
        self.assertEqual(len(received), 4)
        self.assertIn("HTTP 422", output.getvalue())
        self.assertIn("Context limit exceeded", output.getvalue())
        self.assertIn("ValueError", output.getvalue())
        self.assertIn("JSONDecodeError", output.getvalue())
        self.assertIn("Succeeded: 0/3; failed: 3", output.getvalue())

    def test_warmup_failure_stops_before_load(self) -> None:
        base_url, received = self.serve([(500, b"Model unavailable")])
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            status = load_test.main(["--base-url", base_url])

        self.assertEqual(status, 1)
        self.assertEqual(len(received), 1)
        self.assertIn("Warm-up failed: HTTP 500", output.getvalue())


if __name__ == "__main__":
    unittest.main()
