from flask import Flask, render_template, request, jsonify, Response
import json
import time

from scraper_engine import start_scraper, stop_scraper, status

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def api_start():
    success, msg = start_scraper()
    return jsonify({"success": success, "message": msg})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    success, msg = stop_scraper()
    return jsonify({"success": success, "message": msg})

@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({
        "is_running": status.is_running
    })

@app.route('/stream')
def stream():
    def event_stream():
        # First send a ping to establish connection
        yield "data: {\"type\": \"log\", \"msg\": \"متصل بنجاح مع محرك السحب!\"}\n\n"
        while True:
            try:
                # Prioritize logs
                if not status.logs_queue.empty():
                    msg = status.logs_queue.get_nowait()
                    yield f"data: {json.dumps(msg)}\n\n"
                    
                # Progress
                elif not status.progress_queue.empty():
                    prog = status.progress_queue.get_nowait()
                    yield f"data: {json.dumps(prog)}\n\n"
                else:
                    time.sleep(0.5)
            except GeneratorExit:
                break
    return Response(event_stream(), content_type='text/event-stream')

if __name__ == '__main__':
    print("Dashboard server running on: http://127.0.0.1:5000")
    print("If you have issues, make sure to: pip install flask cloudscraper beautifulsoup4 requests lxml")
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
