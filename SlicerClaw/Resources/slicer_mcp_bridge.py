import sys
import json
import urllib.request
import urllib.error

SLICER_MCP_URL = "http://127.0.0.1:2016/mcp"

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            line = line.strip()
            if not line: continue
            req = urllib.request.Request(SLICER_MCP_URL, data=line.encode('utf-8'))
            req.add_header('Content-Type', 'application/json')
            try:
                response = urllib.request.urlopen(req, timeout=120)
                sys.stdout.write(response.read().decode('utf-8') + "\n")
                sys.stdout.flush()
            except urllib.error.URLError as e:
                try:
                    msg = json.loads(line)
                    if msg.get("id") is not None:
                        err = {"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32000, "message": str(e)}}
                        sys.stdout.write(json.dumps(err) + "\n")
                        sys.stdout.flush()
                except: pass
        except KeyboardInterrupt: break
        except Exception as e: sys.stderr.write(f"Bridge error: {e}\n")

if __name__ == '__main__':
    main()