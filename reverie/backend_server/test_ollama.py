"""
File: test_ollama.py
Description: Quick smoke-tests for the Ollama backend integration.
             Requires utils.py to have LLM_BACKEND = "ollama" configured.
             Run from reverie/backend_server/:  python test_ollama.py
"""
from persona.prompt_template.gpt_structure import (
  ChatGPT_request,
  GPT4_request,
  get_embedding,
  ChatGPT_safe_generate_response,
)


# ---------------------------------------------------------------------------
# Test 2: GPT4_request (routed to ollama_gpt4_model)
# ---------------------------------------------------------------------------
def test_gpt4_request():
  print("=" * 60)
  print("TEST 2: GPT4_request (routed to ollama_gpt4_model)")
  print("=" * 60)
  prompt = "Name three planets in the solar system."
  response = GPT4_request(prompt)
  print(f"Prompt : {prompt}")
  print(f"Response: {response}")
  assert response and response != "ChatGPT ERROR", "GPT4 request failed"
  print("PASSED\n")


# ---------------------------------------------------------------------------
# Test 3: embeddings via Ollama native /api/embed
# ---------------------------------------------------------------------------
def test_embedding():
  print("=" * 60)
  print("TEST 3: get_embedding (Ollama native /api/embed)")
  print("=" * 60)
  text = "Klaus Mueller is writing a research paper on gentrification."
  embedding = get_embedding(text)
  print(f"Text   : {text}")
  print(f"Embedding length: {len(embedding)}")
  print(f"First 5 values  : {embedding[:5]}")
  assert isinstance(embedding, list) and len(embedding) > 0, "Embedding failed"
  print("PASSED\n")


# ---------------------------------------------------------------------------
# Test 4: safe generate with validation (mirrors real agent usage)
# ---------------------------------------------------------------------------
def test_safe_generate():
  print("=" * 60)
  print("TEST 4: ChatGPT_safe_generate_response")
  print("=" * 60)

  prompt = (
    "Character 1: Maria Lopez is working on her physics degree and streaming "
    "games on Twitch to make extra money.\n"
    "Character 2: Klaus Mueller is writing a research paper on gentrification.\n\n"
    "Here is their conversation.\nMaria Lopez: \""
  )
  example_output = '[["Maria Lopez", "Hi Klaus!"], ["Klaus Mueller", "Hello Maria!"]]'
  special_instruction = (
    'The output should be a list of lists where each inner list is '
    '["<Name>", "<Utterance>"].'
  )

  def validate(response, prompt=None):
    try:
      parsed = eval(response)
      return isinstance(parsed, list) and len(parsed) > 0
    except Exception:
      return False

  def clean_up(response, prompt=None):
    return eval(response)

  result = ChatGPT_safe_generate_response(
    prompt,
    example_output,
    special_instruction,
    repeat=3,
    fail_safe_response=[],
    func_validate=validate,
    func_clean_up=clean_up,
    verbose=True,
  )
  print(f"Result: {result}")
  assert result, "Safe generate returned empty/falsy result"
  print("PASSED\n")


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------
if __name__ == "__main__":
  test_gpt4_request()
  test_embedding()
  test_safe_generate()
  print("All Ollama tests passed.")
