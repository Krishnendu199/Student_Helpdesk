from crewai import LLM

def get_ollama_model(model_name: str = "llama3"):
    """
    Initializes and returns a CrewAI-compatible Ollama LLM.

    Parameters:
        model_name (str): The name of the model to use (default: "llama3")

    Returns:
        LLM: A CrewAI-compatible LLM instance with Ollama provider
    """
    return LLM(
        model=f"ollama/{model_name}",  # e.g., "ollama/llama3"
        provider="ollama",             # Important: tells CrewAI to use Ollama provider
        base_url="http://localhost:11434",  # Default base URL for Ollama server
        temperature=0.7,
        max_tokens=512
    )

# Optional test
if __name__ == "__main__":
    model = get_ollama_model()
    result = model.call("List the required documents for student admission.")
    print("\n\nModel Response:\n", result)
