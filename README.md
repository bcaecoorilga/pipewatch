# pipewatch

A lightweight CLI tool for monitoring and alerting on data pipeline health metrics.

---

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/youruser/pipewatch.git && cd pipewatch && pip install .
```

---

## Usage

Monitor a pipeline by pointing pipewatch at your metrics endpoint or log source:

```bash
pipewatch monitor --source my_pipeline --interval 60 --alert-on failure,latency
```

Check pipeline status at a glance:

```bash
pipewatch status --source my_pipeline
```

Set a threshold alert and get notified when metrics exceed limits:

```bash
pipewatch watch --source my_pipeline --metric latency --threshold 500 --notify slack
```

### Example Output

```
[2024-03-15 10:42:01] ✅ my_pipeline   status=healthy   latency=120ms   records=48,302
[2024-03-15 10:43:01] ⚠️  my_pipeline   status=degraded  latency=610ms   records=12,100
[2024-03-15 10:43:01] 🔔 ALERT: latency threshold exceeded (610ms > 500ms)
```

---

## Configuration

Pipewatch can be configured via a `pipewatch.yaml` file in your project root:

```yaml
source: my_pipeline
interval: 60
metrics:
  - latency
  - failure_rate
alerts:
  slack_webhook: https://hooks.slack.com/your/webhook
```

---

## License

This project is licensed under the [MIT License](LICENSE).