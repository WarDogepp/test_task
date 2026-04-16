# Multimodal Inference Platform

This project contains a production-ready deployment for serving a multimodal AI inference platform. It provides a unified gateway to access speech-to-text, text embeddings, and multimodal (text + image) generation models.

## Architecture

The platform uses a microservices architecture managed by Docker Compose. An NGINX reverse proxy acts as a round-robin gateway, routing incoming API requests to the appropriate model serving containers based on the endpoint path.

### Model Serving Stack
* **Gemma 4 E4B (Text + Image):** Served using **vLLM** to leverage high-throughput GPU inference.
* **MPNet (Embeddings):** Served using Hugging Face's **Text Embeddings Inference (TEI)**. This runs on the CPU to reserve GPU memory for the main generative model.
* **Whisper (Speech-to-Text):** Served using **faster-whisper-server**. Configured to run on the CPU to optimize infrastructure costs while maintaining acceptable latency.

## Deployment Instructions

### Prerequisites
* Docker and Docker Compose installed.
* NVIDIA Container Toolkit (nvidia-docker) installed and configured for GPU support.
* A valid Hugging Face token.
* The project files saved and extracted locally on your machine.

### Local Setup
1.  Open your terminal and navigate to the local directory containing the project files (where `docker-compose.yml` is located).
2.  Create a `.env` file based on the provided example:
    ```bash
    cp .env.example .env
    ```
3.  Add your Hugging Face token to the `.env` file:
    ```env
    HF_TOKEN=your_real_token_here
    ```
4.  Build and start the services locally:
    ```bash
    docker compose up -d --build
    ```

The NGINX gateway will listen on port `80` and route traffic to:
* `/v1/chat/completions` -> vLLM (Gemma)
* `/v1/embeddings` -> TEI (MPNet)
* `/v1/audio/transcriptions` -> Whisper

### Validation (Optional)
A Python validation utility (`validate.py`) is included to verify endpoints.
```bash
# Test audio transcription
python validate.py transcribe --file test.wav

# Test embeddings
python validate.py embed --text "hello world"

# Test text+image inference
python validate.py chat --prompt "Describe this image" --image test.jpeg

## Operations & Jenkins Pipeline

A Jenkins pipeline (`Jenkinsfile`) is included to handle health checking, monitoring, and automated recovery.

### Failure Recovery
* **Container Level:** All services in `docker-compose.yml` use the `restart: always` policy for immediate recovery from unexpected crashes.
* **Stack Level:** The Jenkins pipeline runs periodically (e.g., every 15 minutes) and checks Docker health statuses. If unhealthy containers are detected, Jenkins automatically triggers a `docker compose restart` to recover the stack.

### Monitoring and Alerting
The pipeline performs end-to-end checks using the validation script to measure system performance:
* **Latency Monitoring:** Measures response time for full multimodal inference.
* **Resource Utilization:** Queries `nvidia-smi` to track GPU usage.
* **Alerts:** If latency exceeds 5.0 seconds or GPU utilization exceeds 90%, an automated email alert is sent to the DevOps team indicating that capacity is insufficient.

## Scaling Approach

The platform is designed to scale horizontally. When the alerting system notifies the team of an overloaded GPU host, the following steps are taken to add capacity:

1.  **Provisioning:** Bring up a new GPU-enabled serving machine.
2.  **Deployment:** Copy the project directory to the new machine and run `docker compose up -d` (excluding the NGINX gateway container).
3.  **Routing Distribution:** Update the `nginx.conf` on the primary gateway node to include the new machine's IP address in the `upstream` blocks. 
4.  **Reload:** Reload NGINX (`nginx -s reload`). Traffic will automatically be distributed in a round-robin fashion across all registered serving nodes.

## Assumptions and Tradeoffs
* **Compute Segregation:** Only the Gemma model is allocated GPU resources. Whisper and MPNet are explicitly pinned to CPU. This is a deliberate tradeoff to prevent Out-Of-Memory (OOM) errors on a single GPU while still serving all three models effectively.
* **Gateway Setup:** NGINX is currently deployed alongside the models. In a larger multi-node production setup, the gateway would be isolated on its own dedicated compute instance.
