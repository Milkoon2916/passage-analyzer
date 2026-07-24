import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .prompt import build_system_prompt, MODEL
from .schemas import AnalysisResponse
from .render import render_pdf

app = FastAPI(title="영어 지문 구문분석 자동 생성기")
STATIC_DIR = Path(__file__).parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

OUTPUT_DIR = Path(tempfile.gettempdir()) / "passage-analyzer-outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

MAX_TOKENS = 20000  # Gemini 2.5 Pro의 출력 토큰 한도는 넉넉한 편이지만,
                     # 지문이 길어서 JSON이 잘리면 이 값을 더 올리세요.


class PromptConfigResponse(BaseModel):
    system_prompt: str
    model: str
    max_tokens: int


@app.get("/prompt-config", response_model=PromptConfigResponse)
def prompt_config():
    """브라우저가 Gemini API를 '직접' 호출할 때 쓸 시스템 프롬프트/모델명을 공개 제공.
    API 키는 서버에 전혀 없음 -- 사용자가 자기 키로 브라우저에서 바로 호출한다."""
    return PromptConfigResponse(
        system_prompt=build_system_prompt(),
        model=MODEL,
        max_tokens=MAX_TOKENS,
    )


class RenderResponse(BaseModel):
    job_id: str
    download_url: str


@app.post("/render", response_model=RenderResponse)
def render(analysis: AnalysisResponse):
    """브라우저에서 이미 Gemini로 분석까지 마친 JSON만 받아서 PDF로 렌더링한다.
    이 엔드포인트는 LLM을 호출하지 않으므로 API 키가 전혀 필요 없다 -- 공개해도 비용 위험 없음."""
    job_id = str(uuid.uuid4())
    pdf_path = OUTPUT_DIR / f"{job_id}.pdf"
    render_pdf(analysis, str(pdf_path))
    return RenderResponse(job_id=job_id, download_url=f"/download/{job_id}")


@app.get("/download/{job_id}")
def download(job_id: str):
    pdf_path = OUTPUT_DIR / f"{job_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(pdf_path, media_type="application/pdf", filename="구문분석_상세분석본.pdf")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")
