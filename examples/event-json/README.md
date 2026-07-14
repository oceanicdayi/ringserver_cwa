# Event JSON streaming with ringserver (Python)

Minimal example: publish and subscribe to earthquake event JSON over DataLink.

## 1. Build ringserver

From the repository root:

```bash
make
```

## 2. Start ringserver

Run from this directory so the relative `RingDirectory ring` resolves correctly:

```bash
cd examples/event-json
mkdir -p ring
../../ringserver ring-event.conf
```

Ports:

- `16000` — DataLink (publish / subscribe)
- `18000` — DataLink + HTTP (`/streams/json`, WebSocket `/datalink`)

## 3. Install Python client

```bash
cd examples/event-json
python3 -m pip install -r requirements.txt
```

## 4. Subscribe

```bash
python3 subscribe_events.py --match '.*/JSON'
```

## 5. Publish a demo event

In another terminal (same directory):

```bash
python3 publish_event.py
# or publish your own JSON file:
python3 publish_event.py --payload my-event.json
```

The subscriber should print the event immediately.

## Stream ID convention

Use a `/JSON` suffix, for example:

- `TW_DEMO_EVENT/JSON`
- `TW_CWB_INTENSITY/JSON`

Clients typically match with `.*/JSON`.

## Notes

- Increase `MaxPacketSize` if your event JSON exceeds the configured limit (this example uses 65536).
- SeedLink clients will not receive these packets; use DataLink.
- ringserver transports opaque payloads; schema validation belongs in your publishers/subscribers.
