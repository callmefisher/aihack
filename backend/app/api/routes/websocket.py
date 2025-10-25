from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List
import json
import httpx
import asyncio
import subprocess
import tempfile
import base64
import os
from pathlib import Path
from app.core.config import settings

router = APIRouter()

# WebSocket配置
WEBSOCKET_HEARTBEAT_TIMEOUT = 200000  # 心跳超时时间（秒）
WEBSOCKET_PING_INTERVAL = 200000  # ping间隔时间（秒）


class QiniuTTSService:
    """七牛云TTS服务"""
    
    def __init__(self):
        self.api_url = "https://openai.qiniu.com/v1/voice/tts"
        api_key = settings.QINIU_API_KEY
        if isinstance(api_key, bytes):
            api_key = api_key.decode('utf-8')
        self.api_token = api_key.replace('Bearer ', '').strip() if api_key else ""
        self.background_music_path = Path(__file__).parent.parent.parent.parent / "ht.mp3"
    
    def mix_audio_with_background(self, tts_audio_base64: str) -> str:
        """
        使用ffmpeg将TTS音频与背景音乐混合
        
        Args:
            tts_audio_base64: base64编码的TTS音频数据
            
        Returns:
            混合后的base64编码音频数据
        """
        try:
            # 检查背景音乐文件是否存在且可读
            if not self.background_music_path.exists():
                print(f"背景音乐文件不存在: {self.background_music_path}，跳过ffmpeg混合，返回原始TTS音频")
                return tts_audio_base64
            
            if not self.background_music_path.is_file():
                print(f"背景音乐路径不是文件: {self.background_music_path}，跳过ffmpeg混合，返回原始TTS音频")
                return tts_audio_base64
            
            if not os.access(self.background_music_path, os.R_OK):
                print(f"背景音乐文件无读取权限: {self.background_music_path}，跳过ffmpeg混合，返回原始TTS音频")
                return tts_audio_base64
            
            print(f"背景音乐文件检查通过: {self.background_music_path}")
            
            # 检查ffmpeg是否可用
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"ffmpeg未安装或不可用: {str(e)}，跳过ffmpeg混合，返回原始TTS音频")
                return tts_audio_base64
            
            # 解码TTS音频
            tts_audio_data = base64.b64decode(tts_audio_base64)
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tts_file:
                tts_file.write(tts_audio_data)
                tts_file_path = tts_file.name
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as output_file:
                output_file_path = output_file.name
            
            try:
                # 使用ffmpeg混合音频
                # -i: 输入文件
                # -filter_complex: 复杂滤镜，混合两个音频流
                # amix=inputs=2: 混合2个音频输入
                # duration=longest: 输出长度为最长输入的长度
                # [0:a]: 第一个输入的音频流 (TTS)
                # [1:a]: 第二个输入的音频流 (背景音乐)
                # volume=1.0: TTS音量保持不变
                # volume=0.3: 背景音乐音量降低到30%
                cmd = [
                    'ffmpeg',
                    '-i', tts_file_path,
                    '-i', str(self.background_music_path),
                    '-filter_complex', '[0:a]volume=1.0[a1];[1:a]volume=0.3[a2];[a1][a2]amix=inputs=2:duration=longest',
                    '-y',  # 覆盖输出文件
                    output_file_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    print(f"ffmpeg混合失败 (返回码: {result.returncode})")
                    print(f"ffmpeg错误输出: {result.stderr}")
                    print(f"跳过ffmpeg混合，返回原始TTS音频")
                    return tts_audio_base64
                
                # 读取混合后的音频并编码为base64
                with open(output_file_path, 'rb') as f:
                    mixed_audio_data = f.read()
                
                mixed_audio_base64 = base64.b64encode(mixed_audio_data).decode('utf-8')
                print(f"音频混合成功: TTS长度={len(tts_audio_data)}, 混合后长度={len(mixed_audio_data)}")
                
                return mixed_audio_base64
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(tts_file_path)
                    os.unlink(output_file_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"音频混合过程出错: {str(e)}，返回原始TTS音频")
            return tts_audio_base64
    
    async def text_to_speech(self, text: str, sequence_number: int = 0) -> Dict[str, Any]:
        """
        调用七牛云TTS API并混合背景音乐
        
        Args:
            text: 要转换的文本
            sequence_number: 序列号，只有序列号为0（段落内第一个）时才混合背景音乐
            
        Returns:
            API响应数据（包含混合背景音乐后的音频）
        """
        print("step1 tts apitoken"+self.api_token)
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "audio": {
                "voice_type": "qiniu_zh_female_wwxkjx",
                "encoding": "mp3",
                "speed_ratio": 1.0
            },
            "request": {
                "text": text
            }
        }
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            # 获取原始TTS音频数据
            if 'data' in result:
                original_audio_base64 = result['data']
                
                # 只有序列号为0（段落内第一个）时才混合背景音乐
                if sequence_number == 0:
                    print(f"TTS生成成功，序列号为0，开始混合背景音乐...")
                    # 混合背景音乐
                    mixed_audio_base64 = self.mix_audio_with_background(original_audio_base64)
                    # 更新返回数据
                    result['data'] = mixed_audio_base64
                else:
                    print(f"TTS生成成功，序列号为{sequence_number}，跳过背景音乐混合")
            
            return result


class QiniuLLMService:
    """七牛云LLM服务"""
    
    def __init__(self):
        self.api_url = "https://openai.qiniu.com/v1/chat/completions"
        api_key = settings.QINIU_API_KEY
        if isinstance(api_key, bytes):
            api_key = api_key.decode('utf-8')
        self.api_token = api_key.replace('Bearer ', '').strip() if api_key else ""
    
    async def simplify_text_to_keywords(self, text: str) -> Dict[str, Any]:
        """
        调用七牛云LLM API将文本精简为关键字
        
        Args:
            text: 原始文本
            
        Returns:
            包含精简关键字和角色信息的字典
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        system_prompt = """你是一个专业的文本摘要助手。请将输入的文本段落精简为40个字符以内的关键字描述。
要求：
1. 如果是动漫/小说场景，需要提取场景关键词
2. 如果包含角色，必须返回角色名称、特点、性格、外貌等关键信息
3. 输出格式为JSON: {"keywords": "关键字描述", "character": "角色名称", "character_info": "角色详细信息"}
4. 如果没有明确的角色，character和character_info为空字符串
5. keywords必须精简到40个字符以内"""
        
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "model": "deepseek-v3",
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            try:
                import json as json_module
                parsed = json_module.loads(content)
                return {
                    "keywords": parsed.get("keywords", "")[:40],
                    "character": parsed.get("character", ""),
                    "character_info": parsed.get("character_info", "")
                }
            except:
                return {
                    "keywords": content[:40],
                    "character": "",
                    "character_info": ""
                }


class QiniuImageService:
    """七牛云文生图服务"""
    
    def __init__(self):
        self.api_url = "https://openai.qiniu.com/v1/images/generations"
        api_key = settings.QINIU_API_KEY
        if isinstance(api_key, bytes):
            api_key = api_key.decode('utf-8')
        self.api_token = api_key.replace('Bearer ', '').strip() if api_key else ""
        self.character_cache = {}
    
    async def _simplify_text_to_prompt(self, text: str, llm_service: 'QiniuLLMService') -> str:
        """
        将原始文本精简为关键字(人物、场景等)
        
        Args:
            text: 原始文本
            llm_service: LLM服务实例
            
        Returns:
            精简后的prompt
        """
        llm_result = await llm_service.simplify_text_to_keywords(text)
        
        keywords = llm_result.get("keywords", "")
        character = llm_result.get("character", "")
        character_info = llm_result.get("character_info", "")
        
        if character and character_info:
            self.character_cache[character] = character_info
        
        if character and character in self.character_cache:
            prompt = f"{self.character_cache[character]}, {keywords}"
        else:
            prompt = keywords
        
        return prompt[:200]
    
    async def text_to_images(self, text: str, llm_service: 'QiniuLLMService') -> Dict[str, Any]:
        """
        调用七牛云文生图API
        
        Args:
            text: 要转换的文本
            llm_service: LLM服务实例
            
        Returns:
            API响应数据，包含base64编码的图片数据
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        prompt = await self._simplify_text_to_prompt(text, llm_service)
        
        payload = {
            "model": "gemini-2.5-flash-image",
            "prompt": prompt,
            "n": 3,
            "size": "1024x1024"
        }
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            print(f"文生图 payload: {payload}")
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            print(f"文生图返回图片数量: {len(response.json()['data'])}")
            response.raise_for_status()
            return response.json()


class QiniuVideoService:
    """七牛云视频生成服务"""
    
    def __init__(self):
        self.api_url = "https://openai.qiniu.com/v1/videos/generations"
        api_key = settings.QINIU_API_KEY
        if isinstance(api_key, bytes):
            api_key = api_key.decode('utf-8')
        self.api_token = api_key.replace('Bearer ', '').strip() if api_key else ""
    
    async def generate_video(self, prompt: str, image_base64: str) -> Dict[str, Any]:
        """
        调用七牛云视频生成API
        
        Args:
            prompt: 视频生成提示词
            image_base64: base64编码的图片数据
            
        Returns:
            API响应数据，包含视频生成任务ID
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "instances": [
                {
                    "prompt": prompt,
                    "image": {
                        "bytesBase64Encoded": image_base64,
                        "mimeType": "image/png"
                    }
                }
            ],
            "parameters": {
                "generateAudio": True,
                "durationSeconds": 8,
                "sampleCount": 1
            },
            "model": "veo-3.1-fast-generate-preview"
        }
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def check_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        查询视频生成状态
        
        Args:
            video_id: 视频生成任务ID
            
        Returns:
            API响应数据，包含视频生成状态和URL
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_url}/{video_id}"
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def poll_video_status(self, video_id: str, max_attempts: int = 1500, initial_interval: float = 1.0, max_interval: float = 3.0, progress_callback=None) -> Dict[str, Any]:
        """
        周期性查询视频生成状态，直到完成（使用智能退避策略）
        
        Args:
            video_id: 视频生成任务ID
            max_attempts: 最大查询次数
            initial_interval: 初始查询间隔（秒）
            max_interval: 最大查询间隔（秒）
            progress_callback: 进度回调函数
            
        Returns:
            完成后的API响应数据
        """
        current_interval = initial_interval
        
        for attempt in range(max_attempts):
            result = await self.check_video_status(video_id)
            
            if result.get("status") == "Completed":
                return result
            elif result.get("status") == "Failed":
                raise Exception(f"视频生成失败: {result.get('message', '未知错误')}")
            
            if progress_callback:
                await progress_callback(attempt, max_attempts)
            
            await asyncio.sleep(current_interval)
            
            current_interval = min(current_interval * 1.2, max_interval)
        
        raise Exception(f"视频生成超时，已尝试 {max_attempts} 次")


qiniu_tts = QiniuTTSService()
qiniu_llm = QiniuLLMService()
qiniu_image = QiniuImageService()
qiniu_video = QiniuVideoService()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket端点，接收文本并流式返回TTS结果
    """
    await websocket.accept()
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            
            try:
                # 解析JSON数据
                message = json.loads(data)
                text = message.get("text", "")
                action = message.get("action", "tts")
                paragraph_number = message.get("paragraph_number")
                task_id = message.get("task_id")
                image_url = message.get("image_url")
                
                print(f"=== 收到WebSocket消息 ===")
                print(f"action: {action}")
                print(f"paragraph_number: {paragraph_number}")
                print(f"task_id: {task_id}")
                print(f"text_length: {len(text) if text else 0}")
                
                # 处理ping请求（心跳保活）
                if action == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "message": "心跳响应"
                    })
                    continue
                
                if not text and action not in ["video"]:
                    await websocket.send_json({
                        "type": "error",
                        "message": "文本内容不能为空"
                    })
                    continue
                
                # 处理TTS请求
                if action == "tts":
                    # 获取序列号，默认为0
                    sequence_number = message.get("sequence_number", 0)
                    
                    await websocket.send_json({
                        "type": "status",
                        "message": "开始处理TTS和图片生成...",
                        "text": text,
                        "paragraph_number": paragraph_number,
                        "sequence_number": sequence_number
                    })
                    
                    # 使用完整段落文本生成图片（只在第一个序列时生成）
                    async def generate_images_background(full_paragraph_text, para_num):
                        """后台生成图片，使用完整段落文本，不阻塞TTS返回"""
                        try:
                            print(f"开始生成图片，使用完整段落文本，长度={len(full_paragraph_text)}，段落号={para_num}")
                            image_result = await qiniu_image.text_to_images(full_paragraph_text, qiniu_llm)
                            await websocket.send_json({
                                "type": "image_result",
                                "data": image_result,
                                "text": full_paragraph_text,
                                "paragraph_number": para_num,
                                "sequence_number": 0  # 图片始终标记为序列0
                            })
                            print(f"图片生成成功，段落={para_num}")
                            
                        except httpx.TimeoutException as e:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"图片生成超时: {str(e)}",
                                "paragraph_number": para_num,
                                "sequence_number": 0
                            })
                        except httpx.HTTPError as e:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"图片生成失败: {str(e)}",
                                "paragraph_number": para_num,
                                "sequence_number": 0
                            })
                        except Exception as e:
                            await websocket.send_json({
                                "type": "error",
                                "message": f"图片生成失败: {str(e)}",
                                "paragraph_number": para_num,
                                "sequence_number": 0
                            })
                    
                    # 只在接收到段落时生成一次图片（使用完整段落文本）
                    # 传递paragraph_number作为参数避免闭包问题
                    asyncio.create_task(generate_images_background(text, paragraph_number))
                    
                    def split_text_by_punctuation(text: str) -> List[str]:
                        """
                        根据中文标点符号分割文本
                        
                        Args:
                            text: 要分割的文本
                            
                        Returns:
                            分割后的句子列表
                        """
                        import re
                        sentences = re.split(r'([。！？；])', text)
                        
                        result = []
                        for i in range(0, len(sentences) - 1, 2):
                            sentence = sentences[i]
                            if i + 1 < len(sentences):
                                punctuation = sentences[i + 1]
                                sentence += punctuation
                            
                            sentence = sentence.strip()
                            if sentence:
                                result.append(sentence)
                        
                        if len(sentences) % 2 == 1:
                            last_sentence = sentences[-1].strip()
                            if last_sentence:
                                result.append(last_sentence)
                        
                        return result
                    
                    try:
                        sentences = split_text_by_punctuation(text)
                        print(f"文本已分割为 {len(sentences)} 个句子")
                        
                        for idx, sentence in enumerate(sentences):
                            print(f"处理句子 {idx + 1}/{len(sentences)}: {sentence[:30]}...")
                            
                            try:
                                # 传递idx作为混合音乐的判断依据，只有idx=0时才会混合背景音乐
                                tts_result = await qiniu_tts.text_to_speech(sentence, sequence_number=idx)
                                
                                await websocket.send_json({
                                    "type": "tts_result",
                                    "data": tts_result,
                                    "text": sentence,
                                    "paragraph_number": paragraph_number,
                                    "sequence_number": idx,
                                    "sentence_index": idx + 1,
                                    "total_sentences": len(sentences)
                                })
                                
                                print(f"句子 {idx + 1} TTS完成")
                                
                            except httpx.HTTPError as e:
                                print(f"句子 {idx + 1} TTS失败: {str(e)}")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": f"句子 {idx + 1} TTS处理失败: {str(e)}",
                                    "paragraph_number": paragraph_number,
                                    "sequence_number": idx
                                })
                            except Exception as e:
                                print(f"句子 {idx + 1} TTS异常: {str(e)}")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": f"句子 {idx + 1} TTS处理失败: {str(e)}",
                                    "paragraph_number": paragraph_number,
                                    "sequence_number": idx
                                })
                        
                        print(f"段落 {paragraph_number} 所有句子TTS完成")
                        
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"TTS处理失败: {str(e)}",
                            "paragraph_number": paragraph_number,
                            "sequence_number": sequence_number
                        })
                
                # 处理视频生成请求
                elif action == "video":
                    print(f"=== 处理视频生成请求 ===")
                    image_base64 = message.get("image_base64", "")
                    text = message.get("text", "")
                    sequence_number = message.get("sequence_number", 0)
                    
                    print(f"image_base64_length: {len(image_base64) if image_base64 else 0}")
                    print(f"text: {text[:50] if text else 'empty'}...")
                    print(f"paragraph_number: {paragraph_number}")
                    print(f"sequence_number: {sequence_number}")
                    
                    if not image_base64:
                        print(f"❌ 图片数据为空，返回错误")
                        await websocket.send_json({
                            "type": "error",
                            "message": "图片数据不能为空",
                            "paragraph_number": paragraph_number,
                            "sequence_number": sequence_number
                        })
                        continue
                    
                    print(f"✅ 发送视频生成开始状态")
                    await websocket.send_json({
                        "type": "status",
                        "message": "开始生成视频...",
                        "paragraph_number": paragraph_number,
                        "sequence_number": sequence_number
                    })
                    
                    async def generate_video_background():
                        """后台生成视频，不阻塞WebSocket"""
                        try:
                            # 使用LLM将文本转换为关键词作为视频生成提示词
                            llm_result = await qiniu_llm.simplify_text_to_keywords(text)
                            video_prompt = llm_result.get("keywords", text[:200])
                            
                            print(f"step1 image2video request - original text: {text}")
                            print(f"step1 image2video request - LLM generated prompt: {video_prompt}")
                            print(f"step1 image2video request - image base64 length: {len(image_base64)}")
                            
                            video_init_result = await qiniu_video.generate_video(video_prompt, image_base64)
                            video_id = video_init_result.get("id")
                            print("step2 image2video response taskid " + video_id)
                            
                            if video_id:
                                async def send_progress(attempt, max_attempts):
                                    """发送进度更新到前端"""
                                    if websocket.client_state.value == 1:  # CONNECTED
                                        progress_percent = int((attempt / max_attempts) * 100)
                                        await websocket.send_json({
                                            "type": "video_progress",
                                            "message": f"视频生成中... {progress_percent}%",
                                            "progress": progress_percent,
                                            "paragraph_number": paragraph_number,
                                            "sequence_number": sequence_number
                                        })
                                
                                video_final_result = await qiniu_video.poll_video_status(
                                    video_id,
                                    progress_callback=send_progress
                                )
                                print("step3 image2video response task status " + video_final_result.get("status") )
                                
                                if video_final_result.get("status") == "Completed":
                                    videos = video_final_result.get("data", {}).get("videos", [])
                                    if videos and len(videos) > 0:
                                        video_url = videos[0].get("url")
                                        # 只在WebSocket仍然连接时发送结果
                                        if websocket.client_state.value == 1:  # CONNECTED
                                            await websocket.send_json({
                                                "type": "video_result",
                                                "video_url": video_url,
                                                "paragraph_number": paragraph_number,
                                                "sequence_number": sequence_number
                                            })
                        except Exception as e:
                            print(f"视频生成错误: {str(e)}")
                            # 只在WebSocket仍然连接时发送错误消息
                            try:
                                if websocket.client_state.value == 1:  # CONNECTED
                                    await websocket.send_json({
                                        "type": "error",
                                        "message": f"视频生成失败: {str(e)}",
                                        "paragraph_number": paragraph_number,
                                        "sequence_number": sequence_number
                                    })
                            except:
                                pass
                    
                    asyncio.create_task(generate_video_background())
                
                # 发送完成消息
                await websocket.send_json({
                    "type": "complete",
                    "message": "处理完成"
                })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "无效的JSON格式"
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"处理错误: {str(e)}"
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket错误: {str(e)}")
        try:
            await websocket.close()
        except:
            pass
