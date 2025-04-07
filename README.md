# Insanely Fast Whisper API
An API to transcribe audio with [OpenAI's Whisper Large v3](https://huggingface.co/openai/whisper-large-v3)! Powered by 🤗 Transformers, Optimum & flash-attn

Features:
- 🎤 Transcribe audio to text at blazing fast speeds
- 📖 Fully open source and deployable on any GPU cloud provider
- 🗣️ Built-in speaker diarization
- ⚡ Easy to use and Fast API layer
- 📃 Async background tasks and webhooks
- 🔥 Optimized for concurrency and parallel processing
- ✅ Task management, cancel and status endpoints
- 🔒 Admin authentication for secure API access
- 🧩 Fully managed API available on [JigsawStack](https://jigsawstack.com/speech-to-text)

Based on [Insanely Fast Whisper CLI](https://github.com/Vaibhavs10/insanely-fast-whisper) project. Check it out if you like to set up this project locally or understand the background of insanely-fast-whisper.

This project is focused on providing a deployable blazing fast whisper API with docker on cloud infrastructure with GPUs for scalable production use cases.

With [Fly.io recent GPU service launch](https://fly.io/docs/gpus/gpu-quickstart/), I've set up the fly config file to easily deploy on fly machines! However, you can deploy this on any other VM environment that supports GPUs and docker.


Here are some benchmarks we ran on Nvidia A100 - 80GB and fly.io GPU infra👇
| Optimization type    | Time to Transcribe (150 mins of Audio) |
|-------------------|----------------------------------------|
| **large-v3 (Transformers) (`fp16` + `batching [24]` + `Flash Attention 2`)** | **~2 (*1 min 38 sec*)**            |
| **large-v3 (Transformers) (`fp16` + `batching [24]` + `Flash Attention 2` + `diarization`)** | **~2 (*3 min 16 sec*)**            |
| **large-v3 (Transformers) (`fp16` + `batching [24]` + `Flash Attention 2` + `fly machine startup`)** | **~2 (*1 min 58 sec*)**            |
| **large-v3 (Transformers) (`fp16` + `batching [24]` + `Flash Attention 2` + `diarization + fly machine startup`)** | **~2 (*3 min 36 sec*)**|

The estimated startup time for the Fly machine with GPU and loading up the model is around ~20 seconds. The rest of the time is spent on the actual computation.

## Docker Image

```
yoeven/insanely-fast-whisper-api:latest
```

Docker Hub: [yoeven/insanely-fast-whisper-api](https://hub.docker.com/r/yoeven/insanely-fast-whisper-api)

## Running with Docker

To run the application using Docker with GPU support, follow these steps:

### **Prerequisites**
- **Docker Engine** installed on your machine. Refer to the [official Docker installation guide](https://docs.docker.com/get-docker/) if you haven't installed it yet.
- **NVIDIA GPU** with the appropriate drivers installed.
- **NVIDIA Container Toolkit** to enable GPU support in Docker. Follow the [NVIDIA Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

### **Steps**

1. **Pull the Docker Image**

   ```bash
   docker pull yoeven/insanely-fast-whisper-api:latest
   ```

2. **Run the Docker Container with GPU Support**

   ```bash
   docker run --gpus all -d \
     -p 8000:8000 \
     --name insanely-fast-whisper-api \
     -e ADMIN_KEY=<your_admin_key> \
     -e HF_TOKEN=<your_hf_token> \
     yoeven/insanely-fast-whisper-api:latest
   ```

   **Explanation:**
   - `--gpus all`: Enables all available GPUs for the container.
   - `-d`: Runs the container in detached mode.
   - `-p 8000:8000`: Maps port `8000` of the container to port `8000` on the host machine.
   - `--name insanely-fast-whisper-api`: Assigns a name to the container for easier management.
   - `-e ADMIN_KEY=<your_admin_key>`: Sets the `ADMIN_KEY` environment variable for admin authentication.
   - `-e HF_TOKEN=<your_hf_token>`: Sets the `HF_TOKEN` environment variable required for speaker diarization.

3. **Verify the Container is Running**

   ```bash
   docker ps
   ```

   You should see the `insanely-fast-whisper-api` container listed and running.

4. **Access the API**

   Open your browser or use `curl` to interact with the API at `http://localhost:8000/`.

### **Stopping and Removing the Container**

- **Stop the Container:**

  ```bash
  docker stop insanely-fast-whisper-api
  ```

- **Remove the Container:**

  ```bash
  docker rm insanely-fast-whisper-api
  ```

## Running with Podman

Podman is an alternative to Docker that offers similar functionalities with a daemonless architecture. To run the application using Podman with GPU support, follow these steps:

### **Prerequisites**
- **Podman** installed on your machine. Refer to the [official Podman installation guide](https://podman.io/getting-started/installation) if you haven't installed it yet.
- **NVIDIA GPU** with the appropriate drivers installed.
- **NVIDIA Container Toolkit** configured for Podman. Podman uses the same NVIDIA Container Toolkit as Docker for GPU support. Follow the [NVIDIA Container Toolkit installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) and ensure it's set up for use with Podman.

### **Steps**

1. **Pull the Docker Image Using Podman**

   ```bash
   podman pull docker.io/yoeven/insanely-fast-whisper-api:latest
   ```

2. **Run the Podman Container with GPU Support**

   ```bash
   podman run --rm -d \
     --gpus all \
     -p 8000:8000 \
     --name insanely-fast-whisper-api \
     -e ADMIN_KEY=<your_admin_key> \
     -e HF_TOKEN=<your_hf_token> \
     docker.io/yoeven/insanely-fast-whisper-api:latest
   ```

   **Explanation:**
   - `--rm`: Automatically removes the container when it exits.
   - `--gpus all`: Enables all available GPUs for the container.
   - `-d`: Runs the container in detached mode.
   - `-p 8000:8000`: Maps port `8000` of the container to port `8000` on the host machine.
   - `--name insanely-fast-whisper-api`: Assigns a name to the container for easier management.
   - `-e ADMIN_KEY=<your_admin_key>`: Sets the `ADMIN_KEY` environment variable for admin authentication.
   - `-e HF_TOKEN=<your_hf_token>`: Sets the `HF_TOKEN` environment variable required for speaker diarization.
   - `docker.io/yoeven/insanely-fast-whisper-api:latest`: Specifies the image to use.

3. **Verify the Container is Running**

   ```bash
   podman ps
   ```

   You should see the `insanely-fast-whisper-api` container listed and running.

4. **Access the API**

   Open your browser or use `curl` to interact with the API at `http://localhost:8000/`.

### **Stopping the Podman Container**

Since we used the `--rm` flag, the container will be automatically removed when stopped. To stop the container:

```bash
podman stop insanely-fast-whisper-api
```

## Deploying to Fly

- Ensure you already have access to Fly GPUs.
- Clone the project locally and navigate to the root directory.
- Rename the `app` name in the `fly.toml` file if desired.
- Remove `image = 'yoeven/insanely-fast-whisper-api:latest'` from `fly.toml` only if you want to rebuild the image from the `Dockerfile`.

[Install Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) if you haven't already.

**Initial Deployment:**

Only need to run this the first time you launch a new Fly app:

```bash
fly launch
```

- Fly will prompt: `Would you like to copy its configuration to the new app? (y/N)`. Type `y` to copy the configuration from the repository.
- Fly will prompt: `Do you want to tweak these settings before proceeding?` If you have nothing to adjust, type `n` to proceed and deploy.

The first deployment will take some time since the image is large. Subsequent deployments will be faster.

**Setting Up Secrets:**

Run the following to set up speaker diarization or an auth token to secure your API:

```bash
fly secrets set ADMIN_KEY=<your_token> HF_TOKEN=<your_hf_key>
```

Verify that the secrets exist by running:

```bash
fly secrets list
```

**Obtaining Hugging Face Token:**

To get the Hugging Face token for speaker diarization, follow these steps:

1. Accept the user conditions for [`pyannote/segmentation-3.0`](https://hf.co/pyannote/segmentation-3.0).
2. Accept the user conditions for [`pyannote/speaker-diarization-3.1`](https://hf.co/pyannote/speaker-diarization-3.1).
3. Create an access token at [`hf.co/settings/tokens`](https://hf.co/settings/tokens).

**Accessing the API:**

Your API should be accessible at:

```
https://insanely-fast-whisper-api.fly.dev
```

**Viewing Logs:**

Run the following command to view real-time logs of your Fly machine:

```bash
fly logs -a insanely-fast-whisper-api
```

## Deploying to other cloud providers
Since this is a dockerized app, you can deploy it to any cloud provider that supports docker and GPUs with a few config tweaks.

## Fully managed and scalable API 
[JigsawStack](https://jigsawstack.com) provides a bunch of powerful APIs for various use cases while keeping costs low. This project is available as a fully managed API [here](https://jigsawstack.com/speech-to-text) with enhanced cloud scalability for cost efficiency and high uptime. Sign up [here](https://jigsawstack.com) for free!


## API usage

### Authentication
If you have set up the `ADMIN_KEY` environment secret, you'll need to pass `x-admin-api-key` in the header with the value of the key you previously set.


### Endpoints
#### Base URL
If deployed on Fly, the base URL should look something like this:
```
https://{app_name}.fly.dev/{path}
```
Depending on the cloud provider you deploy to, the base URL will be different.

#### **POST** `/`
Transcribe or translate audio into text
##### Body params (JSON)
| **Name**             | **Value**                                                                                     |
|----------------------|-----------------------------------------------------------------------------------------------|
| `url` *(Required)*   | URL of the audio                                                                                |
| `task`               | `transcribe`, `translate`<br>**Default:** `transcribe`                                       |
| `language`           | `None`, `en`, [other languages](https://huggingface.co/openai/whisper-large-v3)<br>**Default:** `None` (Auto detects language) |
| `batch_size`         | Number of parallel batches you want to compute. Reduce if you face OOMs.<br>**Default:** `64` |
| `timestamp`          | `chunk`, `word`<br>**Default:** `chunk`                                                       |
| `diarise_audio`      | Diarize the audio clips by speaker. You will need to set `HF_TOKEN`.<br>**Default:** `false` |
| `webhook`            | Webhook `POST` call on completion or error.<br>**Default:** `None`                           |
| `webhook.url`        | URL to send the webhook                                                                        |
| `webhook.header`     | Headers to send with the webhook                                                               |
| `is_async`           | Run task in background and sends results to webhook URL.<br>`true`, `false`<br>**Default:** `false` |
| `managed_task_id`    | Custom Task ID used to reference an ongoing task.<br>**Default:** `uuid() v4` will be generated for each transcription task |

#### **GET** `/tasks`
Get all active transcription tasks, both async background tasks and ongoing tasks

#### **GET** `/status/{task_id}`
Get the status of a task, completed tasks will be removed from the list which may throw an error

#### **DELETE** `/cancel/{task_id}`
Cancel async background task. Only transcription jobs created with `is_async` set to `true` can be cancelled.


## Running Locally

```bash
# Clone the repository
git clone https://github.com/jigsawstack/insanely-fast-whisper-api.git

# Change the working directory
cd insanely-fast-whisper-api

# Install PyTorch and related packages
pip3 install torch torchvision torchaudio

# Upgrade wheel and install required packages for FlashAttention
pip3 install -U wheel && pip install ninja packaging

# Install FlashAttention without build isolation
pip3 install flash-attn --no-build-isolation

# Generate updated requirements.txt if you want to use other management tools (Optional)
poetry export --output requirements.txt

# Get the path of Python interpreter
which python3

# Setup virtual environment using Poetry
poetry env use /full/path/to/python

# Install the project dependencies
poetry install

# Run the application with Uvicorn
uvicorn app.app:app --reload
```

## Extra
### Shutting down fly machine programmatically
Fly machines are charged by the second and might take up to 15 minutes of idling before they decide to shut themselves down. You can shut down the machine when you're done with the API to save costs by sending a `POST` request to the following endpoint:
```
https://api.machines.dev/v1/apps/<app_name>/machines/<machine_id>/stop
```
Authorization header:
```
Authorization Bearer <fly_token>
```
Lear more [here](https://fly.io/docs/machines/api/machines-resource/)

## Acknowledgements

1. [Vaibhav Srivastav](https://github.com/Vaibhavs10) for writing a huge chunk of the code and the CLI version of this project.
2. [OpenAI Whisper](https://huggingface.co/openai/whisper-large-v3) 


## JigsawStack
This project is part of [JigsawStack](https://jigsawstack.com) - A suite of powerful and developer friendly APIs for various use cases while keeping costs low. Sign up [here](https://jigsawstack.com) for free!
