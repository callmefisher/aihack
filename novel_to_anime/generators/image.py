import os


class ImageGenerator:
    def __init__(self, api_key: str = None, provider: str = "stability"):
        self.api_key = api_key or os.getenv('IMAGE_API_KEY')
        self.provider = provider
    
    def generate_image(self, prompt: str, output_path: str) -> str:
        if not self.api_key:
            print(f"⚠️ 警告: 未配置API密钥，将生成占位符图片")
            return self._generate_placeholder(output_path, prompt)
        
        if self.provider == "stability":
            return self._generate_stability_ai(prompt, output_path)
        elif self.provider == "openai":
            return self._generate_openai_dalle(prompt, output_path)
        elif self.provider == "qiniu":
            return self._generate_qiniu_image(prompt, output_path)
        else:
            raise ValueError(f"不支持的图像生成器: {self.provider}")
    
    def _generate_placeholder(self, output_path: str, prompt: str) -> str:
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.new('RGB', (1024, 576), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        
        text = f"场景描述:\n{prompt[:100]}..."
        d.text((50, 250), text, fill=(255, 255, 255))
        
        img.save(output_path)
        return output_path
    
    def _generate_stability_ai(self, prompt: str, output_path: str) -> str:
        import requests
        
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "text_prompts": [
                {
                    "text": f"anime style, high quality, {prompt}",
                    "weight": 1
                }
            ],
            "cfg_scale": 7,
            "height": 576,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            import base64
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(data['artifacts'][0]['base64']))
            return output_path
        else:
            raise Exception(f"图像生成失败: {response.text}")
    
    def _generate_openai_dalle(self, prompt: str, output_path: str) -> str:
        import openai
        
        openai.api_key = self.api_key
        
        response = openai.Image.create(
            prompt=f"anime style, high quality illustration: {prompt}",
            n=1,
            size="1024x1024"
        )
        
        image_url = response['data'][0]['url']
        
        import requests
        img_data = requests.get(image_url).content
        with open(output_path, 'wb') as f:
            f.write(img_data)
        
        return output_path
    
    def _generate_qiniu_image(self, prompt: str, output_path: str) -> str:
        import requests
        import base64
        
        url = "https://openai.qiniu.com/v1/images/generations"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "model": "gemini-2.5-flash-image",
            "prompt": f"anime style, high quality, {prompt}",
            "n": 1,
            "size": "1024x1024"
        }
        
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code == 200:
            data = response.json()
            image_data = base64.b64decode(data['data'][0]['b64_json'])
            with open(output_path, 'wb') as f:
                f.write(image_data)
            return output_path
        else:
            raise Exception(f"七牛图像生成失败: {response.text}")
