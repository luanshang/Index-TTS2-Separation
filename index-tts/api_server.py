import html
import json
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Optional, List

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import argparse
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, "indextts"))

# 解析命令行参数
parser = argparse.ArgumentParser(
    description="IndexTTS API Server",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose mode")
parser.add_argument("--port", type=int, default=10080, help="Port to run the API server on")
parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the API server on")
parser.add_argument("--model_dir", type=str, default="./checkpoints", help="Model checkpoints directory")
parser.add_argument("--fp16", action="store_true", default=False, help="Use FP16 for inference if available")
parser.add_argument("--deepspeed", action="store_true", default=False, help="Use DeepSpeed to accelerate if available")
parser.add_argument("--cuda_kernel", action="store_true", default=False, help="Use CUDA kernel for inference if available")
cmd_args = parser.parse_args()

# 检查模型目录
if not os.path.exists(cmd_args.model_dir):
    print(f"Model directory {cmd_args.model_dir} does not exist. Please download the model first.")
    sys.exit(1)

for file in [
    "bpe.model",
    "gpt.pth",
    "config.yaml",
    "s2mel.pth",
    "wav2vec2bert_stats.pt"
]:
    file_path = os.path.join(cmd_args.model_dir, file)
    if not os.path.exists(file_path):
        print(f"Required file {file_path} does not exist. Please download it.")
        sys.exit(1)

# 导入 TTS 模型
from indextts.infer_v2 import IndexTTS2
from tools.i18n.i18n import I18nAuto

i18n = I18nAuto(language="Auto")

# 初始化 TTS 模型
tts = None
tts_error = None
print("正在加载 IndexTTS2 模型...")
try:
    tts = IndexTTS2(
        model_dir=cmd_args.model_dir,
        cfg_path=os.path.join(cmd_args.model_dir, "config.yaml"),
        use_fp16=cmd_args.fp16,
        use_deepspeed=cmd_args.deepspeed,
        use_cuda_kernel=cmd_args.cuda_kernel,
    )
    print("模型加载完成！")
except Exception as e:
    import traceback
    tts_error = str(e)
    traceback.print_exc()
    print(f"警告: 模型加载失败: {tts_error}")
    print("服务器将继续启动，但某些功能可能不可用。")

# 创建必要的目录
os.makedirs("outputs/tasks", exist_ok=True)
os.makedirs("voices", exist_ok=True)

# FastAPI 应用
app = FastAPI(title="IndexTTS API Server", version="2.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
if os.path.exists("outputs"):
    app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")
if os.path.exists("voices"):
    app.mount("/voices", StaticFiles(directory="voices"), name="voices")
if os.path.exists("examples"):
    app.mount("/examples", StaticFiles(directory="examples"), name="examples")

# 情感控制选项
EMO_CHOICES_ALL = [
    i18n("与音色参考音频相同"),
    i18n("使用情感参考音频"),
    i18n("使用情感向量控制"),
    i18n("使用情感描述文本控制")
]
EMO_CHOICES_OFFICIAL = EMO_CHOICES_ALL[:-1]

# 请求/响应模型
class GenerateRequest(BaseModel):
    text: str
    emo_control_method: int = 0
    emo_ref_path: Optional[str] = None
    emo_weight: float = 0.65
    emo_text: Optional[str] = None
    emo_random: bool = False
    emo_vector: Optional[List[float]] = None
    max_text_tokens_per_segment: int = 120
    # 高级参数
    do_sample: bool = True
    top_p: float = 0.8
    top_k: int = 30
    temperature: float = 0.8
    length_penalty: float = 0.0
    num_beams: int = 3
    repetition_penalty: float = 10.0
    max_mel_tokens: int = 1500

class SegmentPreviewRequest(BaseModel):
    text: str
    max_text_tokens_per_segment: int = 120

class SegmentPreviewResponse(BaseModel):
    segments: List[dict]

class SaveVoiceRequest(BaseModel):
    voice_name: str

class VoiceListResponse(BaseModel):
    voices: List[str]

# API 路由
@app.get("/")
async def root():
    if tts is None:
        return {
            "message": "IndexTTS API Server",
            "version": "2.0.0",
            "status": "error",
            "error": tts_error or "模型未加载"
        }
    return {
        "message": "IndexTTS API Server",
        "version": "2.0.0",
        "model_version": getattr(tts, 'model_version', None) or "2.0",
        "status": "ready"
    }

@app.get("/api/model/info")
async def get_model_info():
    """获取模型信息"""
    if tts is None:
        raise HTTPException(
            status_code=503, 
            detail=f"模型未加载: {tts_error or '未知错误'}"
        )
    
    try:
        model_version = getattr(tts, 'model_version', None) or "2.0"
        
        max_text_tokens = 300
        max_mel_tokens = 2000
        
        if hasattr(tts, 'cfg') and tts.cfg:
            if hasattr(tts.cfg, 'gpt') and tts.cfg.gpt:
                max_text_tokens = getattr(tts.cfg.gpt, 'max_text_tokens', 300)
                max_mel_tokens = getattr(tts.cfg.gpt, 'max_mel_tokens', 2000)
        
        return {
            "model_version": model_version,
            "max_text_tokens": max_text_tokens,
            "max_mel_tokens": max_mel_tokens,
            "emo_choices": EMO_CHOICES_OFFICIAL,
            "emo_choices_all": EMO_CHOICES_ALL
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {str(e)}")

@app.post("/api/upload/voice")
async def upload_voice(file: UploadFile = File(...)):
    """上传音色参考音频"""
    try:
        # 保存上传的文件
        file_path = os.path.join("voices", f"temp_{int(time.time())}_{file.filename}")
        os.makedirs("voices", exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "success": True,
            "file_path": file_path,
            "filename": file.filename,
            "url": f"/voices/{os.path.basename(file_path)}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.post("/api/voice/save")
async def save_voice(
    voice_name: str = Form(...),
    file: UploadFile = File(...)
):
    """保存音色到 voices 目录"""
    if not voice_name or voice_name.strip() == "":
        raise HTTPException(status_code=400, detail="请输入音色名称！")
    
    try:
        # 确保 voices 目录存在
        os.makedirs("voices", exist_ok=True)
        
        # 获取文件扩展名
        ext = os.path.splitext(file.filename)[1] or ".wav"
        
        # 清理文件名
        safe_name = "".join(c for c in voice_name if c.isalnum() or c in (' ', '-', '_')).strip()
        save_path = os.path.join("voices", f"{safe_name}{ext}")
        
        # 保存文件
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "success": True,
            "message": f"音色已保存：{safe_name}{ext}",
            "filename": f"{safe_name}{ext}",
            "url": f"/voices/{safe_name}{ext}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败：{str(e)}")

@app.get("/api/voice/list")
async def get_voice_list():
    """获取已保存的音色列表"""
    try:
        voices_dir = "voices"
        if not os.path.exists(voices_dir):
            os.makedirs(voices_dir, exist_ok=True)
            return VoiceListResponse(voices=[])
        
        try:
            # 支持常见的音频格式，也包括 .pt 文件（可能是误用的扩展名）
            voices = [f for f in os.listdir(voices_dir) 
                     if os.path.isfile(os.path.join(voices_dir, f)) 
                     and f.lower().endswith(('.wav', '.mp3', '.flac', '.ogg', '.m4a', '.pt'))]
            return VoiceListResponse(voices=sorted(voices))
        except PermissionError:
            raise HTTPException(status_code=500, detail="没有权限访问 voices 目录")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取音色列表失败: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取音色列表失败: {str(e)}")

@app.get("/api/voice/{filename}")
async def get_voice_file(filename: str):
    """获取音色文件"""
    file_path = os.path.join("voices", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)

@app.post("/api/segments/preview")
async def preview_segments(request: SegmentPreviewRequest):
    """预览文本分句结果"""
    if tts is None:
        raise HTTPException(
            status_code=503, 
            detail=f"模型未加载: {tts_error or '未知错误'}"
        )
    
    try:
        if not request.text or len(request.text) == 0:
            return SegmentPreviewResponse(segments=[])
        
        text_tokens_list = tts.tokenizer.tokenize(request.text)
        segments = tts.tokenizer.split_segments(
            text_tokens_list,
            max_text_tokens_per_segment=int(request.max_text_tokens_per_segment)
        )
        
        data = []
        for i, s in enumerate(segments):
            segment_str = ''.join(s)
            tokens_count = len(s)
            data.append({
                "index": i,
                "text": segment_str,
                "tokens": tokens_count
            })
        
        return SegmentPreviewResponse(segments=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")

@app.post("/api/generate")
async def generate_audio(
    text: str = Form(...),
    spk_audio_path: str = Form(...),
    emo_control_method: int = Form(0),
    emo_ref_path: Optional[str] = Form(None),
    emo_weight: float = Form(0.65),
    emo_text: Optional[str] = Form(None),
    emo_random: bool = Form(False),
    vec1: float = Form(0.0),
    vec2: float = Form(0.0),
    vec3: float = Form(0.0),
    vec4: float = Form(0.0),
    vec5: float = Form(0.0),
    vec6: float = Form(0.0),
    vec7: float = Form(0.0),
    vec8: float = Form(0.0),
    max_text_tokens_per_segment: int = Form(120),
    do_sample: bool = Form(True),
    top_p: float = Form(0.8),
    top_k: int = Form(30),
    temperature: float = Form(0.8),
    length_penalty: float = Form(0.0),
    num_beams: int = Form(3),
    repetition_penalty: float = Form(10.0),
    max_mel_tokens: int = Form(1500)
):
    """生成语音"""
    if tts is None:
        raise HTTPException(
            status_code=503, 
            detail=f"模型未加载: {tts_error or '未知错误'}"
        )
    
    try:
        # 验证音色文件路径
        if not os.path.exists(spk_audio_path):
            raise HTTPException(status_code=400, detail=f"音色参考音频不存在: {spk_audio_path}")
        
        # 处理情感控制方式（与 webui 保持一致）
        if emo_control_method == 0:  # 与音色参考音频相同
            emo_ref_path = None  # remove external reference audio
        if emo_control_method == 1:  # 使用情感参考音频
            if emo_ref_path and not os.path.exists(emo_ref_path):
                raise HTTPException(status_code=400, detail=f"情感参考音频不存在: {emo_ref_path}")
        if emo_control_method == 2:  # 使用情感向量控制
            emo_ref_path = None
            emo_vector = [vec1, vec2, vec3, vec4, vec5, vec6, vec7, vec8]
            emo_vector = tts.normalize_emo_vec(emo_vector, apply_bias=True)
        else:
            # don't use the emotion vector inputs for the other modes
            emo_vector = None
        
        # 处理情感文本
        if emo_text == "" or (emo_text and emo_text.strip() == ""):
            # erase empty emotion descriptions; `infer()` will then automatically use the main prompt
            emo_text = None
        
        use_emo_text = (emo_control_method == 3)
        
        # 生成输出路径
        output_path = os.path.join("outputs", f"spk_{int(time.time())}.wav")
        os.makedirs("outputs", exist_ok=True)
        
        # 生成参数
        generation_kwargs = {
            "do_sample": bool(do_sample),
            "top_p": float(top_p),
            "top_k": int(top_k) if int(top_k) > 0 else None,
            "temperature": float(temperature),
            "length_penalty": float(length_penalty),
            "num_beams": num_beams,
            "repetition_penalty": float(repetition_penalty),
            "max_mel_tokens": int(max_mel_tokens),
        }
        
        print(f"生成音频: text={text[:50]}..., spk={spk_audio_path}, emo_mode={emo_control_method}")
        print(f"情感控制参数: emo_ref_path={emo_ref_path}, emo_weight={emo_weight}, emo_vector={emo_vector}")
        print(f"生成参数: {generation_kwargs}")
        
        # 调用 TTS 生成
        try:
            result = tts.infer(
                spk_audio_prompt=spk_audio_path,
                text=text,
                output_path=output_path,
                emo_audio_prompt=emo_ref_path,
                emo_alpha=emo_weight,
                emo_vector=emo_vector,
                use_emo_text=use_emo_text,
                emo_text=emo_text,
                use_random=emo_random,
                verbose=cmd_args.verbose,
                max_text_tokens_per_segment=int(max_text_tokens_per_segment),
                **generation_kwargs
            )
            print(f"生成完成，返回值: {result}")
            print(f"输出文件路径: {output_path}")
            print(f"文件是否存在: {os.path.exists(output_path)}")
        except Exception as e:
            import traceback
            print(f"TTS infer 调用失败: {str(e)}")
            traceback.print_exc()
            raise
        
        # 检查结果（infer 可能返回路径或 None）
        if output_path and os.path.exists(output_path):
            print(f"音频文件已生成: {output_path}")
        else:
            error_msg = f"音频生成失败: 文件不存在 {output_path}"
            if result:
                error_msg += f", infer 返回值: {result}"
            raise HTTPException(status_code=500, detail=error_msg)
        
        return {
            "success": True,
            "output_path": output_path,
            "filename": os.path.basename(output_path),
            "url": f"/outputs/{os.path.basename(output_path)}"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")

@app.get("/api/examples/list")
async def get_examples_list():
    """获取示例列表"""
    try:
        examples_dir = "examples"
        example_file = os.path.join(examples_dir, "cases.jsonl")
        
        # 如果 examples 目录不存在，返回空列表
        if not os.path.exists(examples_dir):
            return {"examples": []}
        
        # 如果示例文件不存在，返回空列表
        if not os.path.exists(example_file):
            return {"examples": []}
        
        examples = []
        try:
            with open(example_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        example = json.loads(line)
                    except json.JSONDecodeError as e:
                        # 跳过格式错误的行，继续处理下一行
                        print(f"警告: 第 {line_num} 行 JSON 格式错误: {e}")
                        continue
                    
                    # 构建示例数据
                    emo_audio_path = None
                    if example.get("emo_audio"):
                        emo_audio_path = os.path.join(examples_dir, example["emo_audio"])
                        if os.path.exists(emo_audio_path):
                            emo_audio_path = f"/examples/{example['emo_audio']}"
                        else:
                            emo_audio_path = None
                    
                    prompt_audio = example.get("prompt_audio", "sample_prompt.wav")
                    prompt_audio_path = os.path.join(examples_dir, prompt_audio)
                    if os.path.exists(prompt_audio_path):
                        prompt_audio_path = f"/examples/{prompt_audio}"
                    else:
                        prompt_audio_path = None
                    
                    examples.append({
                        "prompt_audio": prompt_audio_path,
                        "emo_mode": example.get("emo_mode", 0),
                        "text": example.get("text", ""),
                        "emo_audio": emo_audio_path,
                        "emo_weight": example.get("emo_weight", 1.0),
                        "emo_text": example.get("emo_text", ""),
                        "emo_vec": [
                            example.get("emo_vec_1", 0),
                            example.get("emo_vec_2", 0),
                            example.get("emo_vec_3", 0),
                            example.get("emo_vec_4", 0),
                            example.get("emo_vec_5", 0),
                            example.get("emo_vec_6", 0),
                            example.get("emo_vec_7", 0),
                            example.get("emo_vec_8", 0),
                        ]
                    })
        except PermissionError:
            raise HTTPException(status_code=500, detail="没有权限读取示例文件")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取示例文件失败: {str(e)}")
        
        return {"examples": examples}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取示例失败: {str(e)}")

@app.get("/outputs/{filename}")
async def get_output_file(filename: str):
    """获取生成的音频文件"""
    file_path = os.path.join("outputs", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path, media_type="audio/wav")

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("IndexTTS API Server")
    print(f"{'='*60}")
    print(f"服务地址: http://{cmd_args.host}:{cmd_args.port}")
    print(f"模型目录: {cmd_args.model_dir}")
    print(f"FP16: {cmd_args.fp16}")
    print(f"DeepSpeed: {cmd_args.deepspeed}")
    print(f"CUDA Kernel: {cmd_args.cuda_kernel}")
    print(f"{'='*60}\n")
    
    uvicorn.run(
        app,
        host=cmd_args.host,
        port=cmd_args.port,
        log_level="info" if cmd_args.verbose else "warning"
    )

