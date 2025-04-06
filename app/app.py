import os
from fastapi import (
    FastAPI,
    Header,
    HTTPException,
    Body,
    BackgroundTasks,
    Request,
)
from fastapi.responses import JSONResponse
from fastapi import File, UploadFile
import tempfile
import logging

# Configure logging to display debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
from pydantic import BaseModel
import torch
from transformers import pipeline
from .diarization_pipeline import diarize
import requests
import asyncio
import uuid


admin_key = os.environ.get(
    "ADMIN_KEY",
)

hf_token = os.environ.get(
    "HF_TOKEN",
)

# fly runtime env https://fly.io/docs/machines/runtime-environment
fly_machine_id = os.environ.get(
    "FLY_MACHINE_ID",
)

pipe = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-large-v3",
    torch_dtype=torch.float16,
    device="cuda:0",
    model_kwargs=({"attn_implementation": "flash_attention_2"}),
)

app = FastAPI()
loop = asyncio.get_event_loop()
running_tasks = {}


class WebhookBody(BaseModel):
    url: str
    header: dict[str, str] = {}


def process(
    url: str,
    task: str,
    language: str,
    batch_size: int,
    timestamp: str,
    diarise_audio: bool,
    webhook: WebhookBody | None = None,
    task_id: str | None = None,
):
    errorMessage: str | None = None
    temp_file = None
    logger.debug(f"Processing task {task_id}: url={url}, task={task}, language={language}, batch_size={batch_size}, timestamp={timestamp}, diarise_audio={diarise_audio}")
    try:
        if not url.startswith("http") and os.path.exists(url):
            temp_file = url  # Store the temp file path for later deletion

        generate_kwargs = {
            "task": task,
            "language": None if language == "None" else language,
        }

        outputs = pipe(
            url,
            chunk_length_s=30,
            batch_size=batch_size,
            generate_kwargs=generate_kwargs,
            return_timestamps="word" if timestamp == "word" else True,
        )

        if diarise_audio is True:
            if hf_token is None:
                raise Exception("Missing Hugging Face Token")
            speakers_transcript = diarize(
                hf_token,
                url,
                outputs,
            )
            outputs["speakers"] = speakers_transcript
        logger.debug(f"Completed task {task_id}: outputs={outputs}")
    except asyncio.CancelledError:
        errorMessage = "Task Cancelled"
        logger.warning(f"Task {task_id} was cancelled.")
    except Exception as e:
        logger.error(f"Error in task {task_id}: {str(e)}")
        errorMessage = str(e)

    if task_id is not None:
        del running_tasks[task_id]

    if webhook is not None:
        webhookResp = (
            {"output": outputs, "status": "completed", "task_id": task_id}
            if errorMessage is None
            else {"error": errorMessage, "status": "error", "task_id": task_id}
        )

        if fly_machine_id is not None:
            webhookResp["fly_machine_id"] = fly_machine_id

        requests.post(
            webhook.url,
            headers=webhook.header,
            json=(webhookResp),
        )

    if errorMessage is not None:
        raise Exception(errorMessage)

    if temp_file:
        try:
            os.remove(temp_file)
            logger.debug(f"Deleted temporary file: {temp_file}")
        except Exception as e:
            logger.error(f"Failed to delete temporary file {temp_file}: {e}")
            print(f"Failed to delete temp file {temp_file}: {e}")

    return outputs


@app.middleware("http")
async def admin_key_auth_check(request: Request, call_next):
    if admin_key is not None:
        if ("x-admin-api-key" not in request.headers) or (
            request.headers["x-admin-api-key"] != admin_key
        ):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    response = await call_next(request)
    return response


@app.post("/")
def root(
    url: str = Body(None),  # Make `url` optional
    file: UploadFile = File(None),  # Add this line
    task: str = Body(default="transcribe", enum=["transcribe", "translate"]),
    language: str = Body(default="None"),
    batch_size: int = Body(default=64),
    timestamp: str = Body(default="chunk", enum=["chunk", "word"]),
    diarise_audio: bool = Body(
        default=False,
    ),
    webhook: WebhookBody | None = None,
    is_async: bool = Body(default=False),
    managed_task_id: str | None = Body(default=None),
):
    if not url and not file:
        raise HTTPException(status_code=400, detail="Either URL or file must be provided")

    if file:
        try:
            logger.debug(f"Received file: {file.filename}")
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
                tmp.write(file.file.read())
                tmp_path = tmp.name
            logger.debug(f"Saved uploaded file to temporary path: {tmp_path}")
            processing_url = tmp_path
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    else:
        logger.debug(f"Received URL: {url}")
        processing_url = url

    logger.debug(f"Processing URL: {processing_url}")

    if not processing_url.lower().startswith("http") and not os.path.exists(processing_url):
        raise HTTPException(status_code=400, detail="Invalid URL or file path")

    logger.debug("Processing URL validation passed.")

    if diarise_audio is True and hf_token is None:
        raise HTTPException(status_code=500, detail="Missing Hugging Face Token")

    if is_async is True and webhook is None:
        raise HTTPException(status_code=400, detail="Webhook is required for async tasks")

    task_id = managed_task_id if managed_task_id is not None else str(uuid.uuid4())

    try:
        logger.debug(f"Starting {'asynchronous' if is_async else 'synchronous'} processing for task_id: {task_id}")
        if is_async is True:
            backgroundTask = asyncio.ensure_future(
                loop.run_in_executor(
                    None,
                    process,
                    processing_url,  # Correctly using `processing_url`
                    task,
                    language,
                    batch_size,
                    timestamp,
                    diarise_audio,
                    webhook,
                    task_id,
                )
            )
            running_tasks[task_id] = backgroundTask
            resp = {
                "detail": "Task is being processed in the background",
                "status": "processing",
                "task_id": task_id,
            }
        else:
            running_tasks[task_id] = None
            outputs = process(
                processing_url,  # Changed from `url` to `processing_url`
                task,
                language,
                batch_size,
                timestamp,
                diarise_audio,
                webhook,
                task_id,
            )
            resp = {
                "output": outputs,
                "status": "completed",
                "task_id": task_id,
            }
        if fly_machine_id is not None:
            resp["fly_machine_id"] = fly_machine_id
        return resp
    except Exception as e:
        logger.error(f"Exception during processing for task_id {task_id}: {e}")
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks")
def tasks():
    return {"tasks": list(running_tasks.keys())}


@app.get("/status/{task_id}")
def status(task_id: str):
    if task_id not in running_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = running_tasks[task_id]

    if task is None:
        return {"status": "processing"}
    elif task.done() is False:
        return {"status": "processing"}
    else:
        return {"status": "completed", "output": task.result()}


@app.delete("/cancel/{task_id}")
def cancel(task_id: str):
    if task_id not in running_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = running_tasks[task_id]
    if task is None:
        return HTTPException(status_code=400, detail="Not a background task")
    elif task.done() is False:
        task.cancel()
        del running_tasks[task_id]
        return {"status": "cancelled"}
    else:
        return {"status": "completed", "output": task.result()}
