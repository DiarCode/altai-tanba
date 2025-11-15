"""
Client example for using the Modal LLM service
"""

import modal

def query_llm(prompt: str, max_tokens: int = 512, temperature: float = 0.7):
    """
    Send a query to the deployed LLM model
    
    Args:
        prompt: Your question or text (in Russian or English)
        max_tokens: Maximum length of response
        temperature: Creativity level (0.0-1.0)
    
    Returns:
        dict with response data
    """
    # Connect to the deployed Modal app
    app = modal.App.lookup("russian-llm-qwen", create_if_missing=False)
    
    # Get the model class
    QwenLLM = app.cls["QwenLLM"]
    model = QwenLLM()
    
    # Generate response
    result = model.generate.remote(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    return result


def batch_query_llm(prompts: list[str], max_tokens: int = 512):
    """
    Send multiple queries at once
    
    Args:
        prompts: List of questions/texts
        max_tokens: Maximum length per response
    
    Returns:
        list of dicts with response data
    """
    app = modal.App.lookup("russian-llm-qwen", create_if_missing=False)
    QwenLLM = app.cls["QwenLLM"]
    model = QwenLLM()
    
    results = model.batch_generate.remote(
        prompts=prompts,
        max_tokens=max_tokens
    )
    
    return results


if __name__ == "__main__":
    # Example usage
    print("Querying the LLM...")
    
    # Single query in Russian
    response = query_llm(
        prompt="Объясни простыми словами, что такое квантовые компьютеры?",
        max_tokens=300,
        temperature=0.7
    )
    
    print(f"\nPrompt: {response['prompt']}")
    print(f"Response: {response['response']}")
    print(f"Model: {response['model']}")
    
    # Batch query
    print("\n" + "="*60)
    print("Batch query example:")
    print("="*60)
    
    batch_responses = batch_query_llm([
        "Какая столица России?",
        "What is the capital of France?",
        "Сколько планет в солнечной системе?"
    ])
    
    for resp in batch_responses:
        print(f"\nQ: {resp['prompt']}")
        print(f"A: {resp['response']}")
