"""
Russian-capable LLM Service on Modal Labs
Model: Qwen2.5-7B-Instruct
"""

import modal

# Define the Modal app
app = modal.App("russian-llm-qwen")

# Define the image with required dependencies
vllm_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "vllm==0.6.3",
        "huggingface_hub==0.25.2",
    )
)


@app.cls(
    gpu=modal.gpu.A10G(),  # A10G GPU is cost-effective for 7B models
    image=vllm_image,
    secrets=[modal.Secret.from_name("huggingface-secret")],  # Optional: for gated models
    container_idle_timeout=300,  # Keep container warm for 5 minutes
    allow_concurrent_inputs=10,
)
class QwenLLM:
    """
    Qwen2.5-7B-Instruct model for Russian language understanding
    """
    
    @modal.enter()
    def load_model(self):
        """Load the model when the container starts"""
        from vllm import LLM
        
        # Initialize vLLM with Qwen2.5-7B-Instruct
        self.llm = LLM(
            model="Qwen/Qwen2.5-7B-Instruct",
            trust_remote_code=True,
            max_model_len=4096,  # Context window
            gpu_memory_utilization=0.9,
        )
        print("Model loaded successfully!")
    
    @modal.method()
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> dict:
        """
        Generate a response to the given prompt
        
        Args:
            prompt: The input text/question (supports Russian)
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (higher = more creative)
            top_p: Nucleus sampling parameter
            
        Returns:
            dict with 'prompt' and 'response' keys
        """
        from vllm import SamplingParams
        
        # Create sampling parameters
        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        
        # Format the prompt for Qwen chat format
        formatted_prompt = f"<|im_start|>system\nYou are a helpful assistant that speaks Russian and English fluently.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        
        # Generate response
        outputs = self.llm.generate([formatted_prompt], sampling_params)
        response_text = outputs[0].outputs[0].text
        
        return {
            "prompt": prompt,
            "response": response_text,
            "model": "Qwen/Qwen2.5-7B-Instruct"
        }
    
    @modal.method()
    def batch_generate(
        self,
        prompts: list[str],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> list[dict]:
        """
        Generate responses for multiple prompts in batch
        
        Args:
            prompts: List of input texts/questions
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            
        Returns:
            List of dicts with 'prompt' and 'response' keys
        """
        from vllm import SamplingParams
        
        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        # Format all prompts
        formatted_prompts = [
            f"<|im_start|>system\nYou are a helpful assistant that speaks Russian and English fluently.<|im_end|>\n<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n"
            for p in prompts
        ]
        
        # Generate all responses
        outputs = self.llm.generate(formatted_prompts, sampling_params)
        
        results = []
        for i, output in enumerate(outputs):
            results.append({
                "prompt": prompts[i],
                "response": output.outputs[0].text,
                "model": "Qwen/Qwen2.5-7B-Instruct"
            })
        
        return results


@app.local_entrypoint()
def main():
    """
    Example usage from command line
    """
    # Test with Russian prompt
    russian_prompt = "Привет! Как дела? Расскажи мне интересный факт о космосе."
    english_prompt = "Hello! Tell me an interesting fact about space."
    
    model = QwenLLM()
    
    print("\n" + "="*60)
    print("Testing with Russian prompt:")
    print("="*60)
    result = model.generate.remote(russian_prompt)
    print(f"Prompt: {result['prompt']}")
    print(f"Response: {result['response']}")
    
    print("\n" + "="*60)
    print("Testing with English prompt:")
    print("="*60)
    result = model.generate.remote(english_prompt)
    print(f"Prompt: {result['prompt']}")
    print(f"Response: {result['response']}")
    
    print("\n" + "="*60)
    print("Testing batch generation:")
    print("="*60)
    batch_results = model.batch_generate.remote([
        "Что такое машинное обучение?",
        "What is artificial intelligence?"
    ])
    for r in batch_results:
        print(f"\nPrompt: {r['prompt']}")
        print(f"Response: {r['response']}")
